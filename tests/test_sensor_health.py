"""Sensor-health checks: a broken meter must be reported as a data problem, never as a leak."""

from __future__ import annotations

import pandas as pd
import pytest

from aquawatch import config
from aquawatch.data_loader import chronological_split, load_sensor_csv
from aquawatch.detectors import METHODS
from aquawatch.model import relative_deviation
from aquawatch.pipeline import score_all_methods
from aquawatch.sensor_health import flatline_mask
from aquawatch.settings import SettingsError, get_settings, load_settings


def test_relative_deviation_is_unknown_without_a_positive_baseline():
    observed = pd.Series([10.0, 0.0, 5.0])
    expected = pd.Series([8.0, 0.0, -1.0])
    out = relative_deviation(observed, expected)
    assert out.iloc[0] == pytest.approx(0.25)
    assert out.iloc[1:].isna().all()  # never inf or 0/0 that could look like a leak


def test_flatline_mask_flags_only_long_identical_runs():
    ts = pd.date_range("2026-01-01", periods=12, freq="h")
    flow = [5.0, 5.1, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 6.0, 6.0, 6.2, 6.3]
    frame = pd.DataFrame({"zone": "A", "timestamp": ts, "flow_index": flow})
    mask = flatline_mask(frame, flatline_hours=6)
    assert list(mask) == [False, False] + [True] * 6 + [False] * 4


def test_dead_meter_raises_no_leak_alarms_but_other_zones_still_do():
    df = load_sensor_csv(config.DEMO_CSV)
    df.loc[df["zone"] == "Zone 02", "flow_index"] = 0.0
    train, test = chronological_split(df, get_settings().dataset("demo").cutoff)
    scored = score_all_methods(train, test)
    dead = scored["zone"] == "Zone 02"
    assert scored.loc[dead, "sensor_suspect"].all()
    for column in METHODS.values():
        assert scored.loc[dead, column].sum() == 0, column
    assert scored.loc[~dead, list(METHODS.values())].to_numpy().sum() > 0


def test_flatline_hours_setting_is_validated():
    assert load_settings(environ={}).sensor_health.flatline_hours == 6
    with pytest.raises(SettingsError, match="flatline_hours"):
        load_settings(environ={"AQUAWATCH__SENSOR_HEALTH__FLATLINE_HOURS": "1"})


def test_nonzero_flatline_is_flagged_but_still_alarms():
    """A coarse or stuck meter at a non-zero value is suspect, but its alarms are not hidden:
    a real leak on a meter that reports rounded values must not disappear."""
    df = load_sensor_csv(config.SIM_CSV)
    zone = df["zone"] == "Zone 03"
    window = zone & df["timestamp"].between("2026-08-10 00:00", "2026-08-10 09:00")
    df.loc[window, "flow_index"] = 500.0  # stuck far above normal flow
    train, test = chronological_split(df, get_settings().dataset("simulated").cutoff)
    scored = score_all_methods(train, test)
    stuck = scored["zone"].eq("Zone 03") & scored["timestamp"].between("2026-08-10 00:00", "2026-08-10 09:00")
    assert scored.loc[stuck, "sensor_suspect"].all()
    assert not scored.loc[stuck, "sensor_dead"].any()
    assert scored.loc[stuck, "rule_pred"].sum() > 0


def test_flatline_spanning_the_cutoff_is_caught():
    from aquawatch.sensor_health import status_over_time

    ts = pd.date_range("2026-01-01", periods=48, freq="h")
    frame = pd.DataFrame({"zone": "A", "timestamp": ts, "flow_index": range(48)}).astype(
        {"flow_index": float}
    )
    frame.loc[20:26, "flow_index"] = 0.0  # 7 h at zero: hours 20-23 before the cutoff, 24-26 after
    frame["flow_rel_dev"] = 0.0
    frame["pressure_dev"] = 0.0
    history, current = frame.iloc[:24], frame.iloc[24:]
    hist_status, cur_status = status_over_time(history, current, flatline_hours=6)
    assert hist_status.loc[20:23, "sensor_dead"].all()
    assert cur_status.loc[24:26, "sensor_dead"].all()


def test_isolation_forest_scores_unknown_rows_as_missing_not_errors():
    from aquawatch.detectors import IsolationForestDetector
    from aquawatch.pipeline import build_features

    train, test = chronological_split(load_sensor_csv(config.DEMO_CSV), get_settings().dataset("demo").cutoff)
    train_f, test_f = build_features(train, test)
    test_f.loc[test_f.index[:5], "flow_rel_dev"] = float("nan")
    detector = IsolationForestDetector().fit(train_f)
    scores = detector.score(test_f)
    assert scores.iloc[:5].isna().all() and scores.iloc[5:].notna().all()
    assert detector.alarms(test_f).iloc[:5].sum() == 0


def test_saved_model_trains_on_the_same_healthy_rows_as_the_pipeline(monkeypatch):
    from aquawatch import model as model_module

    captured = {}
    real_train = model_module.train_isolation_forest

    def spy(features, **kwargs):
        captured["features"] = features
        return real_train(features, **kwargs)

    monkeypatch.setattr(model_module, "train_isolation_forest", spy)
    df = load_sensor_csv(config.DEMO_CSV)
    df.loc[df["zone"] == "Zone 02", "flow_index"] = 0.0
    train, _ = chronological_split(df, get_settings().dataset("demo").cutoff)
    model_module.fit_detector(train)
    assert "Zone 02" not in set(captured["features"]["zone"])  # dead meter rows excluded
    assert captured["features"][["flow_rel_dev", "pressure_dev"]].notna().all().all()

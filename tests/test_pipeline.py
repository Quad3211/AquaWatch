"""Smoke tests for the Phase 1 detection pipeline.

Owner: Nicholas Smalling
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.alerts import build_alert_table
from src.baseline import predict_rule
from src.data_loader import chronological_split, load_sensor_csv
from src.metrics import alarm_episodes, compare_methods, proportion_ci
from src.model import (
    add_deviations,
    fit_detector,
    load_model_artifacts,
    predict_isolation_forest,
    run_detection,
)

LABEL_COLS = ["simulated_leak_label", "simulated_event_id"]


@pytest.fixture(scope="module")
def split():
    return chronological_split(load_sensor_csv())


@pytest.fixture(scope="module")
def scored(split):
    train, test = split
    out, _ = run_detection(train, test)
    out["rule_pred"] = predict_rule(out)
    return out


def test_load_and_split(split):
    train, test = split
    assert len(train) == 1200
    assert len(test) == 480


def test_training_never_reads_labels(split):
    """A real utility has no leak labels, so training must work without them."""
    train, test = split
    with_labels, _ = run_detection(train, test)
    without_labels, _ = run_detection(train.drop(columns=LABEL_COLS), test)
    pd.testing.assert_series_equal(with_labels["ai_pred"], without_labels["ai_pred"])


def test_event_level_quality_gates(scored):
    """Regression gates: both detectors must catch most held-out leak events and
    produce far fewer false alarms than random alarms at the same rate."""
    table = compare_methods(scored).set_index("method")
    rule = table.loc["Simple flow rule"]
    ai = table.loc["Isolation Forest"]
    rand = table.loc["Random alarms (same rate as AI)"]

    assert rule["events_total"] == 3
    assert ai["events_detected"] >= 2
    assert rule["events_detected"] >= 2
    assert ai["episode_precision"] > rand["episode_precision"] + 0.2
    assert ai["false_alarms_per_zone_week"] < rand["false_alarms_per_zone_week"] / 2


def test_alarm_episodes_merge_consecutive_hours():
    ts = pd.to_datetime(["2026-11-12 00:00", "2026-11-12 01:00", "2026-11-12 05:00"])
    frame = pd.DataFrame({"zone": "Zone 01", "timestamp": ts, "pred": [1, 1, 1]})
    episodes = alarm_episodes(frame, "pred")
    assert list(episodes["hours"]) == [2, 1]


def test_proportion_ci_is_wide_for_small_samples():
    low, high = proportion_ci(3, 3)
    assert high == 1.0
    assert low < 0.35  # 3/3 is consistent with a true rate below 35%
    assert all(pd.isna(x) for x in proportion_ci(0, 0))


def test_saved_model_round_trip(split, tmp_path):
    """skops save/load gives identical predictions and refuses untrusted types."""
    from src.model import save_model_artifacts

    train, test = split
    model, profile = fit_detector(train)
    paths = dict(
        model_path=tmp_path / "m.skops",
        profile_path=tmp_path / "p.csv",
        metadata_path=tmp_path / "meta.json",
    )
    save_model_artifacts(model, profile, train=train, **paths)
    loaded, loaded_profile = load_model_artifacts(**paths)
    before = predict_isolation_forest(model, add_deviations(test, profile))
    after = predict_isolation_forest(loaded, add_deviations(test, loaded_profile))
    pd.testing.assert_series_equal(before, after)
    assert "sklearn_version" in paths["metadata_path"].read_text()


def test_alerts_not_empty_on_held_out(scored):
    alerts = build_alert_table(scored)
    assert not alerts.empty
    assert "reason" in alerts.columns
    assert "next_step" in alerts.columns


def _csv_bytes(df) -> BytesIO:
    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_load_from_uploaded_bytes():
    """Streamlit uploads arrive as bytes, not a file path."""
    raw = load_sensor_csv()
    df = load_sensor_csv(_csv_bytes(raw))
    assert len(df) == len(raw)
    assert str(df["timestamp"].dtype).startswith("datetime64")


def test_missing_column_is_rejected():
    raw = load_sensor_csv().drop(columns=["pressure_index"])
    with pytest.raises(ValueError, match="pressure_index"):
        load_sensor_csv(_csv_bytes(raw))


def test_bad_timestamp_is_rejected():
    raw = load_sensor_csv().astype({"timestamp": str})
    raw.loc[0, "timestamp"] = "not a date"
    with pytest.raises(ValueError, match="timestamp"):
        load_sensor_csv(_csv_bytes(raw))


def test_duplicate_and_negative_readings_are_rejected():
    raw = load_sensor_csv()
    bad = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    bad.loc[3, "flow_index"] = -1.0
    with pytest.raises(ValueError, match="failed validation") as excinfo:
        load_sensor_csv(_csv_bytes(bad))
    assert "flow_index" in str(excinfo.value)
    assert "uniqueness" in str(excinfo.value)


def test_app_runs_without_errors():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
    assert not at.exception
    assert not at.error


def test_split_explains_out_of_range_dates():
    df = load_sensor_csv()
    early = df[df["timestamp"] < "2026-11-05"]
    with pytest.raises(ValueError, match="cutoff"):
        chronological_split(early)


def test_event_alerts_one_row_per_episode(scored):
    from src.alerts import build_event_alerts
    from src.metrics import alarm_episodes

    events = build_event_alerts(scored, prediction_col="ai_pred", flow_unit="units/h")
    assert len(events) == len(alarm_episodes(scored, "ai_pred"))
    assert list(events["priority"]) == list(range(1, len(events) + 1))
    assert (events["est_volume_lost_units"] >= 0).all()
    assert events["est_volume_lost_units"].is_monotonic_decreasing
    assert set(events["matches_injected_leak"]) <= {"no (false alarm)"} | set(
        scored["simulated_event_id"]
    )


def test_merging_alarms_gives_fewer_incidents(scored):
    from src.alerts import build_event_alerts

    raw = build_event_alerts(scored, prediction_col="ai_pred", max_gap_hours=1)
    merged = build_event_alerts(scored, prediction_col="ai_pred", max_gap_hours=12)
    assert 0 < len(merged) <= len(raw)


def test_app_runs_for_every_dataset_and_detector():
    from streamlit.testing.v1 import AppTest

    from src.metrics import METHODS

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=300).run()
    for dataset in at.sidebar.radio[0].options[:2]:  # the two built-in datasets
        at.sidebar.radio[0].set_value(dataset).run()
        for detector in METHODS:
            at.sidebar.selectbox[0].set_value(detector).run()
            assert not at.exception, (dataset, detector)
            assert not at.error, (dataset, detector, [e.value for e in at.error])
            assert len(at.metric) == 4

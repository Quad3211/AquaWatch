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

"""Tests for the baseline detectors in src/baseline.py.

Owner: Nicholas Smalling
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aquawatch import config
from aquawatch.baseline import predict_cusum, predict_flow_pressure_rule, predict_night_flow
from aquawatch.data_loader import chronological_split, load_sensor_csv
from aquawatch.metrics import RANDOM_NAME, compare_methods
from aquawatch.pipeline import score_all_methods
from aquawatch.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]


def _hourly(days: int, start: str = "2026-01-05", zone: str = "Zone 01") -> pd.DataFrame:
    """Steady, slightly noisy synthetic zone: flow 50, pressure 60."""
    rng = np.random.default_rng(0)
    ts = pd.date_range(start, periods=days * 24, freq="h")
    return pd.DataFrame(
        {
            "zone": zone,
            "timestamp": ts,
            "flow_index": 50 + rng.normal(0, 1, len(ts)),
            "pressure_index": 60 + rng.normal(0, 0.2, len(ts)),
            "flow_rel_dev": rng.normal(0, 0.02, len(ts)),
            "pressure_dev": rng.normal(0, 0.2, len(ts)),
        }
    )


def test_cusum_flags_a_small_lasting_rise_but_not_noise():
    train, test = _hourly(14), _hourly(7, start="2026-01-19")
    assert predict_cusum(train, test).sum() == 0  # pure noise: no alarms

    # A 4% rise (2 SDs per hour) lasting a day: too small for a one-hour rule,
    # but CUSUM builds up evidence and alarms within the day.
    leak = test.copy()
    window = leak["timestamp"].between("2026-01-21 00:00", "2026-01-21 23:00")
    leak.loc[window, "flow_rel_dev"] += 0.04
    alarms = predict_cusum(train, leak)
    assert alarms[window].sum() > 0
    assert alarms[~window & (leak["timestamp"] < "2026-01-21")].sum() == 0


def test_flow_pressure_rule_needs_both_signals():
    train, test = _hourly(14), _hourly(2, start="2026-01-19")
    flow_only = test.assign(flow_rel_dev=0.2, pressure_dev=0.0)  # pressure exactly normal
    both = flow_only.assign(pressure_dev=-2.0)
    assert predict_flow_pressure_rule(train, flow_only).sum() == 0
    assert predict_flow_pressure_rule(train, both).sum() == len(test)


def test_night_flow_flags_raised_nights_only():
    history, test = _hourly(21), _hourly(7, start="2026-01-26")
    leak = test.copy()
    night = leak["timestamp"].dt.normalize() == pd.Timestamp("2026-01-28")
    leak.loc[night, "flow_index"] += 10  # +20% for the whole day
    alarms = predict_night_flow(history, leak)
    flagged_hours = set(leak.loc[alarms == 1, "timestamp"].dt.hour)
    assert flagged_hours == set(get_settings().night_flow.hours)
    assert (leak.loc[alarms == 1, "timestamp"].dt.normalize() == pd.Timestamp("2026-01-28")).all()
    assert predict_night_flow(history, test).sum() == 0


@pytest.fixture(scope="module")
def simulated_ladder():
    df = load_sensor_csv(config.SIM_CSV)
    train, test = chronological_split(df, get_settings().dataset("simulated").cutoff)
    return compare_methods(score_all_methods(train, test)).set_index("method")


def test_every_detector_beats_random_on_simulated_data(simulated_ladder):
    rand = simulated_ladder.loc[RANDOM_NAME]
    for method in ["Flow + pressure rule", "Night flow (MNF)", "CUSUM on flow", "Isolation Forest"]:
        row = simulated_ladder.loc[method]
        assert row["events_detected"] >= 15, method
        assert row["false_alarms_per_zone_week"] < 1.0, method
        assert row["episode_precision"] > rand["episode_precision"] + 0.3, method

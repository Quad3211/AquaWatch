"""Tests for the WNTR simulator and the committed simulated dataset.

Owner: Nickel Small

The dataset tests need only pandas. The simulator tests need WNTR, which has no
Python 3.14 build yet, so they are skipped where WNTR is missing (CI runs them
on Python 3.11 and 3.13).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from src.data_loader import chronological_split, load_sensor_csv


@pytest.fixture(scope="module")
def sim_readings():
    return load_sensor_csv(config.SIM_CSV)


@pytest.fixture(scope="module")
def sim_events():
    return pd.read_csv(config.SIM_EVENTS_CSV, parse_dates=["start", "end"])


def test_simulated_dataset_passes_schema(sim_readings):
    assert len(sim_readings) == 120 * 24 * 5
    assert sim_readings["zone"].nunique() == 5


def test_events_table_matches_labels(sim_readings, sim_events):
    labelled = set(sim_readings.loc[sim_readings["simulated_leak_label"] == 1, "simulated_event_id"])
    assert labelled == set(sim_events["event_id"])
    assert sim_events["target_fraction_of_inflow"].between(0.03, 0.40).all()
    assert set(sim_events["kind"]) == {"abrupt", "incipient"}


def test_leaks_do_not_overlap_within_a_zone(sim_events):
    for _, zone_events in sim_events.sort_values("start").groupby("zone"):
        assert (zone_events["start"].iloc[1:].to_numpy() > zone_events["end"].iloc[:-1].to_numpy()).all()


def test_both_windows_contain_many_events(sim_readings):
    train, test = chronological_split(sim_readings, config.SIM_TRAIN_CUTOFF)
    for window in (train, test):
        events = window.loc[window["simulated_leak_label"] == 1, "simulated_event_id"].nunique()
        assert events >= 15


def test_simulator_is_deterministic_and_grows_incipient_leaks():
    pytest.importorskip("wntr")
    from src.simulate import SimConfig, run

    cfg = SimConfig(days=12, leaks_per_zone=2, seed=5)
    readings_a, events_a = run(cfg)
    readings_b, _ = run(cfg)
    pd.testing.assert_frame_equal(readings_a, readings_b)

    # Incipient leaks start at a quarter of full size; they must grow to near full
    # size (peak within 50% of the target set at 50 m pressure), proving the
    # leak-area control actually takes effect.
    incipient = events_a[events_a["kind"] == "incipient"]
    assert not incipient.empty
    ratio = incipient["peak_leak_m3h"] / incipient["target_leak_m3h"]
    assert (ratio > 0.6).all()


def test_day_type_profile_removes_weekend_false_alarms(sim_readings):
    """Regression gate for the weekend fix: with a weekday/weekend profile,
    Isolation Forest must keep false alarms low and most alarms real."""
    from src.baseline import predict_rule
    from src.metrics import compare_methods
    from src.model import run_detection

    train, test = chronological_split(sim_readings, config.SIM_TRAIN_CUTOFF)
    results = {}
    for profile in ("hour", "day_type"):
        scored, _ = run_detection(train, test, profile_by=profile)
        scored["rule_pred"] = predict_rule(scored)
        results[profile] = compare_methods(scored).set_index("method").loc["Isolation Forest"]

    old, new = results["hour"], results["day_type"]
    assert new["false_alarms_per_zone_week"] < old["false_alarms_per_zone_week"] / 3
    assert new["episode_precision"] > 0.6
    assert new["events_detected"] >= 15


def test_sizing_options_make_big_zones_smoother_and_fix_leak_sizes():
    """Sizing-study options: customer-based noise shrinks with zone size, and
    leaks use the absolute sizes given (as a share of each zone's inflow)."""
    pytest.importorskip("wntr")
    import numpy as np

    from src.simulate import SimConfig, demand_multipliers, run

    cfg = SimConfig(days=14, liters_per_customer_day=600.0)
    rng = np.random.default_rng(0)
    shared = {"zone_day": np.ones(cfg.hours), "zone_hour": np.ones(cfg.hours)}
    small = demand_multipliers(cfg, rng, customers=10, **shared)
    big = demand_multipliers(cfg, rng, customers=10_000, **shared)
    base = demand_multipliers(cfg, rng, customers=1e12, **shared)
    assert np.std(small / base) > 5 * np.std(big / base)

    sizing = SimConfig(
        days=12, leaks_per_zone=2, zones=2, zone_mean_inflow_m3h=(10.0, 100.0),
        zone_elevations_m=(20.0, 20.0), leak_sizes_m3h=(5.0,), liters_per_customer_day=600.0,
        scale_pipes=True,
    )
    _, events = run(sizing)
    assert (events["target_leak_m3h"] == 5.0).all()
    shares = events.groupby("zone")["target_fraction_of_inflow"].first().sort_values()
    assert list(shares.round(2)) == [0.05, 0.5]


def test_committed_sizing_results_show_size_effect():
    """The committed DMA sizing results: 10 m3/h leaks are caught far more often in
    small zones than big ones, for every detector."""
    results = pd.read_csv(ROOT / "data" / "simulated" / "sizing" / "dma_sizing_results.csv")
    ten = results[results["leak_m3h"] == 10.0].assign(rate=lambda d: d["caught_24h"] / d["leaks"])
    for _method, part in ten.groupby("method"):
        rates = part.set_index("zone_m3h")["rate"]
        assert rates[10.0] == 1.0
        assert rates[200.0] <= 0.5

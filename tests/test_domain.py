"""Tests for the shared domain types (src/aquawatch/domain.py)."""

from __future__ import annotations

import pandas as pd
import pytest

from aquawatch import config
from aquawatch.alerts import build_incidents, incidents_to_frame
from aquawatch.data_loader import chronological_split, load_sensor_csv
from aquawatch.domain import Incident, IncidentStatus, LeakEvent, RunInfo
from aquawatch.metrics import compare_methods
from aquawatch.pipeline import score_all_methods
from aquawatch.settings import get_settings


@pytest.fixture(scope="module")
def simulated_scored():
    train, test = chronological_split(
        load_sensor_csv(config.SIM_CSV), get_settings().dataset("simulated").cutoff
    )
    return score_all_methods(train, test)


def test_leak_events_round_trip_and_validate():
    frame = pd.read_csv(config.SIM_EVENTS_CSV, parse_dates=["start", "end"])
    events = LeakEvent.from_frame(frame)
    assert len(events) == len(frame)
    assert events[0].size_m3h is not None and events[0].kind in {"abrupt", "incipient"}
    back = LeakEvent.to_frame(events)
    assert list(back["event_id"]) == list(frame["event_id"])
    with pytest.raises(ValueError, match="end is before start"):
        LeakEvent("x", "Zone 01", pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-01"))


def test_metrics_accept_leak_event_objects(simulated_scored):
    frame = pd.read_csv(config.SIM_EVENTS_CSV, parse_dates=["start", "end"])
    as_table = compare_methods(simulated_scored, events=frame, detect_within_hours=24)
    as_objects = compare_methods(simulated_scored, events=LeakEvent.from_frame(frame), detect_within_hours=24)
    pd.testing.assert_frame_equal(as_table, as_objects)


def test_incidents_are_typed_ranked_and_stable(simulated_scored):
    incidents = build_incidents(
        simulated_scored, prediction_col="fp_rule_pred", detector="Flow + pressure rule"
    )
    assert incidents and all(isinstance(i, Incident) for i in incidents)
    assert all(i.status is IncidentStatus.NEW and i.outcome is None for i in incidents)
    volumes = [i.est_volume for i in incidents]
    assert volumes == sorted(volumes, reverse=True)
    ids = [i.incident_id for i in incidents]
    assert len(set(ids)) == len(ids)  # unique
    again = build_incidents(simulated_scored, prediction_col="fp_rule_pred", detector="Flow + pressure rule")
    assert [i.incident_id for i in again] == ids  # stable across runs
    table = incidents_to_frame(incidents)
    assert list(table["priority"]) == list(range(1, len(incidents) + 1))
    assert set(table["matches_injected_leak"]) - {"no (false alarm)"} <= set(
        simulated_scored["simulated_event_id"]
    )


def test_run_info_records_what_produced_results():
    run = RunInfo.create("simulated", "2026-07-31", "2026-09-28", get_settings().fingerprint())
    assert run.settings_fingerprint == get_settings().fingerprint()
    assert run.run_id.split("-")[1] == run.settings_fingerprint[:6]
    assert run.code_version  # a git SHA here; "unknown" outside a git checkout

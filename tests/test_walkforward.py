"""Walk-forward evaluation (src/aquawatch/walkforward.py)."""

from __future__ import annotations

import pandas as pd
import pytest

from aquawatch import config
from aquawatch.cli import main
from aquawatch.data_loader import load_sensor_csv
from aquawatch.errors import DataError
from aquawatch.walkforward import make_folds, run_walk_forward, tune_threshold, zone_weeks


@pytest.fixture(scope="module")
def simulated():
    return load_sensor_csv(config.SIM_CSV)


def test_folds_move_forward_without_overlap_or_leakage(simulated):
    folds = make_folds(simulated, train_days=42, val_days=14, test_days=14, step_days=14)
    assert len(folds) == 4
    for fold in folds:
        assert fold.train_start < fold.val_start < fold.test_start < fold.test_end
        assert fold.test_end <= simulated["timestamp"].max() + pd.Timedelta(hours=1)
    # test windows follow each other without overlapping
    for earlier, later in zip(folds, folds[1:], strict=False):
        assert later.test_start >= earlier.test_end


def test_too_little_data_is_a_clear_data_error():
    demo = load_sensor_csv(config.DEMO_CSV)
    with pytest.raises(DataError, match="needs at least 70"):
        make_folds(demo, train_days=42, val_days=14, test_days=14, step_days=14)


def test_threshold_tuning_respects_the_budget_and_never_reads_labels(simulated):
    frame = simulated[simulated["timestamp"] < "2026-06-15"].copy()
    scores = frame["flow_index"] / frame.groupby("zone")["flow_index"].transform("median")
    budget = 1.0
    threshold = tune_threshold(scores, frame, budget)
    flagged = frame.assign(a=(scores > threshold).astype(int))
    from aquawatch.metrics import alarm_episodes

    assert len(alarm_episodes(flagged, "a")) <= budget * zone_weeks(frame)
    # Same threshold with the label columns removed: tuning is label-free.
    stripped = frame.drop(columns=["simulated_leak_label", "simulated_event_id"])
    assert tune_threshold(scores, stripped, budget) == threshold
    # A looser budget never gives a stricter threshold.
    assert tune_threshold(scores, frame, 5.0) <= threshold


def test_walk_forward_end_to_end(simulated):
    per_fold, pooled, folds = run_walk_forward(simulated)
    assert set(per_fold["fold"]) == {f.number for f in folds}
    assert set(pooled["variant"]) == {"tuned", "default"}
    cusum = pooled[(pooled["method"] == "CUSUM on flow") & (pooled["variant"] == "tuned")].iloc[0]
    random = pooled[pooled["method"].str.startswith("Random")].iloc[0]
    assert cusum["events_total"] == random["events_total"] > 0
    assert cusum["events_detected"] > random["events_detected"]
    assert cusum["false_alarms_per_zone_week"] < random["false_alarms_per_zone_week"]


def test_cli_walk_forward(capsys):
    assert main(["evaluate", "--dataset", "simulated", "--protocol", "walk-forward", "--budget", "2"]) == 0
    out = capsys.readouterr().out
    assert "walk-forward" in out and "at most 2 alarm(s) per zone-week" in out
    assert "per-fold recall range" in out

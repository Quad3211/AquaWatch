"""Evaluation report: compare every detector on one dataset (`aquawatch evaluate`).

Owner: Nicholas Smalling

The data is simulated. Training never reads the labels; they are used only to
score the held-out window. Results are reported per leak event, with exact 95%
confidence intervals and a same-budget random baseline.
"""
from __future__ import annotations

import sys

import pandas as pd

from aquawatch import config
from aquawatch.data_loader import chronological_split, load_sensor_csv
from aquawatch.domain import RunInfo
from aquawatch.metrics import (
    METHODS,
    compare_methods,
    detection_by_leak_size,
    format_comparison,
    true_events,
)
from aquawatch.pipeline import score_all_methods
from aquawatch.settings import get_settings

# name -> (readings CSV, events CSV, events are the ground truth?). Cutoffs and the
# detection window come from the settings ([datasets.<name>]).
DATASETS = {
    "demo": (config.DEMO_CSV, None, False),
    "simulated": (config.SIM_CSV, config.SIM_EVENTS_CSV, False),
    "battledim": (config.BATTLEDIM_CSV, config.BATTLEDIM_EVENTS_CSV, True),
}


def evaluate(
    dataset: str = "demo",
    cutoff: str | None = None,
    profile: str | None = None,
    detect_within: float | None = None,
) -> None:
    """Score every detector on one dataset and print the event-level comparison."""
    profile = profile or get_settings().profile.by
    override_window = detect_within

    settings = get_settings()
    path, events_path, events_are_truth = DATASETS[dataset]
    default_cutoff = settings.dataset(dataset).cutoff
    # Detection window: the --detect-within value if given, else the dataset's
    # setting (only BattLeDIM sets one by default; None = no limit).
    dataset_window = settings.dataset(dataset).detect_within_hours
    detect_within = override_window if override_window is not None else dataset_window
    cutoff = cutoff or default_cutoff
    if not path.exists():
        sys.exit(
            f"{path} not found. For BattLeDIM run `aquawatch battledim fetch`, then "
            "`aquawatch battledim prepare`."
        )
    events = pd.read_csv(events_path, parse_dates=["start", "end"]) if events_path else None
    df = load_sensor_csv(path)
    train, test = chronological_split(df, cutoff)
    scored = score_all_methods(train, test, profile_by=profile)
    truth = events if events_are_truth else None
    table = format_comparison(compare_methods(scored, events=truth, detect_within_hours=detect_within))

    run = RunInfo.create(dataset, test["timestamp"].min(), test["timestamp"].max(), settings.fingerprint())
    print(f"Run {run.run_id} | dataset: {dataset} ({path.name}) | expected-flow profile: {profile}")
    print(f"Settings fingerprint: {run.settings_fingerprint} | code version: {run.code_version}")
    print(f"Rows: {len(df):,} | training window: {len(train):,} rows | held out from {cutoff}: {len(test):,}")
    if events_are_truth and events is not None:
        new = events[(events["start"] >= scored["timestamp"].min())]
        print(f"Leaks starting in the test window: {len(new)} (an alarm must come within "
              f"{detect_within} h of a leak's start to count; later alarms on it are repeats)")
    else:
        print(f"Held-out injected leak events: {len(true_events(scored))}")
        if detect_within is not None:
            print(f"A leak counts as caught only if an alarm comes within {detect_within:g} h of its start.")
    suspect, dead = int(scored["sensor_suspect"].sum()), int(scored["sensor_dead"].sum())
    if suspect:
        print(f"Sensor health: {suspect:,} readings look like a sensor fault (flat-lined, zero or no "
              f"baseline); no leak alarms were raised on the {dead:,} dead ones.")
    print(f"Held-out injected anomaly readings: {int(test['simulated_leak_label'].sum())}")
    print()
    print(table.to_string(index=False))

    if events is not None:
        sizes = detection_by_leak_size(
            scored,
            METHODS,
            events,
            use_events_as_truth=events_are_truth,
            detect_within_hours=detect_within,
        )
        print("\nLeak events caught, by leak size:")
        print(sizes.to_string(index=False))

    print(
        "\nInterpretation: results on deliberately simulated scenarios, not real utility data."
        "\nWhere events are few, the confidence intervals are wide; do not read small differences"
        " as real."
    )


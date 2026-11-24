"""Compare every detector (four baselines, Isolation Forest) and a random baseline.

Run from the project root:
    pip install -r requirements.txt
    python scripts/AquaWatch_Evaluate.py                       # original 14-day demo CSV
    python scripts/AquaWatch_Evaluate.py --dataset simulated   # 120-day WNTR simulation

The data is simulated. Training never reads the labels; they are used only to
score the held-out window. Results are reported per leak event, with exact 95%
confidence intervals. For the WNTR dataset, a second table shows how detection
depends on leak size.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.data_loader import chronological_split, load_sensor_csv  # noqa: E402
from src.metrics import (  # noqa: E402
    METHODS,
    compare_methods,
    detection_by_leak_size,
    format_comparison,
    true_events,
)
from src.model import PROFILE_KEYS  # noqa: E402
from src.pipeline import score_all_methods  # noqa: E402

DATASETS = {
    "demo": (config.DEMO_CSV, config.TRAIN_CUTOFF, None),
    "simulated": (config.SIM_CSV, config.SIM_TRAIN_CUTOFF, config.SIM_EVENTS_CSV),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AquaWatch detectors.")
    parser.add_argument("--dataset", choices=sorted(DATASETS), default="demo")
    parser.add_argument("--cutoff", help="Override the train/test cutoff date (YYYY-MM-DD).")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_KEYS),
        default=config.PROFILE_BY,
        help="How expected flow is looked up (default from config.PROFILE_BY).",
    )
    args = parser.parse_args()

    path, cutoff, events_path = DATASETS[args.dataset]
    cutoff = args.cutoff or cutoff
    df = load_sensor_csv(path)
    train, test = chronological_split(df, cutoff)
    scored = score_all_methods(train, test, profile_by=args.profile)
    table = format_comparison(compare_methods(scored))

    print(f"Dataset: {args.dataset} ({path.name}) | expected-flow profile: {args.profile}")
    print(f"Rows: {len(df):,} | training window: {len(train):,} rows | held out from {cutoff}: {len(test):,}")
    print(f"Held-out injected leak events: {len(true_events(scored))}")
    print(f"Held-out injected anomaly readings: {int(test['simulated_leak_label'].sum())}")
    print()
    print(table.to_string(index=False))

    if events_path is not None and events_path.exists():
        events = pd.read_csv(events_path)
        sizes = detection_by_leak_size(scored, METHODS, events)
        print("\nLeak events caught, by leak size:")
        print(sizes.to_string(index=False))

    print(
        "\nInterpretation: results on deliberately simulated scenarios, not real utility data."
        "\nWhere events are few, the confidence intervals are wide; do not read small differences"
        " as real."
    )


if __name__ == "__main__":
    main()

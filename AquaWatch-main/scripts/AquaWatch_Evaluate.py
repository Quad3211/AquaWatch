"""Reproduce the simple-rule vs Isolation Forest test used in the AquaWatch pitch.

Run from the project root:
    pip install -r requirements.txt
    python scripts/AquaWatch_Evaluate.py

The data is simulated. The label is not a model feature; here it selects normal
training rows and scores the held-out test.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.baseline import predict_rule
from src.data_loader import chronological_split, load_sensor_csv
from src.metrics import compare_rule_and_ai
from src.model import run_detection


def main() -> None:
    df = load_sensor_csv()
    train, test = chronological_split(df)
    scored, _model = run_detection(train, test)
    scored = scored.copy()
    scored["rule_pred"] = predict_rule(scored)
    table = compare_rule_and_ai(scored)

    print(f"Dataset rows: {len(df):,}")
    print(f"Training-window rows: {len(train):,}")
    print(f"Held-out rows: {len(test):,}")
    print(f"Held-out injected anomaly readings: {int(test['simulated_leak_label'].sum())}")
    print("\nMethod              Precision   Recall   TP   FP   FN   TN")
    for _, row in table.iterrows():
        print(
            f"{row['method']:<19} {row['precision']:>8.1%} {row['recall']:>8.1%} "
            f"{row['tp']:>4} {row['fp']:>4} {row['fn']:>4} {row['tn']:>4}"
        )
    print("\nInterpretation: these are results on deliberately simulated scenarios, not real utility data.")


if __name__ == "__main__":
    main()

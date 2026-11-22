"""Compare the simple flow rule, Isolation Forest and a random baseline.

Run from the project root:
    pip install -r requirements.txt
    python scripts/AquaWatch_Evaluate.py

The data is simulated. Training never reads the labels; they are used only to
score the held-out window. Results are reported per leak event, with exact 95%
confidence intervals, because there are only a few events to score.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.baseline import predict_rule  # noqa: E402
from src.data_loader import chronological_split, load_sensor_csv  # noqa: E402
from src.metrics import compare_methods, format_comparison, true_events  # noqa: E402
from src.model import run_detection  # noqa: E402


def main() -> None:
    df = load_sensor_csv()
    train, test = chronological_split(df)
    scored, _model = run_detection(train, test)
    scored["rule_pred"] = predict_rule(scored)
    table = format_comparison(compare_methods(scored))

    print(f"Dataset rows: {len(df):,}")
    print(f"Training-window rows: {len(train):,}")
    print(f"Held-out rows: {len(test):,}")
    print(f"Held-out injected leak events: {len(true_events(scored))}")
    print(f"Held-out injected anomaly readings: {int(test['simulated_leak_label'].sum())}")
    print()
    print(table.to_string(index=False))
    print(
        "\nInterpretation: results on deliberately simulated scenarios, not real utility data."
        "\nWith so few events, the confidence intervals are wide; do not read small differences"
        " as real."
    )


if __name__ == "__main__":
    main()

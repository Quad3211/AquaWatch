"""Evaluation helpers for rule vs AI comparison.

Owner: Nicholas Smalling
"""
from __future__ import annotations

import pandas as pd
from sklearn.metrics import confusion_matrix, precision_score, recall_score


def score_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float | int]:
    """Precision/recall plus confusion counts for a binary alert column."""
    tn, fp, fn, tp = confusion_matrix(y_true.astype(int), y_pred.astype(int), labels=[0, 1]).ravel()
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }


def compare_rule_and_ai(scored_test: pd.DataFrame) -> pd.DataFrame:
    """Build the pitch-style comparison table."""
    required = {"simulated_leak_label", "rule_pred", "ai_pred"}
    missing = required.difference(scored_test.columns)
    if missing:
        raise ValueError(f"scored_test is missing: {sorted(missing)}")

    y_true = scored_test["simulated_leak_label"]
    rows = []
    for name, col in [("Simple flow rule", "rule_pred"), ("Isolation Forest", "ai_pred")]:
        stats = score_predictions(y_true, scored_test[col])
        rows.append(
            {
                "method": name,
                "precision": stats["precision"],
                "recall": stats["recall"],
                "tp": stats["tp"],
                "fp": stats["fp"],
                "fn": stats["fn"],
                "tn": stats["tn"],
            }
        )
    return pd.DataFrame(rows)

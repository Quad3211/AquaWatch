"""Turn model/rule predictions into explainable investigation alerts.

Owner: Nickel Small (logic) / Jason Williams (UI consumption)
"""
from __future__ import annotations

import pandas as pd


def _reason(row: pd.Series) -> str:
    flow_bit = (
        "Flow above its usual zone/hour pattern"
        if row.get("flow_rel_dev", 0) > 0.10
        else "Flow pattern looks unusual versus its zone/hour baseline"
    )
    press_bit = (
        "pressure index drops at the same time"
        if row.get("pressure_dev", 0) < -2
        else "pressure also differs from its usual zone/hour level"
    )
    return f"{flow_bit}; {press_bit}."


def build_alert_table(
    scored: pd.DataFrame,
    *,
    prediction_col: str = "ai_pred",
    min_score_rows: bool = True,
) -> pd.DataFrame:
    """Return ranked alerts for investigation (not confirmed leaks)."""
    if prediction_col not in scored.columns:
        raise KeyError(f"Missing prediction column: {prediction_col}")

    alerts = scored[scored[prediction_col] == 1].copy()
    if alerts.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "zone",
                "flow_index",
                "pressure_index",
                "flow_rel_dev",
                "pressure_dev",
                "reason",
                "next_step",
                "source",
            ]
        )

    alerts["reason"] = alerts.apply(_reason, axis=1)
    alerts["next_step"] = "Check logger quality; request field verification."
    alerts["source"] = "Isolation Forest" if prediction_col == "ai_pred" else "Simple flow rule"

    # Stronger combined deviation sorts higher (more urgent review).
    alerts["rank_score"] = alerts["flow_rel_dev"].clip(lower=0) + (-alerts["pressure_dev"]).clip(lower=0) / 20.0
    alerts = alerts.sort_values(["rank_score", "timestamp"], ascending=[False, True])

    cols = [
        "timestamp",
        "zone",
        "flow_index",
        "pressure_index",
        "flow_rel_dev",
        "pressure_dev",
        "reason",
        "next_step",
        "source",
        "rank_score",
    ]
    if min_score_rows:
        return alerts[cols].reset_index(drop=True)
    return alerts.reset_index(drop=True)

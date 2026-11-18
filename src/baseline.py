"""Simple flow-threshold baseline.

Owner: Nicholas Smalling

Alert when flow is more than 25% above the expected value for that zone/hour.
"""
from __future__ import annotations

import pandas as pd

FLOW_THRESHOLD = 0.25


def predict_rule(frame: pd.DataFrame, flow_rel_col: str = "flow_rel_dev") -> pd.Series:
    """Return 1/0 predictions for the simple flow rule."""
    if flow_rel_col not in frame.columns:
        raise KeyError(f"Missing column required by baseline: {flow_rel_col}")
    return (frame[flow_rel_col] > FLOW_THRESHOLD).astype(int)

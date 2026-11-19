"""Simple flow-threshold baseline.

Owner: Nicholas Smalling

Alert when flow is more than FLOW_RULE_THRESHOLD above the expected value for that zone/hour.
"""
from __future__ import annotations

import pandas as pd

import config

FLOW_THRESHOLD = config.FLOW_RULE_THRESHOLD


def predict_rule(frame: pd.DataFrame, flow_rel_col: str = "flow_rel_dev") -> pd.Series:
    """Return 1/0 predictions for the simple flow rule."""
    if flow_rel_col not in frame.columns:
        raise KeyError(f"Missing column required by baseline: {flow_rel_col}")
    return (frame[flow_rel_col] > FLOW_THRESHOLD).astype(int)

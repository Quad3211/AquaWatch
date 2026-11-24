"""One scoring path for every detector, so all are compared on equal terms.

Owner: Nickel Small / Nicholas Smalling
"""
from __future__ import annotations

import pandas as pd

from src.baseline import (
    predict_cusum,
    predict_flow_pressure_rule,
    predict_night_flow,
    predict_rule,
)
from src.metrics import METHODS  # noqa: F401  (re-exported for callers)
from src.model import add_deviations, fit_detector, predict_isolation_forest


def score_all_methods(
    train: pd.DataFrame, test: pd.DataFrame, profile_by: str | None = None
) -> pd.DataFrame:
    """Fit on the training window (no labels) and add every method's alarms to the test rows."""
    model, profile = fit_detector(train, profile_by=profile_by)
    train_features = add_deviations(train, profile)
    scored = add_deviations(test, profile)
    scored["rule_pred"] = predict_rule(scored)
    scored["fp_rule_pred"] = predict_flow_pressure_rule(train_features, scored)
    scored["mnf_pred"] = predict_night_flow(train, scored)
    scored["cusum_pred"] = predict_cusum(train_features, scored)
    scored["ai_pred"] = predict_isolation_forest(model, scored)
    return scored

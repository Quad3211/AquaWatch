"""Zone/hour profiling and Isolation Forest detection.

Owner: Nickel Small
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURE_COLS = ["flow_rel_dev", "pressure_dev"]


def build_zone_hour_profile(normal_train: pd.DataFrame) -> pd.DataFrame:
    """Average flow/pressure by zone and hour from known-normal training rows."""
    if normal_train.empty:
        raise ValueError("No normal training rows are available.")
    return (
        normal_train.groupby(["zone", "hour"])
        .agg(
            expected_flow=("flow_index", "mean"),
            expected_pressure=("pressure_index", "mean"),
        )
        .reset_index()
    )


def add_deviations(frame: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    """Attach expected values and deviation features used by rule + AI."""
    out = frame.merge(profile, on=["zone", "hour"], how="left")
    if out[["expected_flow", "expected_pressure"]].isna().any().any():
        raise ValueError("Some zone/hour combinations have no training reference profile.")
    out = out.copy()
    out["flow_rel_dev"] = (out["flow_index"] - out["expected_flow"]) / out["expected_flow"]
    out["pressure_dev"] = out["pressure_index"] - out["expected_pressure"]
    return out


def train_isolation_forest(
    train_features: pd.DataFrame,
    *,
    n_estimators: int = 300,
    contamination: float = 0.01,
    random_state: int = 17,
) -> IsolationForest:
    """Fit Isolation Forest on normal deviation features only (no labels)."""
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )
    model.fit(train_features[FEATURE_COLS])
    return model


def predict_isolation_forest(model: IsolationForest, frame: pd.DataFrame) -> pd.Series:
    """Return 1 for anomaly (-1 from sklearn), else 0."""
    preds = model.predict(frame[FEATURE_COLS])
    return pd.Series((preds == -1).astype(int), index=frame.index, name="ai_pred")


def run_detection(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, IsolationForest]:
    """Full Phase 1 detection path on a chronological split.

    Labels are used only to keep known-normal rows in the training reference set.
    They are never passed as model features.
    """
    normal_train = train[train["simulated_leak_label"] == 0].copy()
    profile = build_zone_hour_profile(normal_train)
    train_features = add_deviations(normal_train, profile)
    test_features = add_deviations(test, profile)
    model = train_isolation_forest(train_features)
    test_features = test_features.copy()
    test_features["ai_pred"] = predict_isolation_forest(model, test_features)
    return test_features, model

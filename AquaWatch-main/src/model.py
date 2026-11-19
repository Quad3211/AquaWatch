"""Zone/hour profiling and Isolation Forest detection.

Owner: Nickel Small
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

import config

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
    n_estimators: int | None = None,
    contamination: float | None = None,
    random_state: int | None = None,
) -> IsolationForest:
    """Fit Isolation Forest on normal deviation features only (no labels)."""
    model = IsolationForest(
        n_estimators=n_estimators if n_estimators is not None else config.IFOREST_N_ESTIMATORS,
        contamination=contamination if contamination is not None else config.IFOREST_CONTAMINATION,
        random_state=random_state if random_state is not None else config.IFOREST_RANDOM_STATE,
    )
    model.fit(train_features[FEATURE_COLS])
    return model


def predict_isolation_forest(model: IsolationForest, frame: pd.DataFrame) -> pd.Series:
    """Return 1 for anomaly (-1 from sklearn), else 0."""
    preds = model.predict(frame[FEATURE_COLS])
    return pd.Series((preds == -1).astype(int), index=frame.index, name="ai_pred")


def save_model_artifacts(
    model: IsolationForest,
    profile: pd.DataFrame,
    *,
    model_path: Path | None = None,
    profile_path: Path | None = None,
) -> tuple[Path, Path]:
    """Persist model + zone/hour profile for offline demos (guide §14.3)."""
    model_path = model_path or config.MODEL_PATH
    profile_path = profile_path or config.PROFILE_PATH
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    profile.to_csv(profile_path, index=False)
    return model_path, profile_path


def load_model_artifacts(
    *,
    model_path: Path | None = None,
    profile_path: Path | None = None,
) -> tuple[IsolationForest, pd.DataFrame]:
    """Load previously saved model + profile."""
    model_path = model_path or config.MODEL_PATH
    profile_path = profile_path or config.PROFILE_PATH
    if not model_path.exists() or not profile_path.exists():
        raise FileNotFoundError(
            f"Saved artifacts not found. Run: python scripts/train_and_save_model.py "
            f"(looked for {model_path} and {profile_path})"
        )
    model = joblib.load(model_path)
    profile = pd.read_csv(profile_path)
    return model, profile


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

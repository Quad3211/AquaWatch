"""Zone/hour profiling and Isolation Forest detection.

Owner: Nickel Small
"""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import sklearn
import skops
import skops.io as sio
from sklearn.ensemble import IsolationForest

import config

FEATURE_COLS = ["flow_rel_dev", "pressure_dev"]


def build_zone_hour_profile(train: pd.DataFrame) -> pd.DataFrame:
    """Typical flow/pressure for each zone and hour of day.

    Uses the median of *all* training rows, so no labels are needed. The median
    is robust: a few leak hours in the training window barely move it, unlike
    the mean.
    """
    if train.empty:
        raise ValueError("No training rows are available.")
    return (
        train.groupby(["zone", "hour"])
        .agg(
            expected_flow=("flow_index", "median"),
            expected_pressure=("pressure_index", "median"),
        )
        .reset_index()
    )


def select_typical_rows(features: pd.DataFrame, z_cutoff: float | None = None) -> pd.DataFrame:
    """Drop training rows that already look abnormal, without using labels.

    For each zone, a robust z-score (median/MAD) is computed for both deviation
    features. Rows beyond ``z_cutoff`` on either feature are left out of the
    Isolation Forest's training set, so past leaks in the history do not teach
    the model that leaks are normal.
    """
    cutoff = config.ROBUST_Z_CUTOFF if z_cutoff is None else z_cutoff
    keep = pd.Series(True, index=features.index)
    for col in FEATURE_COLS:
        grouped = features.groupby("zone")[col]
        median = grouped.transform("median")
        mad = grouped.transform(lambda x: (x - x.median()).abs().median())
        # 0.6745 scales MAD to match a standard deviation for normal data.
        robust_z = 0.6745 * (features[col] - median) / mad.replace(0, float("nan"))
        keep &= robust_z.abs().fillna(0) <= cutoff
    typical = features[keep]
    if typical.empty:
        raise ValueError("Robust filter removed every training row; check the data.")
    return typical


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


# The only non-default type an Isolation Forest needs when loading with skops.
# Listing it explicitly means a tampered file containing anything else is refused.
TRUSTED_SKOPS_TYPES = ["sklearn.tree._tree.Tree"]


def data_fingerprint(frame: pd.DataFrame) -> str:
    """Short SHA-256 of the training data, so a saved model can be traced to it."""
    digest = hashlib.sha256(pd.util.hash_pandas_object(frame, index=False).values.tobytes())
    return digest.hexdigest()[:16]


def save_model_artifacts(
    model: IsolationForest,
    profile: pd.DataFrame,
    *,
    train: pd.DataFrame | None = None,
    model_path: Path | None = None,
    profile_path: Path | None = None,
    metadata_path: Path | None = None,
) -> tuple[Path, Path, Path]:
    """Save model (skops, not pickle), profile and a metadata JSON.

    Pickle/joblib files can run arbitrary code when loaded and break across
    library versions, so the model is stored with skops and never committed.
    """
    model_path = model_path or config.MODEL_PATH
    profile_path = profile_path or config.PROFILE_PATH
    metadata_path = metadata_path or config.MODEL_METADATA_PATH
    model_path.parent.mkdir(parents=True, exist_ok=True)
    sio.dump(model, model_path)
    profile.to_csv(profile_path, index=False)
    metadata = {
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_file": model_path.name,
        "profile_file": profile_path.name,
        "features": FEATURE_COLS,
        "params": model.get_params(),
        "robust_z_cutoff": config.ROBUST_Z_CUTOFF,
        "train_cutoff": config.TRAIN_CUTOFF,
        "train_rows": None if train is None else len(train),
        "train_data_sha256_16": None if train is None else data_fingerprint(train),
        "sklearn_version": sklearn.__version__,
        "skops_version": skops.__version__,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str))
    return model_path, profile_path, metadata_path


def load_model_artifacts(
    *,
    model_path: Path | None = None,
    profile_path: Path | None = None,
    metadata_path: Path | None = None,
) -> tuple[IsolationForest, pd.DataFrame]:
    """Load a saved model + profile, warning if scikit-learn has changed since saving."""
    model_path = model_path or config.MODEL_PATH
    profile_path = profile_path or config.PROFILE_PATH
    metadata_path = metadata_path or config.MODEL_METADATA_PATH
    if not model_path.exists() or not profile_path.exists():
        raise FileNotFoundError(
            f"Saved artifacts not found. Run: python scripts/train_and_save_model.py "
            f"(looked for {model_path} and {profile_path})"
        )
    if metadata_path.exists():
        saved_with = json.loads(metadata_path.read_text()).get("sklearn_version")
        if saved_with and saved_with != sklearn.__version__:
            warnings.warn(
                f"Model was saved with scikit-learn {saved_with} but {sklearn.__version__} "
                "is installed; retrain with scripts/train_and_save_model.py.",
                stacklevel=2,
            )
    model = sio.load(model_path, trusted=TRUSTED_SKOPS_TYPES)
    profile = pd.read_csv(profile_path)
    return model, profile


def fit_detector(train: pd.DataFrame) -> tuple[IsolationForest, pd.DataFrame]:
    """Build the zone/hour profile and fit Isolation Forest on the training window.

    Never reads ``simulated_leak_label`` or ``simulated_event_id``: a real utility
    has no such labels, so training must work without them.
    """
    profile = build_zone_hour_profile(train)
    train_features = select_typical_rows(add_deviations(train, profile))
    model = train_isolation_forest(train_features)
    return model, profile


def run_detection(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, IsolationForest]:
    """Full Phase 1 detection path on a chronological split (label-free training)."""
    model, profile = fit_detector(train)
    test_features = add_deviations(test, profile)
    test_features["ai_pred"] = predict_isolation_forest(model, test_features)
    return test_features, model

"""Load and validate AquaWatch sensor CSV files.

Owner: Nicholas Smalling
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config

REQUIRED_COLUMNS = {
    "timestamp",
    "zone",
    "flow_index",
    "pressure_index",
    "hour",
    "simulated_leak_label",
}

DEFAULT_DATA = config.DEMO_CSV
TRAIN_CUTOFF = config.TRAIN_CUTOFF


def load_sensor_csv(path: str | Path | None = None) -> pd.DataFrame:
    """Load the synthetic (or compatible) sensor CSV and return a clean frame."""
    csv_path = Path(path) if path is not None else DEFAULT_DATA
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")

    df = df.sort_values(["zone", "timestamp"]).reset_index(drop=True)
    df["hour"] = df["timestamp"].dt.hour.astype(int)
    df["simulated_leak_label"] = df["simulated_leak_label"].astype(int)
    if "simulated_event_id" in df.columns:
        df["simulated_event_id"] = df["simulated_event_id"].fillna("").astype(str).replace("nan", "")
    else:
        df["simulated_event_id"] = ""

    return df


def chronological_split(df: pd.DataFrame, cutoff: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into train (< cutoff) and held-out test (>= cutoff)."""
    cut = cutoff or TRAIN_CUTOFF
    train = df[df["timestamp"] < cut].copy()
    test = df[df["timestamp"] >= cut].copy()
    if train.empty or test.empty:
        raise ValueError("Expected rows in both the training window and the held-out test window.")
    return train, test

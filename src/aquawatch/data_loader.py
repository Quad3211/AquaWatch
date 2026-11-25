"""Load and validate AquaWatch sensor CSV files.

Owner: Nicholas Smalling
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import IO

import pandas as pd

from aquawatch import config
from aquawatch.errors import DataError
from aquawatch.schema import validate_sensor_frame
from aquawatch.settings import get_settings

REQUIRED_COLUMNS = {
    "timestamp",
    "zone",
    "flow_index",
    "pressure_index",
    "hour",
    "simulated_leak_label",
}

DEFAULT_DATA = config.DEMO_CSV


def load_sensor_csv(source: str | Path | IO | None = None) -> pd.DataFrame:
    """Load the synthetic (or compatible) sensor CSV and return a clean frame.

    ``source`` may be a file path or an open file-like object (for example a
    ``BytesIO`` holding a Streamlit upload). ``None`` loads the project CSV.
    """
    if source is None or isinstance(source, (str, Path)):
        csv_path = Path(source) if source is not None else DEFAULT_DATA
        if not csv_path.exists():
            raise FileNotFoundError(f"Dataset not found: {csv_path}")
        source = csv_path

    df = pd.read_csv(source)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise DataError(f"Dataset is missing required columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise DataError("Some rows have a missing or unreadable timestamp.")

    df["hour"] = df["timestamp"].dt.hour.astype(int)
    df = validate_sensor_frame(df)
    df = df.sort_values(["zone", "timestamp"]).reset_index(drop=True)
    if "simulated_event_id" in df.columns:
        df["simulated_event_id"] = df["simulated_event_id"].fillna("").astype(str).replace("nan", "")
    else:
        df["simulated_event_id"] = ""

    return df


def chronological_split(df: pd.DataFrame, cutoff: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into train (< cutoff) and held-out test (>= cutoff)."""
    cut = cutoff or get_settings().dataset("demo").cutoff
    train = df[df["timestamp"] < cut].copy()
    test = df[df["timestamp"] >= cut].copy()
    if train.empty or test.empty:
        raise DataError(
            f"Expected rows both before and on/after the training cutoff ({cut}). "
            f"This dataset covers {df['timestamp'].min()} to {df['timestamp'].max()}."
        )
    return train, test


def load_uploaded_csv(data: bytes) -> pd.DataFrame:
    """Load a CSV uploaded in the app (raw bytes) with the same checks as a file."""
    return load_sensor_csv(BytesIO(data))


def midpoint_cutoff(df: pd.DataFrame) -> str:
    """A default train/test cutoff for unfamiliar data: the date halfway through it."""
    start, end = df["timestamp"].min(), df["timestamp"].max()
    if start == end:
        raise DataError("The data covers a single moment; it needs a time range to train and test on.")
    return str((start + (end - start) / 2).normalize().date())

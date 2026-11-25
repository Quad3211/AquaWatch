"""Data contract for sensor CSVs, checked every time data is loaded.

Owner: Nicholas Smalling

A bad file should fail loudly at load time with a clear message, not produce
quietly wrong alerts later. ``flow_index`` and ``pressure_index`` stay unitless
on purpose: the synthetic data is not calibrated to litres/second or metres,
and renaming the columns to units would imply a calibration we do not have.
"""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

from aquawatch.errors import DataError

SENSOR_SCHEMA = pa.DataFrameSchema(
    {
        "timestamp": pa.Column("datetime64[ns]", nullable=False, coerce=True),
        "zone": pa.Column(str, nullable=False),
        "flow_index": pa.Column(float, pa.Check.ge(0), nullable=False, coerce=True),
        "pressure_index": pa.Column(float, pa.Check.ge(0), nullable=False, coerce=True),
        "hour": pa.Column(int, pa.Check.in_range(0, 23), nullable=False, coerce=True),
        "simulated_leak_label": pa.Column(int, pa.Check.isin([0, 1]), nullable=False, coerce=True),
    },
    unique=["zone", "timestamp"],
    strict=False,  # extra columns (e.g. simulated_event_id) are allowed
    report_duplicates="all",
)


def validate_sensor_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return the validated frame, or raise ValueError listing every problem."""
    try:
        return SENSOR_SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        cases = exc.failure_cases
        summary = (
            cases.groupby(["column", "check"], dropna=False)
            .size()
            .reset_index(name="rows")
            .to_string(index=False)
        )
        raise DataError(f"Sensor data failed validation:\n{summary}") from exc


def find_gaps(df: pd.DataFrame, freq: str = "h") -> pd.DataFrame:
    """Count missing hourly readings per zone (gaps are reported, not fatal)."""
    rows = []
    for zone, group in df.groupby("zone"):
        expected = pd.date_range(group["timestamp"].min(), group["timestamp"].max(), freq=freq)
        missing = len(expected.difference(pd.DatetimeIndex(group["timestamp"])))
        if missing:
            rows.append({"zone": zone, "missing_readings": missing})
    return pd.DataFrame(rows, columns=["zone", "missing_readings"])

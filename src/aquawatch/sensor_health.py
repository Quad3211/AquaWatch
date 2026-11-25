"""Sensor-health checks: tell a broken meter apart from a leak.

Owner: Nicholas Smalling

A meter that is stuck (the same value hour after hour) or reads zero against a
zone that normally uses water is a *data problem*, not a leak. Before this
check, a dead meter produced undefined deviations and Isolation Forest raised
leak alarms on it. Now such readings are flagged ``sensor_suspect``: detectors
do not train on them and never raise a leak alarm on them, and the app and
report say how many there were, so the data issue gets fixed instead of a crew
being sent out.

A reading is suspect when:

- **flatline:** its zone's flow has not changed at all for at least
  ``[sensor_health] flatline_hours`` consecutive hours (real demand always
  moves a little), or
- **no baseline:** there is no usable expected flow for it (missing, or zero,
  so a relative deviation cannot be computed).
"""
from __future__ import annotations

import pandas as pd

from aquawatch.settings import get_settings


def flatline_mask(frame: pd.DataFrame, flatline_hours: int | None = None) -> pd.Series:
    """True for readings inside a run of identical flow values lasting ``flatline_hours`` or more."""
    hours = flatline_hours or get_settings().sensor_health.flatline_hours
    ordered = frame.sort_values(["zone", "timestamp"])
    changed = ordered.groupby("zone")["flow_index"].diff().ne(0)  # first row of each zone is True (NaN != 0)
    run_id = changed.cumsum()
    run_length = run_id.map(run_id.value_counts())
    return (run_length >= hours).reindex(frame.index)


def suspect_readings(features: pd.DataFrame, flatline_hours: int | None = None) -> pd.Series:
    """True where a reading looks like a sensor fault rather than real flow (see module docstring)."""
    no_baseline = features["flow_rel_dev"].isna() | features["pressure_dev"].isna()
    return (flatline_mask(features, flatline_hours) | no_baseline).astype(bool)

"""Sensor-health checks: tell a broken meter apart from a leak.

Owner: Nicholas Smalling

A meter that is stuck (the same value hour after hour) or reads zero against a
zone that normally uses water is a *data problem*, not a leak. Two levels:

- **suspect** (``sensor_suspect``): the reading may be a sensor fault. These
  rows are left out of detector training and counted in the app and report, so
  the meter gets checked. Suspect means *any* of:

  - **flatline:** the zone's flow has not changed at all for at least
    ``[sensor_health] flatline_hours`` consecutive hours;
  - **dead:** see below.

- **dead** (``sensor_dead``): the meter reads zero for at least
  ``flatline_hours``, or there is no usable expected flow (missing or zero), so
  a relative deviation cannot be computed. No leak alarm is raised on dead
  readings: they would only produce nonsense deviations.

Non-zero flat-lines are *not* silenced. Meters that report rounded or pulse
values can repeat the same number for hours while a small leak runs, and
hiding a real leak is worse than an alarm someone can check. Those alarms are
still raised, and the reading is shown as suspect.

Runs are measured on training and test data together (``flatline_mask`` on the
concatenated frame), so a meter that sticks just before the cutoff is caught.
"""

from __future__ import annotations

import pandas as pd

from aquawatch.settings import get_settings


def _runs(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """(run length, run value) for every reading: consecutive identical flows per zone."""
    ordered = frame.sort_values(["zone", "timestamp"])
    changed = ordered.groupby("zone")["flow_index"].diff().ne(0)  # first row of each zone is True (NaN != 0)
    run_id = changed.cumsum()
    run_length = run_id.map(run_id.value_counts())
    return run_length.reindex(frame.index), ordered["flow_index"].reindex(frame.index)


def flatline_mask(frame: pd.DataFrame, flatline_hours: int | None = None) -> pd.Series:
    """True for readings inside a run of identical flow values lasting ``flatline_hours`` or more."""
    hours = flatline_hours or get_settings().sensor_health.flatline_hours
    run_length, _ = _runs(frame)
    return run_length >= hours


def sensor_status(features: pd.DataFrame, flatline_hours: int | None = None) -> pd.DataFrame:
    """Columns ``sensor_suspect`` and ``sensor_dead`` for each row of a deviation-feature frame."""
    hours = flatline_hours or get_settings().sensor_health.flatline_hours
    run_length, value = _runs(features)
    flat = run_length >= hours
    no_baseline = features["flow_rel_dev"].isna() | features["pressure_dev"].isna()
    dead = (flat & (value <= 0)) | no_baseline
    return pd.DataFrame({"sensor_suspect": (flat | dead).astype(bool), "sensor_dead": dead.astype(bool)})


def suspect_readings(features: pd.DataFrame, flatline_hours: int | None = None) -> pd.Series:
    """True where a reading may be a sensor fault (flat-lined, zero or without a baseline)."""
    return sensor_status(features, flatline_hours)["sensor_suspect"]


def status_over_time(
    history: pd.DataFrame, frame: pd.DataFrame, flatline_hours: int | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sensor status for ``history`` and ``frame``, with runs measured across both.

    A meter stuck from shortly before the train/test cutoff to shortly after it
    forms one run, not two shorter ones that each miss the limit.
    """
    both = pd.concat([history, frame], ignore_index=True)
    status = sensor_status(both, flatline_hours)
    split = len(history)
    hist_status = status.iloc[:split].set_axis(history.index)
    frame_status = status.iloc[split:].set_axis(frame.index)
    return hist_status, frame_status

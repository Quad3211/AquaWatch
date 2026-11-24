"""Baseline detectors that any "AI" detector has to beat.

Owner: Nicholas Smalling

All of them work on the deviation features from ``src.model.add_deviations``
(flow relative to expected, pressure minus expected) and never read labels.
Their thresholds are fixed in ``config.py`` in advance and are not tuned on
the test window.

1. ``predict_rule``: flow more than 25% above expected (the original rule).
2. ``predict_flow_pressure_rule``: flow clearly up **and** pressure down at the
   same time, in robust z-score units. This is the fair comparison for
   Isolation Forest, which also sees both signals.
3. ``predict_night_flow``: minimum night flow (MNF), the standard utility check.
   Each night's 02:00-04:00 mean inflow is compared with the median of the
   previous nights.
4. ``predict_cusum``: a one-sided CUSUM on the flow deviation, which builds up
   evidence over hours, so it suits leaks (lasting level shifts) better than
   rules that judge each hour on its own.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from aquawatch.settings import get_settings

MAD_TO_SD = 1.4826  # scales a median absolute deviation to a standard deviation


def predict_rule(frame: pd.DataFrame, flow_rel_col: str = "flow_rel_dev") -> pd.Series:
    """Return 1/0 predictions for the simple flow rule."""
    if flow_rel_col not in frame.columns:
        raise KeyError(f"Missing column required by baseline: {flow_rel_col}")
    return (frame[flow_rel_col] > get_settings().rules.flow_threshold).astype(int)


def robust_scales(train_features: pd.DataFrame) -> pd.DataFrame:
    """Per-zone median and robust SD of each deviation feature (training window)."""
    rows = []
    for zone, group in train_features.groupby("zone"):
        row = {"zone": zone}
        for col in ("flow_rel_dev", "pressure_dev"):
            median = group[col].median()
            sd = MAD_TO_SD * (group[col] - median).abs().median()
            row[f"{col}_median"] = median
            row[f"{col}_sd"] = sd if sd > 0 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _robust_z(frame: pd.DataFrame, scales: pd.DataFrame, col: str) -> pd.Series:
    merged = frame[["zone"]].merge(scales, on="zone", how="left")
    z = (frame[col].to_numpy() - merged[f"{col}_median"].to_numpy()) / merged[f"{col}_sd"].to_numpy()
    return pd.Series(np.nan_to_num(z), index=frame.index)


def predict_flow_pressure_rule(
    train_features: pd.DataFrame,
    frame: pd.DataFrame,
    flow_z: float | None = None,
    pressure_z: float | None = None,
) -> pd.Series:
    """Flag hours where flow is high *and* pressure is low versus the zone's usual spread."""
    flow_z = get_settings().rules.fp_flow_z if flow_z is None else flow_z
    pressure_z = get_settings().rules.fp_pressure_z if pressure_z is None else pressure_z
    scales = robust_scales(train_features)
    zf = _robust_z(frame, scales, "flow_rel_dev")
    zp = _robust_z(frame, scales, "pressure_dev")
    return ((zf >= flow_z) & (zp <= -pressure_z)).astype(int)


def predict_night_flow(
    history: pd.DataFrame,
    frame: pd.DataFrame,
    *,
    night_hours: tuple[int, ...] | None = None,
    lookback_nights: int | None = None,
    k_mad: float | None = None,
    min_rise: float | None = None,
) -> pd.Series:
    """Minimum night flow check.

    For each zone and night, the mean inflow over ``night_hours`` is compared
    with the median of the previous ``lookback_nights`` nights (only the past is
    used). A night is flagged if it is above that median by more than both
    ``k_mad`` robust SDs and ``min_rise`` (a fraction). The night-hour readings
    of a flagged night become alarms. ``history`` is earlier data (the training
    window) so the first test nights have a baseline.
    """
    night_hours = night_hours or get_settings().night_flow.hours
    lookback = lookback_nights or get_settings().night_flow.lookback_nights
    k_mad = get_settings().night_flow.k_mad if k_mad is None else k_mad
    min_rise = get_settings().night_flow.min_rise if min_rise is None else min_rise

    both = pd.concat([history, frame], ignore_index=True).drop_duplicates(["zone", "timestamp"])
    night = both[both["timestamp"].dt.hour.isin(night_hours)].copy()
    night["night"] = night["timestamp"].dt.normalize()
    nightly = night.groupby(["zone", "night"])["flow_index"].mean().rename("mnf").reset_index()

    flagged_nights = []
    for _zone, group in nightly.groupby("zone"):
        past = group["mnf"].shift(1).rolling(lookback, min_periods=max(3, lookback // 2))
        median = past.median()
        mad = past.apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
        threshold = median + np.maximum(k_mad * MAD_TO_SD * mad, min_rise * median)
        flagged_nights.append(group.loc[group["mnf"] > threshold, ["zone", "night"]])
    flagged = pd.concat(flagged_nights) if flagged_nights else pd.DataFrame(columns=["zone", "night"])

    key = frame["zone"].astype(str) + "|" + frame["timestamp"].dt.normalize().astype(str)
    flagged_keys = set(flagged["zone"].astype(str) + "|" + flagged["night"].astype(str))
    is_night = frame["timestamp"].dt.hour.isin(night_hours)
    return (key.isin(flagged_keys) & is_night).astype(int)


def predict_cusum(
    train_features: pd.DataFrame,
    frame: pd.DataFrame,
    *,
    k: float | None = None,
    h: float | None = None,
) -> pd.Series:
    """One-sided (upward) CUSUM on the flow deviation, per zone.

    The flow deviation is turned into robust z-scores using the training window.
    ``S = max(0, S + z - k)`` builds up while flow stays above normal; an alarm
    is raised while ``S > h``. ``S`` is capped at ``2h`` so it recovers quickly
    after a repair. The sum runs over training and test hours in time order, so
    it is warmed up when the test window starts, and only the past is used.
    """
    k = get_settings().cusum.k if k is None else k
    h = get_settings().cusum.h if h is None else h
    scales = robust_scales(train_features)
    both = pd.concat(
        [train_features.assign(_test=False), frame.assign(_test=True)], ignore_index=False
    )
    both = both.reset_index(names="_orig_index").sort_values(["zone", "timestamp"])
    both["_z"] = _robust_z(both, scales, "flow_rel_dev").to_numpy()

    alarms = np.zeros(len(both), dtype=int)
    positions = {idx: pos for pos, idx in enumerate(both.index)}
    for _zone, group in both.groupby("zone", sort=False):
        s = 0.0
        for idx, z in zip(group.index, group["_z"].to_numpy(), strict=True):
            s = min(max(0.0, s + z - k), 2 * h)
            alarms[positions[idx]] = int(s > h)
    both["_alarm"] = alarms
    test_part = both[both["_test"]].set_index("_orig_index")
    return test_part["_alarm"].reindex(frame.index).fillna(0).astype(int)

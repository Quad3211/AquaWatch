"""One scoring path for every detector, so all are compared on equal terms.

Owner: Nickel Small / Nicholas Smalling

Builds the deviation features once (static or rolling expected-flow profile),
then fits and runs every detector in ``aquawatch.detectors.REGISTRY``.
"""
from __future__ import annotations

import pandas as pd

from aquawatch.detectors import METHODS, build_detectors  # noqa: F401  (METHODS re-exported)
from aquawatch.model import add_deviations, add_rolling_deviations, build_zone_hour_profile
from aquawatch.sensor_health import suspect_readings
from aquawatch.settings import PROFILE_CHOICES, get_settings  # noqa: F401  (re-exported)


def build_features(
    train: pd.DataFrame, test: pd.DataFrame, profile_by: str | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deviation features (expected flow/pressure and deviations) for train and test rows."""
    profile_by = profile_by or get_settings().profile.by
    if profile_by == "rolling":
        # Baseline = median of the previous weeks, updated as time moves on.
        return add_rolling_deviations(train, test)
    profile = build_zone_hour_profile(train, by=profile_by)
    return add_deviations(train, profile), add_deviations(test, profile)


def score_all_methods(
    train: pd.DataFrame, test: pd.DataFrame, profile_by: str | None = None
) -> pd.DataFrame:
    """Fit every registered detector on the training window (no labels) and add its
    alarms (``<column>``) and scores (``<column>_score``) to the test rows.

    Readings flagged by the sensor-health check (``sensor_suspect``: flat-lined
    or no usable baseline) are left out of training and never raise a leak
    alarm; they are a data problem to fix, not a leak.
    """
    train_features, scored = build_features(train, test, profile_by)
    healthy_train = train_features[~suspect_readings(train_features)]
    scored["sensor_suspect"] = suspect_readings(scored)
    for detector in build_detectors():
        detector.fit(healthy_train)
        scored[f"{detector.column}_score"] = detector.score(scored)
        scored[detector.column] = detector.alarms(scored).where(~scored["sensor_suspect"], 0).astype(int)
    return scored

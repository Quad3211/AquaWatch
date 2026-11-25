"""One scoring path for every detector, so all are compared on equal terms.

Owner: Nickel Small / Nicholas Smalling

Builds the deviation features once (static or rolling expected-flow profile),
then fits and runs every detector in ``aquawatch.detectors.REGISTRY``.
"""

from __future__ import annotations

import pandas as pd

from aquawatch.detectors import METHODS, build_detectors  # noqa: F401  (METHODS re-exported)
from aquawatch.model import add_deviations, add_rolling_deviations, build_zone_hour_profile
from aquawatch.sensor_health import status_over_time
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


def score_all_methods(train: pd.DataFrame, test: pd.DataFrame, profile_by: str | None = None) -> pd.DataFrame:
    """Fit every registered detector on the training window (no labels) and add its
    alarms (``<column>``) and scores (``<column>_score``) to the test rows.

    Sensor health (see ``aquawatch.sensor_health``): suspect readings
    (flat-lined, zero or without a baseline) are left out of training, and dead
    readings (zero flow or no baseline) never raise a leak alarm. Non-zero
    flat-lines still alarm, so a real leak on a coarse meter is not hidden.
    """
    train_features, scored = build_features(train, test, profile_by)
    train_status, test_status = status_over_time(train_features, scored)
    healthy_train = train_features[~train_status["sensor_suspect"]]
    scored["sensor_suspect"] = test_status["sensor_suspect"]
    scored["sensor_dead"] = test_status["sensor_dead"]
    for detector in build_detectors():
        detector.fit(healthy_train)
        scored[f"{detector.column}_score"] = detector.score(scored)
        scored[detector.column] = detector.alarms(scored).where(~scored["sensor_dead"], 0).astype(int)
    return scored

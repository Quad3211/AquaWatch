"""Contract tests run against every registered detector (src/aquawatch/detectors.py).

A new detector added to REGISTRY is tested automatically.
"""

from __future__ import annotations

import pandas as pd
import pytest

from aquawatch import config
from aquawatch.data_loader import chronological_split, load_sensor_csv
from aquawatch.detectors import LABEL_COLUMNS, METHODS, REGISTRY, Detector, build_detectors
from aquawatch.pipeline import build_features
from aquawatch.settings import get_settings


@pytest.fixture(scope="module")
def features():
    cutoff = get_settings().dataset("simulated").cutoff
    train, test = chronological_split(load_sensor_csv(config.SIM_CSV), cutoff)
    return build_features(train, test)


def test_registry_names_and_columns_are_unique():
    assert len({cls.name for cls in REGISTRY}) == len(REGISTRY)
    assert len({cls.column for cls in REGISTRY}) == len(REGISTRY)
    assert list(METHODS.values()) == [cls.column for cls in REGISTRY]
    assert all(isinstance(d, Detector) for d in build_detectors())


@pytest.mark.parametrize("cls", REGISTRY, ids=lambda c: c.name)
def test_detector_never_reads_labels(cls, features):
    """Same alarms and scores with the label columns present or deleted."""
    train_f, test_f = features
    with_labels = cls().fit(train_f)
    without = cls().fit(train_f.drop(columns=list(LABEL_COLUMNS)))
    stripped_test = test_f.drop(columns=list(LABEL_COLUMNS))
    pd.testing.assert_series_equal(
        with_labels.alarms(test_f), without.alarms(stripped_test), check_names=False
    )
    pd.testing.assert_series_equal(with_labels.score(test_f), without.score(stripped_test), check_names=False)


@pytest.mark.parametrize("cls", REGISTRY, ids=lambda c: c.name)
def test_alarms_follow_score_and_threshold(cls, features):
    train_f, test_f = features
    detector = cls().fit(train_f)
    alarms, score = detector.alarms(test_f), detector.score(test_f)
    assert alarms.index.equals(test_f.index)
    assert set(alarms.unique()) <= {0, 1}
    # Alarm exactly when the score passes the threshold (>= allowed at the boundary).
    above = score > detector.threshold
    at_or_above = score >= detector.threshold - 1e-12
    assert (alarms[above] == 1).all()
    assert (at_or_above[alarms == 1]).all()


@pytest.mark.parametrize("cls", REGISTRY, ids=lambda c: c.name)
def test_unfitted_detector_fails_clearly_or_needs_no_fit(cls, features):
    _, test_f = features
    detector = cls()
    try:
        detector.alarms(test_f)
    except RuntimeError as exc:
        assert "fit()" in str(exc)

"""One interface for every detector, plus the registry the rest of AquaWatch reads.

Owner: Nickel Small / Nicholas Smalling

Every detector:

- ``fit(history)``: learns from the training window's deviation features
  (flow, pressure, expected values, deviations, time, zone). It must never read
  ``simulated_leak_label`` or ``simulated_event_id``; tests check this for every
  registered detector.
- ``score(frame)``: a continuous "how unusual" value per row, higher = more
  unusual. Kept separate from the threshold so thresholds can be tuned on a
  validation window (build guide step B1) without touching the detector.
- ``alarms(frame)``: 0/1 per row, by default ``score > threshold``.

To add a detector: write a class with these methods, give it a unique
``name`` and ``column``, and append it to ``REGISTRY``. The pipeline, the
metrics, the evaluation report and the app pick it up automatically.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Protocol, runtime_checkable

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from aquawatch.baseline import _robust_z, cusum_statistic, night_flow_scores, robust_scales
from aquawatch.model import FEATURE_COLS, select_typical_rows, train_isolation_forest
from aquawatch.settings import get_settings

LABEL_COLUMNS = ("simulated_leak_label", "simulated_event_id")


@runtime_checkable
class Detector(Protocol):
    name: ClassVar[str]
    column: ClassVar[str]

    @property
    def threshold(self) -> float: ...

    def fit(self, history: pd.DataFrame) -> Detector: ...

    def score(self, frame: pd.DataFrame) -> pd.Series: ...

    def alarms(self, frame: pd.DataFrame) -> pd.Series: ...


def _unlabelled(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop label columns before a detector sees the data (defence in depth)."""
    return frame.drop(columns=[c for c in LABEL_COLUMNS if c in frame.columns])


class _ThresholdDetector:
    """Shared behaviour: alarms are ``score > threshold``."""

    name: ClassVar[str]
    column: ClassVar[str]

    @property
    def threshold(self) -> float:
        raise NotImplementedError

    def fit(self, history: pd.DataFrame) -> _ThresholdDetector:
        return self

    def score(self, frame: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def alarms(self, frame: pd.DataFrame) -> pd.Series:
        return (self.score(frame) > self.threshold).astype(int)


@dataclass
class FlowRule(_ThresholdDetector):
    """Flow more than ``rules.flow_threshold`` (25%) above expected."""

    name: ClassVar[str] = "Simple flow rule"
    column: ClassVar[str] = "rule_pred"

    @property
    def threshold(self) -> float:
        return get_settings().rules.flow_threshold

    def score(self, frame: pd.DataFrame) -> pd.Series:
        return frame["flow_rel_dev"].astype(float)


@dataclass
class FlowPressureRule(_ThresholdDetector):
    """Flow clearly up *and* pressure down, in robust z-score units of the training window."""

    name: ClassVar[str] = "Flow + pressure rule"
    column: ClassVar[str] = "fp_rule_pred"
    _scales: pd.DataFrame | None = field(default=None, repr=False)

    @property
    def threshold(self) -> float:
        return 1.0  # score is scaled so 1 = both limits reached

    def fit(self, history: pd.DataFrame) -> FlowPressureRule:
        self._scales = robust_scales(_unlabelled(history))
        return self

    def _z(self, frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        if self._scales is None:
            raise RuntimeError("fit() first")
        return _robust_z(frame, self._scales, "flow_rel_dev"), _robust_z(frame, self._scales, "pressure_dev")

    def score(self, frame: pd.DataFrame) -> pd.Series:
        cfg = get_settings().rules
        zf, zp = self._z(frame)
        if cfg.fp_pressure_z > 0:
            pressure_part = -zp / cfg.fp_pressure_z
        else:  # no pressure condition: only flow counts
            pressure_part = pd.Series(np.inf, index=zp.index)
        return np.minimum(zf / cfg.fp_flow_z, pressure_part)

    def alarms(self, frame: pd.DataFrame) -> pd.Series:
        # Exact original rule (>= on both limits), kept so results do not move.
        cfg = get_settings().rules
        zf, zp = self._z(frame)
        return ((zf >= cfg.fp_flow_z) & (zp <= -cfg.fp_pressure_z)).astype(int)


@dataclass
class NightFlow(_ThresholdDetector):
    """Minimum night flow against the median of previous nights (score 1 = limit)."""

    name: ClassVar[str] = "Night flow (MNF)"
    column: ClassVar[str] = "mnf_pred"
    _history: pd.DataFrame | None = field(default=None, repr=False)

    @property
    def threshold(self) -> float:
        return 1.0

    def fit(self, history: pd.DataFrame) -> NightFlow:
        self._history = _unlabelled(history)
        return self

    def score(self, frame: pd.DataFrame) -> pd.Series:
        if self._history is None:
            raise RuntimeError("fit() first")
        return night_flow_scores(self._history, _unlabelled(frame))


@dataclass
class Cusum(_ThresholdDetector):
    """One-sided CUSUM on the flow deviation; alarms while the statistic exceeds h."""

    name: ClassVar[str] = "CUSUM on flow"
    column: ClassVar[str] = "cusum_pred"
    _history: pd.DataFrame | None = field(default=None, repr=False)

    @property
    def threshold(self) -> float:
        return get_settings().cusum.h

    def fit(self, history: pd.DataFrame) -> Cusum:
        self._history = _unlabelled(history)
        return self

    def score(self, frame: pd.DataFrame) -> pd.Series:
        if self._history is None:
            raise RuntimeError("fit() first")
        return cusum_statistic(self._history, _unlabelled(frame))


@dataclass
class IsolationForestDetector(_ThresholdDetector):
    """Isolation Forest on flow and pressure deviation, trained on typical rows only."""

    name: ClassVar[str] = "Isolation Forest"
    column: ClassVar[str] = "ai_pred"
    model: IsolationForest | None = field(default=None, repr=False)

    @property
    def threshold(self) -> float:
        return 0.0  # sklearn flags an outlier when decision_function < 0

    def fit(self, history: pd.DataFrame) -> IsolationForestDetector:
        self.model = train_isolation_forest(select_typical_rows(_unlabelled(history)))
        return self

    def score(self, frame: pd.DataFrame) -> pd.Series:
        if self.model is None:
            raise RuntimeError("fit() first")
        return pd.Series(-self.model.decision_function(frame[FEATURE_COLS]), index=frame.index)


# Order = display order in tables and the app.
REGISTRY: tuple[type[_ThresholdDetector], ...] = (
    FlowRule,
    FlowPressureRule,
    NightFlow,
    Cusum,
    IsolationForestDetector,
)

# Display name -> prediction column.
METHODS: dict[str, str] = {cls.name: cls.column for cls in REGISTRY}


def build_detectors() -> list[_ThresholdDetector]:
    """Fresh, unfitted instances of every registered detector."""
    return [cls() for cls in REGISTRY]

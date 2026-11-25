"""Typed, versioned settings for detectors and evaluation.

Owner: Nickel Small / Nicholas Smalling

Defaults live in ``configs/default.toml``. Precedence (lowest to highest):

1. ``configs/default.toml`` (or the file named by ``AQUAWATCH_CONFIG``)
2. environment variables ``AQUAWATCH__<SECTION>__<KEY>``, for example
   ``AQUAWATCH__CUSUM__H=10`` or ``AQUAWATCH__DATASETS__DEMO__CUTOFF=2026-11-10``

Values are validated when loaded, unknown keys are rejected (so a typo fails
loudly instead of being ignored), and ``Settings.fingerprint()`` gives a short
hash of everything that affects results, printed with every evaluation.

Uses only the standard library (dataclasses + tomllib); see
docs/adr/0001-settings-format.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import tomllib
from dataclasses import asdict, dataclass, field, fields
from functools import lru_cache
from pathlib import Path
from typing import Any

from aquawatch.config import PROJECT_ROOT

DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "default.toml"
ENV_PREFIX = "AQUAWATCH__"
PROFILE_CHOICES = ("hour", "day_type", "hour_of_week", "rolling")


class SettingsError(ValueError):
    """Raised when settings are missing, unknown or out of range."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SettingsError(message)


@dataclass(frozen=True)
class ProfileSettings:
    by: str = "day_type"
    rolling_days: int = 28

    def __post_init__(self) -> None:
        _check(self.by in PROFILE_CHOICES, f"profile.by must be one of {PROFILE_CHOICES}, got {self.by!r}")
        _check(self.rolling_days >= 7, "profile.rolling_days must be at least 7")


@dataclass(frozen=True)
class IsolationForestSettings:
    n_estimators: int = 300
    contamination: float = 0.01
    random_state: int = 17
    robust_z_cutoff: float = 3.5

    def __post_init__(self) -> None:
        _check(self.n_estimators > 0, "isolation_forest.n_estimators must be positive")
        _check(0 < self.contamination <= 0.5, "isolation_forest.contamination must be in (0, 0.5]")
        _check(self.robust_z_cutoff > 0, "isolation_forest.robust_z_cutoff must be positive")


@dataclass(frozen=True)
class RuleSettings:
    flow_threshold: float = 0.25
    fp_flow_z: float = 2.5
    fp_pressure_z: float = 1.0

    def __post_init__(self) -> None:
        _check(self.flow_threshold > 0, "rules.flow_threshold must be positive")
        _check(self.fp_flow_z > 0 and self.fp_pressure_z >= 0, "rules z thresholds must be positive")


@dataclass(frozen=True)
class NightFlowSettings:
    hours: tuple[int, ...] = (2, 3, 4)
    lookback_nights: int = 14
    k_mad: float = 3.0
    min_rise: float = 0.05

    def __post_init__(self) -> None:
        object.__setattr__(self, "hours", tuple(self.hours))
        _check(
            len(self.hours) > 0 and all(0 <= h <= 23 for h in self.hours),
            "night_flow.hours must be hours of the day (0-23)",
        )
        _check(self.lookback_nights >= 3, "night_flow.lookback_nights must be at least 3")
        _check(self.k_mad >= 0 and self.min_rise >= 0, "night_flow thresholds must be non-negative")


@dataclass(frozen=True)
class CusumSettings:
    k: float = 0.5
    h: float = 8.0

    def __post_init__(self) -> None:
        _check(self.k >= 0 and self.h > 0, "cusum.k must be >= 0 and cusum.h > 0")


@dataclass(frozen=True)
class SensorHealthSettings:
    flatline_hours: int = 6

    def __post_init__(self) -> None:
        _check(self.flatline_hours >= 3, "sensor_health.flatline_hours must be at least 3")


@dataclass(frozen=True)
class DatasetSettings:
    cutoff: str
    detect_within_hours: float | None = None

    def __post_init__(self) -> None:
        try:
            import datetime as _dt

            _dt.date.fromisoformat(str(self.cutoff)[:10])
        except ValueError as exc:
            raise SettingsError(f"dataset cutoff must be a YYYY-MM-DD date, got {self.cutoff!r}") from exc
        object.__setattr__(self, "cutoff", str(self.cutoff))


@dataclass(frozen=True)
class AppSettings:
    incident_merge_hours: int = 12
    default_detector: str = "Flow + pressure rule"

    def __post_init__(self) -> None:
        _check(self.incident_merge_hours >= 1, "app.incident_merge_hours must be at least 1")


@dataclass(frozen=True)
class Settings:
    profile: ProfileSettings = field(default_factory=ProfileSettings)
    isolation_forest: IsolationForestSettings = field(default_factory=IsolationForestSettings)
    rules: RuleSettings = field(default_factory=RuleSettings)
    night_flow: NightFlowSettings = field(default_factory=NightFlowSettings)
    cusum: CusumSettings = field(default_factory=CusumSettings)
    sensor_health: SensorHealthSettings = field(default_factory=SensorHealthSettings)
    datasets: dict[str, DatasetSettings] = field(default_factory=dict)
    app: AppSettings = field(default_factory=AppSettings)

    def dataset(self, name: str) -> DatasetSettings:
        _check(name in self.datasets, f"No [datasets.{name}] section in the settings")
        return self.datasets[name]

    def fingerprint(self) -> str:
        """Short hash of every setting that can change results (the app section is excluded)."""
        payload = {k: v for k, v in asdict(self).items() if k != "app"}
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:12]


SECTIONS = {
    "profile": ProfileSettings,
    "isolation_forest": IsolationForestSettings,
    "rules": RuleSettings,
    "night_flow": NightFlowSettings,
    "cusum": CusumSettings,
    "sensor_health": SensorHealthSettings,
    "app": AppSettings,
}


def _parse_env_value(raw: str) -> Any:
    """Parse an override as a TOML value (numbers, booleans, lists), else keep it as text."""
    try:
        return tomllib.loads(f"v = {raw}")["v"]
    except tomllib.TOMLDecodeError:
        return raw


def _apply_env(data: dict[str, Any], environ: dict[str, str]) -> None:
    for name, raw in environ.items():
        if not name.startswith(ENV_PREFIX):
            continue
        path = [part.lower() for part in name[len(ENV_PREFIX) :].split("__")]
        _check(len(path) >= 2, f"{name}: use {ENV_PREFIX}<SECTION>__<KEY>")
        node = data
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = _parse_env_value(raw)


def _build(section_cls: type, values: dict[str, Any], section: str) -> Any:
    allowed = {f.name for f in fields(section_cls)}
    unknown = set(values) - allowed
    _check(not unknown, f"Unknown setting(s) in [{section}]: {sorted(unknown)}; allowed: {sorted(allowed)}")
    try:
        return section_cls(**values)
    except TypeError as exc:
        raise SettingsError(f"[{section}]: {exc}") from exc


def load_settings(path: Path | None = None, environ: dict[str, str] | None = None) -> Settings:
    """Read the TOML file, apply environment overrides, validate and return Settings."""
    environ = dict(os.environ) if environ is None else environ
    path = Path(path or environ.get("AQUAWATCH_CONFIG") or DEFAULT_CONFIG)
    _check(path.exists(), f"Settings file not found: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    _apply_env(data, environ)

    unknown = set(data) - set(SECTIONS) - {"datasets"}
    _check(not unknown, f"Unknown settings section(s): {sorted(unknown)}")
    sections = {name: _build(cls, data.get(name, {}), name) for name, cls in SECTIONS.items()}
    datasets = {
        name: _build(DatasetSettings, values, f"datasets.{name}")
        for name, values in data.get("datasets", {}).items()
    }
    return Settings(datasets=datasets, **sections)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The settings for this process (loaded once; call ``get_settings.cache_clear()`` to reload)."""
    return load_settings()

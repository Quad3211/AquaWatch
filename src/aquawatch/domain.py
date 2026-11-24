"""Shared domain types: the nouns every part of AquaWatch talks about.

Owner: Nickel Small

Detection and evaluation work on pandas DataFrames (fast, vectorised). These
types are used at the *boundaries*, wherever results leave the core: the app,
reports, and later the database, API and notifications. Keep them small,
explicit and free of I/O.

- ``LeakEvent``: a ground-truth leak (simulated, benchmark or, later, a
  field-confirmed repair).
- ``Alarm``: a run of hours one detector flagged in one zone.
- ``Incident``: what a crew sees: one or more alarms merged, with an estimate
  of the extra water, a reason, a workflow status and (finally) an outcome.
- ``RunInfo``: what produced a set of results (data range, settings
  fingerprint, code version), so results can always be traced and repeated.
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

import pandas as pd

from aquawatch.config import PROJECT_ROOT


class IncidentStatus(StrEnum):
    """Workflow states (the full state machine arrives in build guide step D1)."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    FIELD_CHECK = "field_check"
    CLOSED = "closed"


class Outcome(StrEnum):
    """How a closed incident ended; these become real labels over time."""

    LEAK_CONFIRMED = "leak_confirmed"
    NO_LEAK_FOUND = "no_leak_found"
    DATA_ISSUE = "data_issue"
    PLANNED_WORK = "planned_work"
    THEFT_SUSPECTED = "theft_suspected"


@dataclass(frozen=True)
class LeakEvent:
    event_id: str
    zone: str
    start: pd.Timestamp
    end: pd.Timestamp
    size_m3h: float | None = None
    kind: str | None = None

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"LeakEvent {self.event_id}: end is before start")

    @staticmethod
    def from_frame(frame: pd.DataFrame) -> list[LeakEvent]:
        """Build events from a table with event_id, zone, start, end (+ optional size/kind)."""
        size_col = next((c for c in ("peak_leak_m3h", "target_leak_m3h", "size_m3h") if c in frame), None)
        return [
            LeakEvent(
                event_id=str(row["event_id"]),
                zone=str(row["zone"]),
                start=pd.Timestamp(row["start"]),
                end=pd.Timestamp(row["end"]),
                size_m3h=float(row[size_col]) if size_col and pd.notna(row[size_col]) else None,
                kind=str(row["kind"]) if "kind" in frame and pd.notna(row["kind"]) else None,
            )
            for _, row in frame.iterrows()
        ]

    @staticmethod
    def to_frame(events: Sequence[LeakEvent]) -> pd.DataFrame:
        columns = ["event_id", "zone", "start", "end", "size_m3h", "kind"]
        return pd.DataFrame([asdict(e) for e in events], columns=columns)


@dataclass(frozen=True)
class Alarm:
    zone: str
    start: pd.Timestamp
    end: pd.Timestamp
    hours: int
    detector: str


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@dataclass
class Incident:
    zone: str
    start: pd.Timestamp
    end: pd.Timestamp
    hours: int
    detector: str
    extra_flow: float
    est_volume: float
    peak_flow_rise: float
    pressure_change: float
    reason: str
    matched_events: tuple[str, ...] = ()
    labelled: bool = False  # True when ground truth was available to match against
    status: IncidentStatus = IncidentStatus.NEW
    outcome: Outcome | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def incident_id(self) -> str:
        """Stable id: the same alarm run always gets the same id (needed for idempotent jobs later)."""
        return f"{_slug(self.zone)}-{self.start:%Y%m%d%H}-{_slug(self.detector)}"


@dataclass(frozen=True)
class RunInfo:
    run_id: str
    created_utc: str
    dataset: str
    data_start: str
    data_end: str
    settings_fingerprint: str
    code_version: str

    @staticmethod
    def create(dataset: str, data_start, data_end, settings_fingerprint: str) -> RunInfo:
        created = datetime.now(UTC)
        version = code_version()
        return RunInfo(
            run_id=f"{created:%Y%m%dT%H%M%SZ}-{settings_fingerprint[:6]}-{version[:7]}",
            created_utc=created.isoformat(timespec="seconds"),
            dataset=dataset,
            data_start=str(data_start),
            data_end=str(data_end),
            settings_fingerprint=settings_fingerprint,
            code_version=version,
        )


def code_version() -> str:
    """Current git commit (with '+dirty' if there are uncommitted changes), or 'unknown'."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def as_event_frame(events: pd.DataFrame | Iterable[LeakEvent] | None) -> pd.DataFrame | None:
    """Accept events either as a table or as LeakEvent objects."""
    if events is None or isinstance(events, pd.DataFrame):
        return events
    return LeakEvent.to_frame(list(events))

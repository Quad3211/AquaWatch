"""Turn model/rule predictions into explainable investigation alerts.

Owner: Nickel Small (logic) / Jason Williams (UI consumption)
"""
from __future__ import annotations

import pandas as pd

from aquawatch.domain import Incident, IncidentStatus
from aquawatch.settings import get_settings


def _reason(row: pd.Series) -> str:
    flow_bit = (
        "Flow above its usual level for this zone, hour and day type"
        if row.get("flow_rel_dev", 0) > 0.10
        else "Flow pattern looks unusual for this zone, hour and day type"
    )
    press_bit = (
        "pressure index drops at the same time"
        if row.get("pressure_dev", 0) < -2
        else "pressure also differs from its usual level"
    )
    return f"{flow_bit}; {press_bit}."


def build_alert_table(
    scored: pd.DataFrame,
    *,
    prediction_col: str = "ai_pred",
    min_score_rows: bool = True,
    source: str | None = None,
) -> pd.DataFrame:
    """Return ranked hourly alerts for investigation (not confirmed leaks)."""
    if prediction_col not in scored.columns:
        raise KeyError(f"Missing prediction column: {prediction_col}")

    alerts = scored[scored[prediction_col] == 1].copy()
    if alerts.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "zone",
                "flow_index",
                "pressure_index",
                "flow_rel_dev",
                "pressure_dev",
                "reason",
                "next_step",
                "source",
            ]
        )

    alerts["reason"] = alerts.apply(_reason, axis=1)
    alerts["next_step"] = "Check logger quality; request field verification."
    alerts["source"] = source or (
        "Isolation Forest" if prediction_col == "ai_pred" else "Simple flow rule"
    )

    # Stronger combined deviation sorts higher (more urgent review).
    flow_up = alerts["flow_rel_dev"].clip(lower=0)
    pressure_drop = (-alerts["pressure_dev"]).clip(lower=0)
    alerts["rank_score"] = flow_up + pressure_drop / 20.0
    alerts = alerts.sort_values(["rank_score", "timestamp"], ascending=[False, True])

    cols = [
        "timestamp",
        "zone",
        "flow_index",
        "pressure_index",
        "flow_rel_dev",
        "pressure_dev",
        "reason",
        "next_step",
        "source",
        "rank_score",
    ]
    if min_score_rows:
        return alerts[cols].reset_index(drop=True)
    return alerts.reset_index(drop=True)


STATUS_LABELS = {IncidentStatus.NEW: "New: verify"}
NEXT_STEP = "Check logger quality; send crew for acoustic survey if confirmed."


def build_incidents(
    scored: pd.DataFrame,
    *,
    prediction_col: str = "ai_pred",
    detector: str | None = None,
    pressure_unit: str = "m",
    max_gap_hours: int = 1,
) -> list[Incident]:
    """Turn one detector's flagged hours into ``Incident`` objects, largest first.

    An incident is a run of flagged hours in one zone; alarms less than
    ``max_gap_hours`` apart are merged. Each gets the mean extra flow above the
    expected level, an estimated volume (hourly data: sum of extra flow), the
    peak flow rise, the mean pressure change and a plain-language reason. If the
    data has simulation labels, ``matched_events`` lists the injected leaks it
    overlapped; with real data this comes from field checks instead.
    """
    from aquawatch.metrics import episode_ids, true_events

    detector = detector or prediction_col
    night_hours = list(get_settings().night_flow.hours)  # same night as the night-flow detector
    ids = episode_ids(scored, prediction_col, max_gap_hours=max_gap_hours)
    flagged = scored.loc[ids.notna()].assign(episode=ids.dropna())
    if flagged.empty:
        return []

    flagged = flagged.assign(excess=(flagged["flow_index"] - flagged["expected_flow"]).clip(lower=0))
    runs = (
        flagged.groupby("episode")
        .agg(
            zone=("zone", "first"),
            start=("timestamp", "min"),
            end=("timestamp", "max"),
            hours=("timestamp", "size"),
            extra_flow=("excess", "mean"),
            volume=("excess", "sum"),  # hourly readings: (unit/h) x 1 h each
            peak_rise=("flow_rel_dev", "max"),
            pressure_change=("pressure_dev", "mean"),
            night_hours=("hour", lambda h: int(h.isin(night_hours).sum())),
        )
        .reset_index(drop=True)
        .sort_values(["volume", "start"], ascending=[False, True])
    )

    truth = true_events(scored) if "simulated_event_id" in scored.columns else pd.DataFrame()
    incidents = []
    for row in runs.itertuples():
        parts = [f"Inflow up to {row.peak_rise:+.0%} above usual for {row.hours} h"]
        if row.pressure_change < -0.5:
            parts.append(f"pressure {row.pressure_change:+.1f} {pressure_unit} at the same time")
        if row.night_hours:
            parts.append("raised during the night, when legitimate use is lowest")
        matched: tuple[str, ...] = ()
        if not truth.empty:
            overlaps = (truth["zone"] == row.zone) & (truth["start"] <= row.end) & (truth["end"] >= row.start)
            matched = tuple(truth.loc[overlaps, "event_id"])
        incidents.append(
            Incident(
                zone=row.zone,
                start=row.start,
                end=row.end,
                hours=int(row.hours),
                detector=detector,
                extra_flow=float(row.extra_flow),
                est_volume=float(row.volume),
                peak_flow_rise=float(row.peak_rise),
                pressure_change=float(row.pressure_change),
                reason="; ".join(parts) + ".",
                matched_events=matched,
                labelled=not truth.empty,
            )
        )
    return incidents


def incidents_to_frame(
    incidents: list[Incident], *, flow_unit: str = "m³/h", pressure_unit: str = "m"
) -> pd.DataFrame:
    """The table shown in the app: one row per incident, ranked by estimated volume."""
    volume_col = f"est_volume_lost_{flow_unit.split('/')[0]}"
    columns = [
        "priority", "zone", "start", "end", "hours", f"extra_flow_{flow_unit}", volume_col,
        "peak_flow_rise", f"pressure_change_{pressure_unit}", "reason", "matches_injected_leak",
        "status", "next_step",
    ]
    rows = []
    for priority, inc in enumerate(incidents, start=1):
        if not inc.labelled:
            match = "n/a"
        else:
            match = ", ".join(inc.matched_events) if inc.matched_events else "no (false alarm)"
        rows.append(
            {
                "priority": priority,
                "zone": inc.zone,
                "start": inc.start,
                "end": inc.end,
                "hours": inc.hours,
                f"extra_flow_{flow_unit}": inc.extra_flow,
                volume_col: inc.est_volume,
                "peak_flow_rise": inc.peak_flow_rise,
                f"pressure_change_{pressure_unit}": inc.pressure_change,
                "reason": inc.reason,
                "matches_injected_leak": match,
                "status": STATUS_LABELS.get(inc.status, inc.status.value),
                "next_step": NEXT_STEP,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def build_event_alerts(
    scored: pd.DataFrame,
    *,
    prediction_col: str = "ai_pred",
    flow_unit: str = "m³/h",
    pressure_unit: str = "m",
    max_gap_hours: int = 1,
) -> pd.DataFrame:
    """Incident table for one detector (``build_incidents`` + ``incidents_to_frame``)."""
    incidents = build_incidents(
        scored, prediction_col=prediction_col, pressure_unit=pressure_unit, max_gap_hours=max_gap_hours
    )
    return incidents_to_frame(incidents, flow_unit=flow_unit, pressure_unit=pressure_unit)

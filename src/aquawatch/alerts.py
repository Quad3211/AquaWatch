"""Turn model/rule predictions into explainable investigation alerts.

Owner: Nickel Small (logic) / Jason Williams (UI consumption)
"""
from __future__ import annotations

import pandas as pd


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


def build_event_alerts(
    scored: pd.DataFrame,
    *,
    prediction_col: str = "ai_pred",
    flow_unit: str = "m³/h",
    pressure_unit: str = "m",
    max_gap_hours: int = 1,
) -> pd.DataFrame:
    """One row per alarm episode, the way a utility crew would see it.

    An episode is a run of flagged hours in one zone (same grouping as the
    metrics). Each row gives when it started, how long it lasted, how much extra
    water flowed compared with the expected level, an estimated volume lost, the
    pressure change and a plain-language reason. If the data has simulation
    labels, ``matches_injected_leak`` says whether the alarm overlapped a real
    (injected) leak; real utility data would fill this from field checks.
    """
    from aquawatch.metrics import episode_ids, true_events

    ids = episode_ids(scored, prediction_col, max_gap_hours=max_gap_hours)
    flagged = scored.loc[ids.notna()].assign(episode=ids.dropna())
    columns = [
        "priority", "zone", "start", "end", "hours", f"extra_flow_{flow_unit}",
        f"est_volume_lost_{flow_unit.split('/')[0]}", "peak_flow_rise", f"pressure_change_{pressure_unit}",
        "reason", "matches_injected_leak", "status", "next_step",
    ]
    if flagged.empty:
        return pd.DataFrame(columns=columns)

    flagged = flagged.assign(excess=(flagged["flow_index"] - flagged["expected_flow"]).clip(lower=0))
    events = (
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
            night_hours=("hour", lambda h: int(h.isin([1, 2, 3, 4]).sum())),
        )
        .reset_index(drop=True)
    )

    def reason(row: pd.Series) -> str:
        parts = [f"Inflow up to {row.peak_rise:+.0%} above usual for {row.hours} h"]
        if row.pressure_change < -0.5:
            parts.append(f"pressure {row.pressure_change:+.1f} {pressure_unit} at the same time")
        if row.night_hours:
            parts.append("raised during the night, when legitimate use is lowest")
        return "; ".join(parts) + "."

    events["reason"] = events.apply(reason, axis=1)

    truth = true_events(scored) if "simulated_event_id" in scored.columns else pd.DataFrame()
    if truth.empty:
        events["matches_injected_leak"] = "n/a"
    else:
        def match(row: pd.Series) -> str:
            overlaps = (truth["start"] <= row.end) & (truth["end"] >= row.start)
            hit = truth[(truth["zone"] == row.zone) & overlaps]
            return ", ".join(hit["event_id"]) if len(hit) else "no (false alarm)"

        events["matches_injected_leak"] = events.apply(match, axis=1)

    events["status"] = "New: verify"
    events["next_step"] = "Check logger quality; send crew for acoustic survey if confirmed."
    events = events.sort_values(["volume", "start"], ascending=[False, True]).reset_index(drop=True)
    events.insert(0, "priority", range(1, len(events) + 1))
    events = events.rename(
        columns={
            "extra_flow": f"extra_flow_{flow_unit}",
            "volume": f"est_volume_lost_{flow_unit.split('/')[0]}",
            "peak_rise": "peak_flow_rise",
            "pressure_change": f"pressure_change_{pressure_unit}",
        }
    )
    return events[columns]

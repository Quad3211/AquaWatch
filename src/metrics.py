"""Evaluation helpers: event-level scores for leak-style alarms.

Owner: Nicholas Smalling

Why event-level? A leak is one event lasting many hours. Scoring every hourly
reading separately rewards a detector for flagging the same leak over and over,
and hides how many separate false alarms crews would be sent on. Utilities
judge a detector by:

- how many leak events it caught (event recall),
- how many alarm episodes were real (episode precision),
- how many false alarms it raises per zone per week,
- how long after a leak starts the first alarm arrives (time to detect).

With only a handful of events, every rate gets an exact (Clopper-Pearson) 95%
confidence interval so small samples are not over-read. Point-wise numbers are
kept as secondary columns for comparison with earlier results.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import precision_score, recall_score

HOURS_PER_WEEK = 168
RANDOM_BASELINE_SEED = 2026


def proportion_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Exact Clopper-Pearson interval for k successes out of n (NaN if n == 0)."""
    if n == 0:
        return float("nan"), float("nan")
    ci = binomtest(k, n).proportion_ci(confidence_level=confidence, method="exact")
    return float(ci.low), float(ci.high)


def alarm_episodes(
    scored: pd.DataFrame, pred_col: str, *, max_gap_hours: int = 1
) -> pd.DataFrame:
    """Group flagged hours into episodes per zone.

    Flags no more than ``max_gap_hours`` apart belong to the same episode, so a
    leak flagged for 10 straight hours counts as one alarm, not ten.
    """
    flagged = scored.loc[scored[pred_col] == 1, ["zone", "timestamp"]].sort_values(
        ["zone", "timestamp"]
    )
    if flagged.empty:
        return pd.DataFrame(columns=["zone", "start", "end", "hours"])
    gap = flagged.groupby("zone")["timestamp"].diff()
    new_episode = gap.isna() | (gap > pd.Timedelta(hours=max_gap_hours))
    flagged = flagged.assign(episode=new_episode.cumsum())
    return (
        flagged.groupby("episode")
        .agg(zone=("zone", "first"), start=("timestamp", "min"), end=("timestamp", "max"),
             hours=("timestamp", "size"))
        .reset_index(drop=True)
    )


def true_events(scored: pd.DataFrame) -> pd.DataFrame:
    """Injected (ground-truth) events in the scored window: zone, start, end."""
    labelled = scored[scored["simulated_event_id"].astype(str).str.len() > 0]
    if labelled.empty:
        return pd.DataFrame(columns=["event_id", "zone", "start", "end"])
    return (
        labelled.groupby("simulated_event_id")
        .agg(zone=("zone", "first"), start=("timestamp", "min"), end=("timestamp", "max"))
        .reset_index()
        .rename(columns={"simulated_event_id": "event_id"})
    )


def _overlaps(zone: str, start, end, others: pd.DataFrame) -> pd.Series:
    return (others["zone"] == zone) & (others["start"] <= end) & (others["end"] >= start)


def event_detections(scored: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    """One row per true event: was it flagged, and how many hours after it began."""
    rows = []
    for ev in true_events(scored).itertuples():
        hits = scored[
            (scored["zone"] == ev.zone)
            & (scored["timestamp"] >= ev.start)
            & (scored["timestamp"] <= ev.end)
            & (scored[pred_col] == 1)
        ]
        delay = (hits["timestamp"].min() - ev.start) / pd.Timedelta(hours=1) if len(hits) else np.nan
        rows.append({"event_id": ev.event_id, "detected": not hits.empty, "hours_to_detect": delay})
    return pd.DataFrame(rows, columns=["event_id", "detected", "hours_to_detect"])


def event_scores(scored: pd.DataFrame, pred_col: str) -> dict[str, float | int]:
    """Event-level scores for one prediction column, plus point-wise secondaries."""
    events = true_events(scored)
    episodes = alarm_episodes(scored, pred_col)
    detections = event_detections(scored, pred_col)
    detected = int(detections["detected"].sum())
    delays = detections["hours_to_detect"].dropna().tolist()

    true_episodes = sum(
        bool(_overlaps(ep.zone, ep.start, ep.end, events).any()) for ep in episodes.itertuples()
    )
    false_episodes = len(episodes) - true_episodes

    span_hours = (scored["timestamp"].max() - scored["timestamp"].min()) / pd.Timedelta(hours=1) + 1
    zone_weeks = scored["zone"].nunique() * span_hours / HOURS_PER_WEEK

    recall_lo, recall_hi = proportion_ci(detected, len(events))
    prec_lo, prec_hi = proportion_ci(true_episodes, len(episodes))
    y_true = scored["simulated_leak_label"].astype(int)
    y_pred = scored[pred_col].astype(int)

    return {
        "events_detected": detected,
        "events_total": len(events),
        "event_recall": detected / len(events) if len(events) else float("nan"),
        "event_recall_ci_low": recall_lo,
        "event_recall_ci_high": recall_hi,
        "alarm_episodes": len(episodes),
        "false_episodes": false_episodes,
        "episode_precision": true_episodes / len(episodes) if len(episodes) else float("nan"),
        "episode_precision_ci_low": prec_lo,
        "episode_precision_ci_high": prec_hi,
        "false_alarms_per_zone_week": false_episodes / zone_weeks if zone_weeks else float("nan"),
        "median_hours_to_detect": float(np.median(delays)) if delays else float("nan"),
        "pointwise_precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "pointwise_recall": float(recall_score(y_true, y_pred, zero_division=0)),
    }


def random_alarms(scored: pd.DataFrame, rate: float, seed: int = RANDOM_BASELINE_SEED) -> pd.Series:
    """Alarms raised at random at the given per-reading rate (the floor to beat)."""
    rng = np.random.default_rng(seed)
    return pd.Series((rng.random(len(scored)) < rate).astype(int), index=scored.index)


# Display name -> prediction column, in the order tables show them.
METHODS = {
    "Simple flow rule": "rule_pred",
    "Flow + pressure rule": "fp_rule_pred",
    "Night flow (MNF)": "mnf_pred",
    "CUSUM on flow": "cusum_pred",
    "Isolation Forest": "ai_pred",
}


def compare_methods(scored_test: pd.DataFrame) -> pd.DataFrame:
    """Score every method present in ``scored_test`` plus a same-rate random baseline.

    Methods are the prediction columns in ``METHODS``; at least ``rule_pred``
    and ``ai_pred`` are required.
    """
    required = {"simulated_leak_label", "simulated_event_id", "rule_pred", "ai_pred"}
    missing = required.difference(scored_test.columns)
    if missing:
        raise ValueError(f"scored_test is missing: {sorted(missing)}")

    scored = scored_test.copy()
    scored["random_pred"] = random_alarms(scored, rate=float(scored["ai_pred"].mean()))
    methods = {name: col for name, col in METHODS.items() if col in scored.columns}
    methods["Random alarms (same rate as AI)"] = "random_pred"
    rows = [{"method": name, **event_scores(scored, col)} for name, col in methods.items()]
    return pd.DataFrame(rows)


def format_comparison(table: pd.DataFrame) -> pd.DataFrame:
    """Human-readable version of ``compare_methods`` output (k/n with 95% CIs)."""

    def pct(x: float) -> str:
        return "n/a" if pd.isna(x) else f"{x:.0%}"

    out = pd.DataFrame({"method": table["method"]})
    out["leak events caught (95% CI)"] = [
        f"{r.events_detected}/{r.events_total} ({pct(r.event_recall_ci_low)}-{pct(r.event_recall_ci_high)})"
        for r in table.itertuples()
    ]
    out["real alarms / all alarms (95% CI)"] = [
        f"{r.alarm_episodes - r.false_episodes}/{r.alarm_episodes} "
        f"({pct(r.episode_precision_ci_low)}-{pct(r.episode_precision_ci_high)})"
        for r in table.itertuples()
    ]
    out["false alarms per zone-week"] = table["false_alarms_per_zone_week"].map(
        lambda x: "n/a" if pd.isna(x) else f"{x:.1f}"
    )
    out["median hours to detect"] = table["median_hours_to_detect"].map(
        lambda x: "n/a" if pd.isna(x) else f"{x:.0f}"
    )
    out["point-wise precision"] = table["pointwise_precision"].map(pct)
    out["point-wise recall"] = table["pointwise_recall"].map(pct)
    return out


def detection_by_leak_size(
    scored: pd.DataFrame,
    pred_cols: dict[str, str],
    events_table: pd.DataFrame,
    bins: tuple[float, ...] = (0.0, 0.05, 0.10, 0.20, 1.0),
) -> pd.DataFrame:
    """Share of events caught per leak-size band (leak flow as % of zone inflow).

    ``events_table`` is the simulator's events CSV (needs ``event_id`` and
    ``target_fraction_of_inflow``). This is the sensitivity curve that shows the
    smallest leak a detector reliably finds.
    """
    sizes = events_table.set_index("event_id")["target_fraction_of_inflow"]
    labels = [f"{lo:.0%}-{hi:.0%}" for lo, hi in zip(bins[:-1], bins[1:], strict=True)]
    out = None
    for name, col in pred_cols.items():
        det = event_detections(scored, col)
        det["size_band"] = pd.cut(det["event_id"].map(sizes), bins=list(bins), labels=labels)
        grouped = det.groupby("size_band", observed=False)["detected"].agg(["sum", "count"])
        pairs = zip(grouped["sum"], grouped["count"], strict=True)
        column = [f"{int(k)}/{int(n)}" if n else "-" for k, n in pairs]
        frame = pd.DataFrame({"leak size (% of zone inflow)": grouped.index.astype(str), name: column})
        out = frame if out is None else out.merge(frame, on="leak size (% of zone inflow)")
    return out

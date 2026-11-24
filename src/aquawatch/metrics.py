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

from aquawatch.domain import as_event_frame

HOURS_PER_WEEK = 168
RANDOM_BASELINE_SEED = 2026


def proportion_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Exact Clopper-Pearson interval for k successes out of n (NaN if n == 0)."""
    if n == 0:
        return float("nan"), float("nan")
    ci = binomtest(k, n).proportion_ci(confidence_level=confidence, method="exact")
    return float(ci.low), float(ci.high)


def episode_ids(scored: pd.DataFrame, pred_col: str, *, max_gap_hours: int = 1) -> pd.Series:
    """Episode number for every flagged row (NaN for unflagged rows).

    Flags in the same zone no more than ``max_gap_hours`` apart share an episode,
    so a leak flagged for 10 straight hours is one alarm, not ten.
    """
    flagged = scored.loc[scored[pred_col] == 1, ["zone", "timestamp"]].sort_values(
        ["zone", "timestamp"]
    )
    ids = pd.Series(np.nan, index=scored.index)
    if flagged.empty:
        return ids
    gap = flagged.groupby("zone")["timestamp"].diff()
    new_episode = gap.isna() | (gap > pd.Timedelta(hours=max_gap_hours))
    ids.loc[flagged.index] = new_episode.cumsum().to_numpy()
    return ids


def alarm_episodes(
    scored: pd.DataFrame, pred_col: str, *, max_gap_hours: int = 1
) -> pd.DataFrame:
    """Group flagged hours into episodes per zone: zone, start, end, hours."""
    ids = episode_ids(scored, pred_col, max_gap_hours=max_gap_hours)
    flagged = scored.loc[ids.notna(), ["zone", "timestamp"]].assign(episode=ids.dropna())
    if flagged.empty:
        return pd.DataFrame(columns=["zone", "start", "end", "hours"])
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


def _scoring_events(scored: pd.DataFrame, events: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(events to score, all events that may be active) for this window.

    Without an explicit ``events`` table, events come from the labels in
    ``scored`` (one id per leak, no overlaps). With a table (for example
    BattLeDIM, where leaks overlap and run for months), only leaks that *start*
    inside the scored window are scored; leaks that began earlier still count as
    active, so alarms they cause are not called false.
    """
    events = as_event_frame(events)
    if events is None:
        found = true_events(scored)
        return found, found
    events = events.copy()
    events["start"] = pd.to_datetime(events["start"])
    events["end"] = pd.to_datetime(events["end"])
    lo, hi = scored["timestamp"].min(), scored["timestamp"].max()
    active = events[(events["end"] >= lo) & (events["start"] <= hi)]
    return active[active["start"] >= lo], active


def _detection_end(ev, detect_within_hours: float | None):
    if detect_within_hours is None:
        return ev.end
    return min(ev.end, ev.start + pd.Timedelta(hours=detect_within_hours))


def event_detections(
    scored: pd.DataFrame,
    pred_col: str,
    *,
    events: pd.DataFrame | None = None,
    detect_within_hours: float | None = None,
) -> pd.DataFrame:
    """One row per scored event: was it flagged in time, and how many hours after it began.

    ``detect_within_hours`` limits how late an alarm may come and still count
    (needed when leaks run for months, or almost any alarm would "detect" them).
    """
    to_score, _active = _scoring_events(scored, events)
    if events is not None:
        return _detections_by_episode_start(scored, pred_col, to_score, detect_within_hours)
    rows = []
    for ev in to_score.itertuples():
        hits = scored[
            (scored["zone"] == ev.zone)
            & (scored["timestamp"] >= ev.start)
            & (scored["timestamp"] <= _detection_end(ev, detect_within_hours))
            & (scored[pred_col] == 1)
        ]
        delay = (hits["timestamp"].min() - ev.start) / pd.Timedelta(hours=1) if len(hits) else np.nan
        rows.append({"event_id": ev.event_id, "detected": not hits.empty, "hours_to_detect": delay})
    return pd.DataFrame(rows, columns=["event_id", "detected", "hours_to_detect"])


def _detections_by_episode_start(
    scored: pd.DataFrame, pred_col: str, to_score: pd.DataFrame, detect_within_hours: float | None
) -> pd.DataFrame:
    """Detection when leaks overlap: a *new* alarm episode must start in the window.

    An alarm that was already running before the leak began carries no
    information about it, so it does not count.
    """
    episodes = alarm_episodes(scored, pred_col)
    rows = []
    for ev in to_score.itertuples():
        starts = episodes[
            (episodes["zone"] == ev.zone)
            & (episodes["start"] >= ev.start)
            & (episodes["start"] <= _detection_end(ev, detect_within_hours))
        ]["start"]
        delay = (starts.min() - ev.start) / pd.Timedelta(hours=1) if len(starts) else np.nan
        rows.append({"event_id": ev.event_id, "detected": len(starts) > 0, "hours_to_detect": delay})
    return pd.DataFrame(rows, columns=["event_id", "detected", "hours_to_detect"])


def _classify_by_episode_start(
    episodes: pd.DataFrame, to_score: pd.DataFrame, detections: pd.DataFrame, detect_within_hours
) -> tuple[int, int]:
    """(true, repeat) episode counts when leaks overlap, BattLeDIM-style.

    True: the episode starts inside a scored leak's detection window. Repeat: it
    starts later during a leak this detector has already caught (scores 0).
    Everything else is false, including alarms during leaks that began before the
    test window: the detector learned those as normal, so they are not evidence.
    """
    caught = to_score[to_score["event_id"].isin(detections.loc[detections["detected"], "event_id"])]
    window_end = pd.Series(
        [_detection_end(ev, detect_within_hours) for ev in to_score.itertuples()], index=to_score.index
    )
    true = repeat = 0
    for ep in episodes.itertuples():
        in_window = (to_score["zone"] == ep.zone) & (to_score["start"] <= ep.start) & (ep.start <= window_end)
        during_caught = (
            (caught["zone"] == ep.zone) & (caught["start"] <= ep.start) & (caught["end"] >= ep.start)
        )
        if in_window.any():
            true += 1
        elif during_caught.any():
            repeat += 1
    return true, repeat


def event_scores(
    scored: pd.DataFrame,
    pred_col: str,
    *,
    events: pd.DataFrame | None = None,
    detect_within_hours: float | None = None,
) -> dict[str, float | int]:
    """Event-level scores for one prediction column, plus point-wise secondaries.

    Without ``events`` (leaks do not overlap), each alarm episode is classed as:
    - **true**: it overlaps a scored leak's detection period (start to start +
      ``detect_within_hours``, or to the leak's end if no limit is set);
    - **repeat**: it overlaps a leak that is already known (later in a long leak,
      or a leak from before the window). Like BattLeDIM's scoring, repeats count
      as neither right nor wrong;
    - **false**: it overlaps no leak at all.

    With an ``events`` table (overlapping, long-running leaks such as
    BattLeDIM), classification uses when each episode *starts*; see
    ``_classify_by_episode_start``.
    """
    to_score, active = _scoring_events(scored, events)
    episodes = alarm_episodes(scored, pred_col)
    detections = event_detections(scored, pred_col, events=events, detect_within_hours=detect_within_hours)
    detected = int(detections["detected"].sum())
    delays = detections["hours_to_detect"].dropna().tolist()

    if events is not None:
        true_episodes, repeat_episodes = _classify_by_episode_start(
            episodes, to_score, detections, detect_within_hours
        )
    else:
        windows = to_score.assign(
            end=[_detection_end(ev, detect_within_hours) for ev in to_score.itertuples()]
        )
        true_episodes = repeat_episodes = 0
        for ep in episodes.itertuples():
            if _overlaps(ep.zone, ep.start, ep.end, windows).any():
                true_episodes += 1
            elif _overlaps(ep.zone, ep.start, ep.end, active).any():
                repeat_episodes += 1
    false_episodes = len(episodes) - true_episodes - repeat_episodes
    judged = true_episodes + false_episodes

    span_hours = (scored["timestamp"].max() - scored["timestamp"].min()) / pd.Timedelta(hours=1) + 1
    zone_weeks = scored["zone"].nunique() * span_hours / HOURS_PER_WEEK

    recall_lo, recall_hi = proportion_ci(detected, len(to_score))
    prec_lo, prec_hi = proportion_ci(true_episodes, judged)
    y_true = scored["simulated_leak_label"].astype(int)
    y_pred = scored[pred_col].astype(int)

    return {
        "events_detected": detected,
        "events_total": len(to_score),
        "event_recall": detected / len(to_score) if len(to_score) else float("nan"),
        "event_recall_ci_low": recall_lo,
        "event_recall_ci_high": recall_hi,
        "alarm_episodes": len(episodes),
        "repeat_episodes": repeat_episodes,
        "false_episodes": false_episodes,
        "episode_precision": true_episodes / judged if judged else float("nan"),
        "episode_precision_ci_low": prec_lo,
        "episode_precision_ci_high": prec_hi,
        "false_alarms_per_zone_week": false_episodes / zone_weeks if zone_weeks else float("nan"),
        "median_hours_to_detect": float(np.median(delays)) if delays else float("nan"),
        "pointwise_precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "pointwise_recall": float(recall_score(y_true, y_pred, zero_division=0)),
    }


RANDOM_NAME = "Random alarms (same budget as AI)"


def random_alarms(scored: pd.DataFrame, like_col: str, seed: int = RANDOM_BASELINE_SEED) -> pd.Series:
    """Random alarms with the same budget as ``like_col``: the floor to beat.

    It raises the same *number* of alarm episodes as ``like_col``, with the same
    lengths, at random zones and times. Matching episodes rather than the
    hourly rate matters: scattered random hours make many more separate alarms
    than a real detector's clustered ones, which would let random alarms
    "detect" leaks just by alarming more often.
    """
    rng = np.random.default_rng(seed)
    lengths = alarm_episodes(scored, like_col)["hours"].astype(int).to_numpy()
    out = pd.Series(0, index=scored.index)
    if len(lengths) == 0:
        return out
    order = scored.sort_values(["zone", "timestamp"])
    by_zone = {zone: group.index.to_numpy() for zone, group in order.groupby("zone")}
    zones = list(by_zone)
    for length in rng.permutation(lengths):
        rows = by_zone[zones[rng.integers(len(zones))]]
        start = rng.integers(0, max(1, len(rows) - length + 1))
        out.loc[rows[start : start + length]] = 1
    return out


# Display name -> prediction column, in the order tables show them.
METHODS = {
    "Simple flow rule": "rule_pred",
    "Flow + pressure rule": "fp_rule_pred",
    "Night flow (MNF)": "mnf_pred",
    "CUSUM on flow": "cusum_pred",
    "Isolation Forest": "ai_pred",
}


def compare_methods(
    scored_test: pd.DataFrame,
    *,
    events: pd.DataFrame | None = None,
    detect_within_hours: float | None = None,
) -> pd.DataFrame:
    """Score every method present in ``scored_test`` plus a same-budget random baseline.

    Methods are the prediction columns in ``METHODS``; at least ``rule_pred``
    and ``ai_pred`` are required.
    """
    required = {"simulated_leak_label", "simulated_event_id", "rule_pred", "ai_pred"}
    missing = required.difference(scored_test.columns)
    if missing:
        raise ValueError(f"scored_test is missing: {sorted(missing)}")

    scored = scored_test.copy()
    scored["random_pred"] = random_alarms(scored, like_col="ai_pred")
    methods = {name: col for name, col in METHODS.items() if col in scored.columns}
    methods[RANDOM_NAME] = "random_pred"
    rows = [
        {
            "method": name,
            **event_scores(scored, col, events=events, detect_within_hours=detect_within_hours),
        }
        for name, col in methods.items()
    ]
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
        f"{r.alarm_episodes - r.false_episodes - r.repeat_episodes}/"
        f"{r.alarm_episodes - r.repeat_episodes} "
        f"({pct(r.episode_precision_ci_low)}-{pct(r.episode_precision_ci_high)})"
        for r in table.itertuples()
    ]
    if table["repeat_episodes"].sum() > 0:
        # Alarms on leaks that were already known: neither right nor wrong.
        out["repeat alarms on known leaks"] = table["repeat_episodes"].astype(int).astype(str)
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
    *,
    use_events_as_truth: bool = False,
    detect_within_hours: float | None = None,
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
        det = event_detections(
            scored,
            col,
            events=events_table if use_events_as_truth else None,
            detect_within_hours=detect_within_hours,
        )
        det["size_band"] = pd.cut(det["event_id"].map(sizes), bins=list(bins), labels=labels)
        grouped = det.groupby("size_band", observed=False)["detected"].agg(["sum", "count"])
        pairs = zip(grouped["sum"], grouped["count"], strict=True)
        column = [f"{int(k)}/{int(n)}" if n else "-" for k, n in pairs]
        frame = pd.DataFrame({"leak size (% of zone inflow)": grouped.index.astype(str), name: column})
        out = frame if out is None else out.merge(frame, on="leak size (% of zone inflow)")
    return out

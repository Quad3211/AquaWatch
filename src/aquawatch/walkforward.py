"""Walk-forward evaluation with thresholds tuned on a validation window (build guide B1).

Owner: Nicholas Smalling

A single train/test split gives one number and leaves thresholds hand-picked.
Walk-forward evaluation repeats the split over time:

    fold 1:  [ train ............ ][ validation ][ test ]
    fold 2:  [ train ....................... ][ validation ][ test ]
    ...      (training grows; every window moves forward by ``step_days``)

In each fold, each detector:

1. is fitted on the training window (no labels, suspect sensor readings left out);
2. has its threshold **tuned on the validation window without labels**: the
   lowest threshold whose alarm rate stays within the alarm budget
   (``[walk_forward] alarm_budget_per_zone_week``). That is how a utility would
   set it, by how many alarms its crews can check, and it means labels are never
   used to choose a threshold;
3. is scored on the test window, which it has never seen, with the tuned
   threshold and, for comparison, its default threshold.

Results are reported per fold and pooled over all folds (summed counts with
exact 95% confidence intervals), plus a random baseline with the same alarm
budget as the tuned Isolation Forest.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from aquawatch.detectors import METHODS, build_detectors
from aquawatch.errors import DataError
from aquawatch.metrics import (
    HOURS_PER_WEEK,
    RANDOM_NAME,
    alarm_episodes,
    event_detections,
    event_scores,
    proportion_ci,
    random_alarms,
)
from aquawatch.pipeline import build_features
from aquawatch.sensor_health import status_over_time
from aquawatch.settings import get_settings

# Candidate thresholds are taken from these quantiles of the validation scores.
_QUANTILES = np.concatenate([np.linspace(0.50, 0.99, 50), np.linspace(0.991, 0.9999, 10)])


@dataclass(frozen=True)
class Fold:
    number: int
    train_start: pd.Timestamp
    val_start: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp  # exclusive


def make_folds(
    df: pd.DataFrame, *, train_days: int, val_days: int, test_days: int, step_days: int
) -> list[Fold]:
    """Expanding-window folds over the data's time range (whole days)."""
    start = df["timestamp"].min().normalize()
    end = df["timestamp"].max()
    folds: list[Fold] = []
    val_start = start + pd.Timedelta(days=train_days)
    while True:
        test_start = val_start + pd.Timedelta(days=val_days)
        test_end = test_start + pd.Timedelta(days=test_days)
        if test_end > end + pd.Timedelta(hours=1):
            break
        folds.append(Fold(len(folds) + 1, start, val_start, test_start, test_end))
        val_start += pd.Timedelta(days=step_days)
    if not folds:
        span = (end - start).days + 1
        raise DataError(
            f"The data covers {span} days; walk-forward needs at least "
            f"{train_days + val_days + test_days} (train {train_days} + validation {val_days} "
            f"+ test {test_days}). Use a longer dataset or smaller --train-days."
        )
    return folds


def zone_weeks(frame: pd.DataFrame) -> float:
    hours = (frame["timestamp"].max() - frame["timestamp"].min()) / pd.Timedelta(hours=1) + 1
    return frame["zone"].nunique() * hours / HOURS_PER_WEEK


def tune_threshold(scores: pd.Series, frame: pd.DataFrame, budget_per_zone_week: float) -> float:
    """Lowest threshold whose alarm episodes on ``frame`` stay within the budget (label-free).

    Alarm episodes are counted the same way as in the metrics (runs of flagged
    hours per zone). If no candidate meets the budget, the strictest is used.
    """
    allowed = budget_per_zone_week * zone_weeks(frame)
    usable = scores.dropna()
    if usable.empty:
        return float("inf")
    candidates = np.unique(np.quantile(usable, _QUANTILES))
    for threshold in candidates:  # ascending: first one inside the budget = most sensitive
        flagged = frame.assign(_alarm=(scores > threshold).astype(int))
        if len(alarm_episodes(flagged, "_alarm")) <= allowed:
            return float(threshold)
    return float(candidates[-1])


def _evaluate_fold(
    df: pd.DataFrame,
    fold: Fold,
    *,
    profile_by: str | None,
    budget: float,
    events: pd.DataFrame | None,
    detect_within: float | None,
) -> tuple[list[dict], pd.DataFrame]:
    ts = df["timestamp"]
    train = df[ts < fold.val_start]
    later = df[(ts >= fold.val_start) & (ts < fold.test_end)]
    train_f, later_f = build_features(train, later, profile_by)
    train_status, later_status = status_over_time(train_f, later_f)
    healthy_train = train_f[~train_status["sensor_suspect"]]
    dead = later_status["sensor_dead"]
    is_val = later_f["timestamp"] < fold.test_start
    val_f, test_f = later_f[is_val].copy(), later_f[~is_val].copy()

    rows = []
    for detector in build_detectors():
        detector.fit(healthy_train)
        scores = detector.score(later_f).where(~dead)  # dead readings: unknown, never alarm
        threshold = tune_threshold(scores[is_val], val_f, budget)
        test_f[detector.column] = (scores[~is_val] > threshold).astype(int)
        test_f[f"{detector.column}_default"] = detector.alarms(test_f).where(~dead[~is_val], 0).astype(int)
        rows.append(
            {"method": detector.name, "threshold": threshold, "default_threshold": detector.threshold}
        )
    test_f["random_pred"] = random_alarms(test_f, like_col="ai_pred", seed=1000 + fold.number)

    results = []
    columns = {**{name: col for name, col in METHODS.items()}, RANDOM_NAME: "random_pred"}
    thresholds = {r["method"]: r for r in rows}
    for name, col in columns.items():
        variants = [("tuned", col)] + ([("default", f"{col}_default")] if name in thresholds else [])
        for variant, column in variants:
            stats = event_scores(test_f, column, events=events, detect_within_hours=detect_within)
            delays = event_detections(test_f, column, events=events, detect_within_hours=detect_within)
            results.append(
                {
                    "fold": fold.number,
                    "method": name,
                    "variant": variant,
                    "threshold": thresholds[name]["threshold" if variant == "tuned" else "default_threshold"]
                    if name in thresholds
                    else np.nan,
                    "zone_weeks": zone_weeks(test_f),
                    "hours_to_detect": list(delays["hours_to_detect"].dropna()),
                    **stats,
                }
            )
    return results, test_f


def run_walk_forward(
    df: pd.DataFrame,
    *,
    profile_by: str | None = None,
    events: pd.DataFrame | None = None,
    detect_within: float | None = None,
    train_days: int | None = None,
    val_days: int | None = None,
    test_days: int | None = None,
    step_days: int | None = None,
    budget: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Fold]]:
    """Run every fold. Returns (per-fold results, pooled results, folds)."""
    cfg = get_settings().walk_forward
    folds = make_folds(
        df,
        train_days=train_days or cfg.train_days,
        val_days=val_days or cfg.val_days,
        test_days=test_days or cfg.test_days,
        step_days=step_days or cfg.step_days,
    )
    budget = cfg.alarm_budget_per_zone_week if budget is None else budget
    per_fold: list[dict] = []
    for fold in folds:
        rows, _ = _evaluate_fold(
            df, fold, profile_by=profile_by, budget=budget, events=events, detect_within=detect_within
        )
        per_fold.extend(rows)
    table = pd.DataFrame(per_fold)
    return table, pool(table), folds


def pool(per_fold: pd.DataFrame) -> pd.DataFrame:
    """Sum counts over folds and recompute rates with exact 95% confidence intervals."""
    out = []
    for (method, variant), group in per_fold.groupby(["method", "variant"], sort=False):
        detected, total = int(group["events_detected"].sum()), int(group["events_total"].sum())
        judged = int((group["alarm_episodes"] - group["repeat_episodes"]).sum())
        true = judged - int(group["false_episodes"].sum())
        delays = [d for row in group["hours_to_detect"] for d in row]
        recall_ci = proportion_ci(detected, total)
        precision_ci = proportion_ci(true, judged)
        out.append(
            {
                "method": method,
                "variant": variant,
                "folds": len(group),
                "events_detected": detected,
                "events_total": total,
                "event_recall_ci": recall_ci,
                "true_alarms": true,
                "judged_alarms": judged,
                "precision_ci": precision_ci,
                "false_alarms_per_zone_week": group["false_episodes"].sum() / group["zone_weeks"].sum(),
                "fold_recall_range": (
                    (group["events_detected"] / group["events_total"].replace(0, np.nan)).min(),
                    (group["events_detected"] / group["events_total"].replace(0, np.nan)).max(),
                ),
                "median_hours_to_detect": float(np.median(delays)) if delays else float("nan"),
            }
        )
    return pd.DataFrame(out)


def format_pooled(pooled: pd.DataFrame) -> pd.DataFrame:
    """Readable pooled table: k/n with 95% CI, false alarms per zone-week, per-fold spread."""

    def pct(x: float) -> str:
        return "n/a" if pd.isna(x) else f"{x:.0%}"

    rows = []
    for r in pooled.itertuples():
        rows.append(
            {
                "method": r.method,
                "thresholds": r.variant,
                "leaks caught (95% CI)": f"{r.events_detected}/{r.events_total} "
                f"({pct(r.event_recall_ci[0])}-{pct(r.event_recall_ci[1])})",
                "per-fold recall range": f"{pct(r.fold_recall_range[0])}-{pct(r.fold_recall_range[1])}",
                "real / judged alarms (95% CI)": f"{r.true_alarms}/{r.judged_alarms} "
                f"({pct(r.precision_ci[0])}-{pct(r.precision_ci[1])})",
                "false alarms per zone-week": f"{r.false_alarms_per_zone_week:.2f}",
                "median hours to detect": "n/a"
                if pd.isna(r.median_hours_to_detect)
                else f"{r.median_hours_to_detect:.0f}",
            }
        )
    return pd.DataFrame(rows)

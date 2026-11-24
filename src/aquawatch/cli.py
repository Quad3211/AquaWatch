"""The `aquawatch` command line.

    aquawatch evaluate [--dataset demo|simulated|battledim] [--profile ...] [--cutoff ...]
    aquawatch train                     # save the demo Isolation Forest to models/
    aquawatch simulate [--days --seed --out]   # needs WNTR (Python <= 3.13)
    aquawatch sizing simulate|analyse   # DMA sizing study (simulate needs WNTR)
    aquawatch battledim fetch|prepare   # download + convert the BattLeDIM benchmark

Heavy imports happen inside each command, so `aquawatch --help` stays fast and
commands that need optional packages (WNTR) only fail when actually used.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path


def _evaluate(args: argparse.Namespace) -> int:
    from aquawatch.report import evaluate

    evaluate(args.dataset, cutoff=args.cutoff, profile=args.profile, detect_within=args.detect_within)
    return 0


def _train(args: argparse.Namespace) -> int:
    from aquawatch.data_loader import chronological_split, load_sensor_csv
    from aquawatch.model import fit_detector, save_model_artifacts

    train, _test = chronological_split(load_sensor_csv())
    model, profile = fit_detector(train)
    paths = save_model_artifacts(model, profile, train=train)
    for label, path in zip(("model", "profile", "metadata"), paths, strict=True):
        print(f"Saved {label + ':':10} {path}")
    return 0


def _simulate(args: argparse.Namespace) -> int:
    from aquawatch import config
    from aquawatch.simulate import SimConfig, run

    out = args.out or config.SIM_DIR
    cfg = SimConfig(days=args.days, seed=args.seed)
    began = time.perf_counter()
    readings, events = run(cfg)
    out.mkdir(parents=True, exist_ok=True)
    readings.to_csv(out / "aquawatch_wntr_readings.csv", index=False)
    events.to_csv(out / "aquawatch_wntr_events.csv", index=False)
    print(
        f"Simulated {cfg.days} days, {len(readings):,} readings, {len(events)} leaks "
        f"in {time.perf_counter() - began:.0f}s -> {out}"
    )
    return 0


def _sizing(args: argparse.Namespace) -> int:
    from aquawatch import sizing

    sizing.simulate() if args.step == "simulate" else sizing.analyse()
    return 0


def _battledim(args: argparse.Namespace) -> int:
    if args.step == "fetch":
        from aquawatch.battledim_fetch import fetch

        return fetch()
    from aquawatch import config
    from aquawatch.battledim import convert

    readings, events = convert(config.BATTLEDIM_DIR)
    readings.to_csv(config.BATTLEDIM_CSV, index=False)
    events.to_csv(config.BATTLEDIM_EVENTS_CSV, index=False)
    print(f"{len(readings):,} hourly readings, {len(events)} leaks -> {config.BATTLEDIM_DIR}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aquawatch", description="AquaWatch research prototype tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="Compare every detector on a dataset (event-level).")
    ev.add_argument("--dataset", choices=["demo", "simulated", "battledim"], default="demo")
    ev.add_argument("--cutoff", help="Override the train/test cutoff date (YYYY-MM-DD).")
    ev.add_argument(
        "--profile",
        choices=["hour", "day_type", "hour_of_week", "rolling"],
        help="How expected flow is looked up (default config.PROFILE_BY). 'rolling' = median of the "
        "previous ROLLING_PROFILE_DAYS days, updated over time.",
    )
    ev.add_argument(
        "--detect-within",
        type=float,
        help="Hours after a leak starts in which an alarm must begin to count (BattLeDIM only).",
    )
    ev.set_defaults(func=_evaluate)

    tr = sub.add_parser("train", help="Train the demo Isolation Forest and save it to models/.")
    tr.set_defaults(func=_train)

    si = sub.add_parser("simulate", help="Regenerate data/simulated/ with WNTR (needs Python <= 3.13).")
    si.add_argument("--days", type=int, default=120)
    si.add_argument("--seed", type=int, default=13)
    si.add_argument("--out", type=Path, help="Output folder (default data/simulated).")
    si.set_defaults(func=_simulate)

    sz = sub.add_parser("sizing", help="DMA sizing study (docs/DMA_SIZING.md).")
    sz.add_argument("step", choices=["simulate", "analyse"])
    sz.set_defaults(func=_sizing)

    bd = sub.add_parser("battledim", help="BattLeDIM benchmark (docs/BATTLEDIM.md).")
    bd.add_argument("step", choices=["fetch", "prepare"])
    bd.set_defaults(func=_battledim)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())

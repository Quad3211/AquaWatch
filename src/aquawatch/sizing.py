"""DMA sizing study: how small must a metered zone be for AquaWatch to find leaks?

BattLeDIM showed that one inflow meter for a whole town (about 230 m3/h) cannot
reliably find leaks of 5-15 m3/h. This study simulates zones of different sizes
side by side, each with leaks of fixed sizes, and measures how often each
detector finds them.

Two steps, because WNTR has no Python 3.14 build:

    # 1. simulate (WNTR, Python 3.12 via uv); about 1 minute per seed
    uv run --no-project --python 3.12 --with wntr==1.5.0 --with six \\
        python scripts/dma_sizing_study.py simulate

    # 2. analyse (normal project environment)
    python scripts/dma_sizing_study.py analyse

Raw simulations go to data/simulated/sizing/raw/ (gitignored, regenerable).
The summary table is written to data/simulated/sizing/dma_sizing_results.csv.

Set-up per seed: 5 zones with mean inflows of 10, 25, 50, 100 and 200 m3/h, all
at the same elevation, with pipes scaled to zone size. Demand noise follows
customer count (600 L per customer per day, so about 400 to 8,000 customers),
so bigger zones have smoother relative demand, as real ones do. Each zone gets
8 leaks of 2, 5 and 10 m3/h in turn. Training uses the first 60 days and testing
the last 60, with no labels used for training.
"""

from __future__ import annotations

import sys

from aquawatch import config

OUT_DIR = config.SIM_DIR / "sizing"
RAW_DIR = OUT_DIR / "raw"
RESULTS_CSV = OUT_DIR / "dma_sizing_results.csv"

ZONE_SIZES_M3H = (10.0, 25.0, 50.0, 100.0, 200.0)
LEAK_SIZES_M3H = (2.0, 5.0, 10.0)
SEEDS = (101, 102, 103, 104)
LITERS_PER_CUSTOMER_DAY = 600.0  # assumption: about one household's daily use
TRAIN_CUTOFF = "2026-07-31"  # 60 days train / 60 days test (start 2026-06-01, 120 days)
DETECT_WITHIN_HOURS = 24  # "found fast": an alarm within a day of the leak starting


def zone_name(size: float) -> str:
    return f"DMA {int(size)} m3/h"


def simulate() -> None:
    from aquawatch.simulate import SimConfig, run

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for seed in SEEDS:
        cfg = SimConfig(
            seed=seed,
            zones=len(ZONE_SIZES_M3H),
            zone_mean_inflow_m3h=ZONE_SIZES_M3H,
            zone_elevations_m=(20.0,) * len(ZONE_SIZES_M3H),
            zone_names=[zone_name(s) for s in ZONE_SIZES_M3H],
            leak_sizes_m3h=LEAK_SIZES_M3H,
            liters_per_customer_day=LITERS_PER_CUSTOMER_DAY,
            scale_pipes=True,
        )
        readings, events = run(cfg)
        readings.to_csv(RAW_DIR / f"readings_seed{seed}.csv", index=False)
        events.to_csv(RAW_DIR / f"events_seed{seed}.csv", index=False)
        print(f"seed {seed}: {len(readings):,} readings, {len(events)} leaks")


def analyse() -> None:
    import pandas as pd

    from aquawatch.data_loader import chronological_split, load_sensor_csv
    from aquawatch.metrics import METHODS, event_detections, event_scores
    from aquawatch.pipeline import score_all_methods

    detection_rows, alarm_rows = [], []
    for seed in SEEDS:
        readings_path = RAW_DIR / f"readings_seed{seed}.csv"
        if not readings_path.exists():
            sys.exit(f"{readings_path} not found: run the 'simulate' step first.")
        df = load_sensor_csv(readings_path)
        events = pd.read_csv(RAW_DIR / f"events_seed{seed}.csv")
        train, test = chronological_split(df, TRAIN_CUTOFF)
        scored = score_all_methods(train, test)
        for zone, zone_scored in scored.groupby("zone"):
            size = float(zone.split()[1])
            for method, col in METHODS.items():
                fast = event_detections(zone_scored, col, detect_within_hours=DETECT_WITHIN_HOURS)
                ever = event_detections(zone_scored, col)
                merged = fast.merge(ever, on="event_id", suffixes=("_24h", "_any"))
                merged = merged.merge(events[["event_id", "target_leak_m3h"]], on="event_id")
                for row in merged.itertuples():
                    detection_rows.append(
                        {
                            "seed": seed,
                            "zone_m3h": size,
                            "leak_m3h": row.target_leak_m3h,
                            "method": method,
                            "caught_24h": row.detected_24h,
                            "caught_any": row.detected_any,
                            "hours_to_detect": row.hours_to_detect_any,
                        }
                    )
                stats = event_scores(zone_scored, col)
                alarm_rows.append(
                    {
                        "seed": seed,
                        "zone_m3h": size,
                        "method": method,
                        "false_alarms_per_week": stats["false_alarms_per_zone_week"],
                    }
                )

    detections = pd.DataFrame(detection_rows)
    alarms = pd.DataFrame(alarm_rows)
    summary = (
        detections.groupby(["method", "zone_m3h", "leak_m3h"])
        .agg(
            leaks=("caught_any", "size"),
            caught_24h=("caught_24h", "sum"),
            caught_any=("caught_any", "sum"),
            median_hours_to_detect=("hours_to_detect", "median"),
        )
        .reset_index()
    )
    summary["leak_pct_of_inflow"] = (100 * summary["leak_m3h"] / summary["zone_m3h"]).round(1)
    fa = alarms.groupby(["method", "zone_m3h"])["false_alarms_per_week"].mean().round(2).reset_index()
    summary = summary.merge(fa, on=["method", "zone_m3h"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(RESULTS_CSV, index=False)

    print(f"Leaks caught within {DETECT_WITHIN_HOURS} h, by zone size (rows) and leak size (columns).")
    print(f"Test window: 60 days x {len(SEEDS)} seeds. False alarms per zone-week in the last column.\n")
    for method in METHODS:
        part = summary[summary["method"] == method]
        caught = part.pivot(index="zone_m3h", columns="leak_m3h", values="caught_24h")
        totals = part.pivot(index="zone_m3h", columns="leak_m3h", values="leaks")
        # Cells with no leaks of that size in that zone show "-" instead of crashing.
        table = caught.fillna(0).astype(int).astype(str) + "/" + totals.fillna(0).astype(int).astype(str)
        table = table.where(totals.notna(), "-")
        table.columns = [f"{c:g} m3/h leak" for c in table.columns]
        table["false alarms/wk"] = part.groupby("zone_m3h")["false_alarms_per_week"].first()
        table.index = [f"{i:g} m3/h zone" for i in table.index]
        print(f"== {method}\n{table.to_string()}\n")
    bands = [0, 2.5, 5, 10, 20, 50, 101]
    labels = ["<2.5%", "2.5-5%", "5-10%", "10-20%", "20-50%", ">=50%"]
    detections["band"] = pd.cut(
        100 * detections["leak_m3h"] / detections["zone_m3h"], bands, labels=labels, right=False
    )
    pooled = (
        detections.groupby(["band", "method"], observed=True)
        .agg(caught=("caught_24h", "sum"), leaks=("caught_24h", "size"))
        .reset_index()
    )
    pooled["cell"] = pooled["caught"].astype(int).astype(str) + "/" + pooled["leaks"].astype(str)
    rule = pooled.pivot(index="band", columns="method", values="cell")[list(METHODS)]
    rule.to_csv(OUT_DIR / "dma_sizing_by_leak_share.csv")
    print(f"== Leaks caught within {DETECT_WITHIN_HOURS} h, by leak size as a share of zone inflow")
    print(rule.to_string())
    print()
    print(f"Saved {RESULTS_CSV} and {OUT_DIR / 'dma_sizing_by_leak_share.csv'}")

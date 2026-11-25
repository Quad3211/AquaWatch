"""Convert downloaded BattLeDIM files into AquaWatch format.

    python scripts/fetch_battledim.py     # download + verify (about 70 MB, once)
    python scripts/prepare_battledim.py   # writes the two CSVs below

Outputs (gitignored, under data/external/battledim/):
    aquawatch_battledim_hourly.csv   hourly readings, zone "L-Town"
    aquawatch_battledim_events.csv   one row per leak (2018 and 2019)

Then: python scripts/AquaWatch_Evaluate.py --dataset battledim
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from src.battledim import convert  # noqa: E402


def main() -> None:
    readings, events = convert(config.BATTLEDIM_DIR)
    readings.to_csv(config.BATTLEDIM_CSV, index=False)
    events.to_csv(config.BATTLEDIM_EVENTS_CSV, index=False)
    print(f"{len(readings):,} hourly readings, {len(events)} leaks -> {config.BATTLEDIM_DIR}")


if __name__ == "__main__":
    main()

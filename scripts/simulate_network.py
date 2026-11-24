"""Generate the WNTR-simulated dataset in data/simulated/.

WNTR has no Python 3.14 build yet, so run with a separate Python via uv:

    uv run --no-project --python 3.12 --with wntr==1.5.0 --with six \
        python scripts/simulate_network.py

Options: --days N, --seed N, --out DIR. Same seed + same WNTR version gives
the same data.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.simulate import SimConfig, run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=SimConfig.days)
    parser.add_argument("--seed", type=int, default=SimConfig.seed)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "simulated")
    args = parser.parse_args()

    cfg = SimConfig(days=args.days, seed=args.seed)
    began = time.perf_counter()
    readings, events = run(cfg)
    args.out.mkdir(parents=True, exist_ok=True)
    readings.to_csv(args.out / "aquawatch_wntr_readings.csv", index=False)
    events.to_csv(args.out / "aquawatch_wntr_events.csv", index=False)
    print(f"Simulated {cfg.days} days, {len(readings):,} readings, {len(events)} leaks "
          f"in {time.perf_counter() - began:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()

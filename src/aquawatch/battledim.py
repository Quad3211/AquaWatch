"""Convert the BattLeDIM 2020 benchmark into AquaWatch's reading format.

Owner: Nickel Small

BattLeDIM (Vrachimis et al. 2020, Zenodo 10.5281/zenodo.4017659, CC BY 4.0)
simulates "L-Town", a network modelled on a real town in Cyprus, over 2018-2019
at 5-minute steps, with 33 leaks. It is the standard public benchmark for leak
detection. Files come from ``scripts/fetch_battledim.py``.

How it maps onto AquaWatch:

- **One zone, "L-Town".** Water enters only from reservoirs R1 and R2 through
  pipes p227 and p235 (both metered), so their sum is the whole network's
  inflow and every leak shows up in it. The third flow sensor (PUMP_1) only
  moves water inside the network into tank T1, so it is not added.
- **Pressure** is the median of the 33 pressure sensors.
- **Hourly means** of the 5-minute readings, to match the rest of the pipeline.
- **Leaks** come from ``dataset_configuration.yaml`` (pipe, start, end, type).
  Many are never repaired and several overlap, so the events table, not the
  per-row label, is the ground truth for scoring. ``simulated_leak_label`` is 1
  whenever any leak is releasing water.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from aquawatch.errors import DataError

ZONE = "L-Town"
INFLOW_PIPES = ("p227", "p235")
LEAK_LINE = re.compile(
    r"^-\s*(p\d+),\s*([\d-]+ [\d:]+),\s*([\d-]+ [\d:]+),\s*([\d.]+),\s*(\w+),\s*([\d-]+ [\d:]+)"
)


def _read_scada(path: Path) -> pd.DataFrame:
    # BattLeDIM CSVs use ';' as separator and ',' as decimal mark.
    frame = pd.read_csv(path, sep=";", decimal=",", parse_dates=["Timestamp"])
    return frame.set_index("Timestamp")


def read_leak_list(config_path: Path) -> pd.DataFrame:
    """Every leak in the 2018-2019 configuration: pipe, start, end, size, type."""
    rows = []
    for line in config_path.read_text().splitlines():
        match = LEAK_LINE.match(line.strip())
        if match:
            pipe, start, end, diameter, kind, peak = match.groups()
            rows.append(
                {
                    "event_id": f"BDIM-{pipe}",
                    "zone": ZONE,
                    "pipe": pipe,
                    "kind": kind,
                    "start": pd.Timestamp(start),
                    "end": pd.Timestamp(end),
                    "peak_time": pd.Timestamp(peak),
                    "leak_diameter_m": float(diameter),
                }
            )
    if not rows:
        raise DataError(f"No leaks found in {config_path}")
    return pd.DataFrame(rows)


def convert(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (hourly readings, events) built from the downloaded BattLeDIM files."""
    flows = pd.concat([_read_scada(raw_dir / f"{y}_SCADA_Flows.csv") for y in (2018, 2019)])
    pressures = pd.concat([_read_scada(raw_dir / f"{y}_SCADA_Pressures.csv") for y in (2018, 2019)])
    leak_flows = pd.concat([_read_scada(raw_dir / f"{y}_Leakages.csv") for y in (2018, 2019)]).fillna(0.0)

    # Hours with no readings (gaps in the source) are dropped, not filled.
    inflow = flows[list(INFLOW_PIPES)].sum(axis=1).resample("h").mean().dropna()
    pressure = pressures.median(axis=1).resample("h").mean()
    leak_hourly = leak_flows.resample("h").mean()
    any_leak = (leak_hourly > 1e-3).any(axis=1).reindex(inflow.index, fill_value=False)

    events = read_leak_list(raw_dir / "dataset_configuration.yaml")
    mean_inflow = float(inflow.mean())
    events["peak_leak_m3h"] = [
        round(float(leak_hourly[p].max()), 3) if p in leak_hourly else float("nan") for p in events["pipe"]
    ]
    events["target_fraction_of_inflow"] = (events["peak_leak_m3h"] / mean_inflow).round(4)

    # Per-row id: the most recently started leak still running (for display only;
    # overlapping leaks mean the events table is the real ground truth).
    latest = pd.Series("", index=inflow.index, dtype=object)
    for ev in events.sort_values("start").itertuples():
        latest[(latest.index >= ev.start) & (latest.index <= ev.end)] = ev.event_id

    readings = pd.DataFrame(
        {
            "timestamp": inflow.index,
            "zone": ZONE,
            "flow_index": inflow.round(3).to_numpy(),
            "pressure_index": pressure.reindex(inflow.index).round(3).to_numpy(),
            "hour": inflow.index.hour,
            "simulated_leak_label": any_leak.astype(int).to_numpy(),
            "simulated_event_id": latest.where(any_leak, "").to_numpy(),
        }
    )
    return readings, events

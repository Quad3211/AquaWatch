"""Physically simulated leak scenarios for AquaWatch, built with WNTR.

Owner: Nickel Small (with Team Lead)

The hand-made CSV in ``data/`` has only 6 injected events, too few to tell
detectors apart. This module builds a small 5-zone water network, runs an
hourly pressure-dependent hydraulic simulation with WNTR, injects many leaks of
different sizes, and exports readings in the same columns the pipeline already
uses. A separate events table records every leak's size and timing.

What is simulated (see data/simulated/DATASHEET.md for the full description):

- One reservoir feeding a trunk main, with five zones (DMA-like areas) at
  different elevations. Each zone has one inlet flow meter and one pressure
  logger at its far end.
- Residential demand: morning/evening peaks, weekend shift, day-to-day and
  hour-to-hour randomness, independent for every node.
- Leaks modelled as pressure-dependent orifices (WNTR ``add_leak``):
  - abrupt ("burst"): constant size from start to repair;
  - incipient: grows in four steps over one to four days before repair.
  Leak sizes span roughly 3% to 40% of the zone's average inflow, so some are
  deliberately too small to detect.
- Sensor noise on both meters.

Limits: the network is fictional and small; demand is not calibrated to any
NWC area; there is no intermittent supply, theft, meter drift or data gaps yet.

WNTR 1.5 has no build for Python 3.14, so run this module with uv:

    uv run --no-project --python 3.12 --with wntr==1.5.0 --with six \\
        python scripts/simulate_network.py

Only wntr, numpy and pandas are imported here, so it runs outside the
project environment.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

GRAVITY = 9.81
DISCHARGE_COEFF = 0.75
SECONDS_PER_HOUR = 3600

# Typical residential day: low at night, peaks around 07:00 and 19:00 (mean ~1).
DAILY_PROFILE = np.array(
    [0.45, 0.38, 0.35, 0.35, 0.42, 0.70, 1.25, 1.65, 1.55, 1.25, 1.10, 1.05,
     1.05, 1.00, 0.95, 0.95, 1.05, 1.25, 1.50, 1.55, 1.35, 1.05, 0.80, 0.60]
)
DAILY_PROFILE = DAILY_PROFILE / DAILY_PROFILE.mean()


@dataclass
class SimConfig:
    start: str = "2026-06-01"
    days: int = 120
    seed: int = 13
    zones: int = 5
    grid: int = 3  # each zone is a grid x grid block of junctions
    reservoir_head_m: float = 95.0
    zone_elevations_m: tuple[float, ...] = (8.0, 15.0, 22.0, 30.0, 38.0)
    zone_mean_inflow_m3h: tuple[float, ...] = (55.0, 40.0, 70.0, 35.0, 50.0)
    leaks_per_zone: int = 8  # at most one leak per node (WNTR limit), 8 nodes per zone
    leak_size_range: tuple[float, float] = (0.03, 0.40)  # fraction of zone mean inflow
    warmup_days: int = 3
    flow_noise_frac: float = 0.01
    pressure_noise_m: float = 0.15
    zone_names: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.zone_names:
            self.zone_names = [f"Zone {i + 1:02d}" for i in range(self.zones)]
        if len(self.zone_elevations_m) < self.zones or len(self.zone_mean_inflow_m3h) < self.zones:
            raise ValueError("Need an elevation and a mean inflow for every zone.")

    @property
    def hours(self) -> int:
        return self.days * 24


@dataclass
class Zone:
    name: str
    inlet_pipe: str
    pressure_node: str
    junctions: list[str]
    mean_inflow_m3h: float


def demand_multipliers(cfg: SimConfig, rng: np.random.Generator) -> np.ndarray:
    """Hourly demand multipliers for one node over the whole simulation."""
    start = pd.Timestamp(cfg.start)
    hours = pd.date_range(start, periods=cfg.hours, freq="h")
    weekend = hours.dayofweek >= 5
    hour_of_day = hours.hour.to_numpy()
    # Weekends: the morning peak comes an hour later and use is a little higher.
    shifted = np.where(weekend, (hour_of_day - 1) % 24, hour_of_day)
    base = DAILY_PROFILE[shifted] * np.where(weekend, 1.05, 1.0)
    day_factor = np.repeat(rng.normal(1.0, 0.05, cfg.days), 24)
    hour_noise = rng.lognormal(0.0, 0.08, cfg.hours)
    return np.clip(base * day_factor * hour_noise, 0.05, None)


def build_network(cfg: SimConfig, rng: np.random.Generator):
    """Reservoir -> trunk main -> five gridded zones, each with one inlet pipe."""
    import wntr

    wn = wntr.network.WaterNetworkModel()
    wn.add_reservoir("R", base_head=cfg.reservoir_head_m, coordinates=(0, 0))
    previous = "R"
    zones: list[Zone] = []
    for z in range(cfg.zones):
        trunk = f"T{z}"
        elev_trunk = cfg.zone_elevations_m[z] - 3.0
        wn.add_junction(trunk, base_demand=0.0, elevation=elev_trunk, coordinates=((z + 1) * 1000, 0))
        wn.add_pipe(f"P_{previous}_{trunk}", previous, trunk, length=1200, diameter=0.45, roughness=110)
        previous = trunk

        names: list[str] = []
        n_nodes = cfg.grid * cfg.grid
        per_node_m3s = cfg.zone_mean_inflow_m3h[z] / SECONDS_PER_HOUR / n_nodes
        for i in range(cfg.grid):
            for j in range(cfg.grid):
                node = f"Z{z + 1}_{i}{j}"
                pattern = f"pat_{node}"
                wn.add_pattern(pattern, demand_multipliers(cfg, rng).tolist())
                elevation = cfg.zone_elevations_m[z] + rng.uniform(0, 6) + 1.5 * (i + j)
                wn.add_junction(
                    node,
                    base_demand=per_node_m3s * rng.uniform(0.7, 1.3),
                    demand_pattern=pattern,
                    elevation=elevation,
                    coordinates=((z + 1) * 1000 + 150 * j, -300 - 150 * i),
                )
                names.append(node)
        for i in range(cfg.grid):
            for j in range(cfg.grid):
                here = f"Z{z + 1}_{i}{j}"
                if j + 1 < cfg.grid:
                    wn.add_pipe(f"P_{here}_r", here, f"Z{z + 1}_{i}{j + 1}", length=250,
                                diameter=0.15, roughness=100)
                if i + 1 < cfg.grid:
                    wn.add_pipe(f"P_{here}_d", here, f"Z{z + 1}_{i + 1}{j}", length=250,
                                diameter=0.15, roughness=100)
        inlet = f"INLET_Z{z + 1}"
        wn.add_pipe(inlet, trunk, f"Z{z + 1}_00", length=600, diameter=0.25, roughness=110)
        far = f"Z{z + 1}_{cfg.grid - 1}{cfg.grid - 1}"
        zones.append(Zone(cfg.zone_names[z], inlet, far, names, cfg.zone_mean_inflow_m3h[z]))

    opts = wn.options
    opts.time.duration = (cfg.hours - 1) * SECONDS_PER_HOUR
    opts.time.hydraulic_timestep = SECONDS_PER_HOUR
    opts.time.pattern_timestep = SECONDS_PER_HOUR
    opts.time.report_timestep = SECONDS_PER_HOUR
    opts.hydraulic.demand_model = "PDD"
    opts.hydraulic.required_pressure = 20.0
    opts.hydraulic.minimum_pressure = 0.0
    return wn, zones


def orifice_area(flow_m3h: float, pressure_m: float = 50.0) -> float:
    """Leak opening (m²) that releases ``flow_m3h`` at ``pressure_m`` (orifice law)."""
    flow_m3s = flow_m3h / SECONDS_PER_HOUR
    return flow_m3s / (DISCHARGE_COEFF * np.sqrt(2 * GRAVITY * pressure_m))


def plan_leaks(cfg: SimConfig, zones: list[Zone], rng: np.random.Generator) -> pd.DataFrame:
    """Random, non-overlapping leak schedule per zone (times in simulation hours).

    The usable period is cut into one slot per leak, and each leak starts at a
    random time inside its slot. This spreads leaks over the whole run, so both
    the training and the held-out windows contain plenty of them.
    """
    rows = []
    lo, hi = cfg.leak_size_range
    usable_start = cfg.warmup_days * 24
    slot = (cfg.hours - usable_start) // cfg.leaks_per_zone
    for zone in zones:
        # WNTR allows one leak per node, so each leak in a zone gets its own node.
        candidates = [n for n in zone.junctions if not n.endswith("_00")]
        if cfg.leaks_per_zone > len(candidates):
            raise ValueError(f"At most {len(candidates)} leaks per zone with this grid size.")
        nodes = rng.permutation(candidates)
        for k in range(cfg.leaks_per_zone):
            kind = "incipient" if rng.random() < 0.4 else "abrupt"
            if kind == "abrupt":
                duration = int(rng.integers(6, 73))
            else:
                duration = int(rng.integers(48, 145))
            slot_start = usable_start + k * slot
            # Leave at least a day of normal flow at the end of each slot.
            duration = min(duration, slot - 24)
            t = slot_start + int(rng.integers(0, slot - 24 - duration + 1))
            size_frac = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
            rows.append(
                {
                    "zone": zone.name,
                    "node": str(nodes[k]),
                    "kind": kind,
                    "start_hour": t,
                    "end_hour": t + duration,
                    "target_leak_m3h": size_frac * zone.mean_inflow_m3h,
                    "target_fraction_of_inflow": size_frac,
                }
            )
    plan = pd.DataFrame(rows)
    plan.insert(0, "event_id", [f"WNTR-{i + 1:03d}" for i in range(len(plan))])
    return plan


def _leak_area_action(control_action_cls, node, area: float):
    """A control action that changes a leak's size mid-simulation.

    WNTR 1.5 exposes ``leak_area`` as read-only, so a plain
    ``ControlAction(node, "leak_area", x)`` fails. The simulator does watch for
    changes to "leak_area", so this sets the private value and reports the change
    under the public name. Checked by tests/test_simulate.py (incipient leaks
    must reach their full size).
    """
    action = control_action_cls(node, "leak_status", True)
    action._attribute = "leak_area"
    action._private_attribute = "_leak_area"
    action._value = area
    return action


def add_leaks(wn, plan: pd.DataFrame) -> None:
    """Attach each planned leak to its node; incipient leaks grow in four steps."""
    from wntr.network.controls import Control, ControlAction, SimTimeCondition

    for ev in plan.itertuples():
        node = wn.get_node(ev.node)
        full_area = orifice_area(ev.target_leak_m3h)
        start_s = ev.start_hour * SECONDS_PER_HOUR
        end_s = ev.end_hour * SECONDS_PER_HOUR
        if ev.kind == "abrupt":
            node.add_leak(wn, area=full_area, start_time=start_s, end_time=end_s)
            continue
        # Incipient: starts at a quarter of full size and grows over the first
        # 60% of the event (at most 4 days), then stays at full size until repair.
        node.add_leak(wn, area=full_area * 0.25, start_time=start_s, end_time=end_s)
        ramp_hours = min(96, int((ev.end_hour - ev.start_hour) * 0.6))
        for step, frac in enumerate([0.5, 0.75, 1.0], start=1):
            when = start_s + int(ramp_hours * step / 3) * SECONDS_PER_HOUR
            action = _leak_area_action(ControlAction, node, full_area * frac)
            wn.add_control(f"grow_{ev.event_id}_{step}", Control(SimTimeCondition(wn, "=", when), action))


def run(cfg: SimConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate and return (readings, events) as DataFrames."""
    import wntr

    cfg = cfg or SimConfig()
    rng = np.random.default_rng(cfg.seed)
    wn, zones = build_network(cfg, rng)
    plan = plan_leaks(cfg, zones, rng)
    add_leaks(wn, plan)

    results = wntr.sim.WNTRSimulator(wn).run_sim()
    flow = results.link["flowrate"] * SECONDS_PER_HOUR  # m³/s -> m³/h
    pressure = results.node["pressure"]
    leak_flow = results.node["leak_demand"] * SECONDS_PER_HOUR

    times = pd.Timestamp(cfg.start) + pd.to_timedelta(flow.index, unit="s")
    frames = []
    for zone in zones:
        frame = pd.DataFrame(
            {
                "timestamp": times,
                "zone": zone.name,
                "flow_index": flow[zone.inlet_pipe].to_numpy()
                * (1 + rng.normal(0, cfg.flow_noise_frac, len(times))),
                "pressure_index": pressure[zone.pressure_node].to_numpy()
                + rng.normal(0, cfg.pressure_noise_m, len(times)),
                "simulated_leak_label": 0,
                "simulated_event_id": "",
            }
        )
        for ev in plan[plan["zone"] == zone.name].itertuples():
            active = leak_flow[ev.node].to_numpy() > 1e-4
            frame.loc[active, "simulated_leak_label"] = 1
            frame.loc[active, "simulated_event_id"] = ev.event_id
        frames.append(frame)

    readings = pd.concat(frames, ignore_index=True)
    readings["flow_index"] = readings["flow_index"].clip(lower=0).round(3)
    readings["pressure_index"] = readings["pressure_index"].clip(lower=0).round(3)
    readings.insert(4, "hour", readings["timestamp"].dt.hour)

    events = plan.copy()
    events["start"] = pd.Timestamp(cfg.start) + pd.to_timedelta(events["start_hour"], unit="h")
    events["end"] = pd.Timestamp(cfg.start) + pd.to_timedelta(events["end_hour"], unit="h")
    for i, ev in events.iterrows():
        window = leak_flow[ev["node"]].iloc[ev["start_hour"] : ev["end_hour"] + 1]
        events.loc[i, "peak_leak_m3h"] = round(float(window.max()), 3)
        events.loc[i, "leak_volume_m3"] = round(float(window.sum()), 1)
    events = events.drop(columns=["start_hour", "end_hour"])
    events["target_leak_m3h"] = events["target_leak_m3h"].round(3)
    events["target_fraction_of_inflow"] = events["target_fraction_of_inflow"].round(3)
    return readings, events

# Datasheet: AquaWatch WNTR-simulated dataset

**Files:** `aquawatch_wntr_readings.csv` (readings) and `aquawatch_wntr_events.csv` (one row per leak)
**Generator:** `src/aquawatch/simulate.py`, run by `scripts/simulate_network.py`
**Status:** synthetic research data. It is not NWC data, not calibrated to any real Jamaican network, and not endorsed by any organisation.

## Why it exists
The original 14-day demo CSV has only 3 leak events in its test window, too few to tell detectors apart (3/3 is consistent with a true catch rate as low as 29%). This dataset gives 40 leaks over 120 days, with sizes that run from easy to deliberately undetectable, produced by a hydraulic model instead of hand-drawn curves.

## How to regenerate
WNTR 1.5 has no Python 3.14 build yet, so run the generator with a separate Python through uv:

```bash
uv run --no-project --python 3.12 --with wntr==1.5.0 --with six python scripts/simulate_network.py
```

Options: `--days`, `--seed`, `--out`. The default is seed 13, 120 days from 2026-06-01. The same seed and WNTR version give identical files (checked by `tests/test_simulate.py`). The run takes about 30 seconds.

## What is simulated
| Part | Model |
|---|---|
| Network | One reservoir (head 95 m) feeding a 6 km trunk main. Five zones branch off it, each a 3×3 grid of junctions (250 m pipes, 150 mm) with one 250 mm inlet pipe. Zone elevations are 8–38 m plus local variation, so pressure differs by zone. |
| Hydraulics | WNTR `WNTRSimulator`, hourly steps, pressure-dependent demand (required pressure 20 m). |
| Demand | Residential daily profile with morning and evening peaks. On weekends the peak comes an hour later and use is 5% higher. Each node gets its own day-to-day (±5%) and hour-to-hour (lognormal σ = 0.08) variation. Zone mean inflows are 35–70 m³/h. |
| Leaks | 8 per zone, 40 in total, spread evenly through the run with no overlap within a zone. Each leak is a pressure-dependent orifice (WNTR `add_leak`, Cd = 0.75). 60% are **abrupt** (6–72 h, constant size). 40% are **incipient** (2–6 days): they start at a quarter of full size and grow in three steps over up to 4 days. The target size is 3–40% of the zone's mean inflow at 50 m pressure (log-uniform). |
| Measurements | The zone inlet flow meter (`flow_index`, **m³/h**) has ±1% noise. The far-end pressure logger (`pressure_index`, **m**) has ±0.15 m noise. |

## Columns
`aquawatch_wntr_readings.csv` uses the same columns as the demo CSV, so the whole pipeline runs on it unchanged. The column names stay as `*_index` for compatibility, but here they **are** in physical units (m³/h and m).

`aquawatch_wntr_events.csv` has:
- `event_id`, `zone`, `node`, `kind`
- `target_leak_m3h` and `target_fraction_of_inflow`: the leak size that was set
- `start`, `end`
- `peak_leak_m3h` and `leak_volume_m3`: what the simulator actually released, which differs from the target because real pressure differs from 50 m

A reading is labelled 1 while its zone has a leak releasing more than 0.0001 m³/h.

## Train / test split
The cutoff `2026-07-31` (`[datasets.simulated]` in `configs/default.toml`) gives 60 days for training and 60 days held out. 20 leaks start in each half. One leak runs across the cutoff, so 21 leaks are scored in the test window. Training does not use the labels.

## Results (`python scripts/AquaWatch_Evaluate.py --dataset simulated`)
21 leaks are scored in the test window. Expected flow uses the weekday/weekend × hour profile (`[profile] by = "day_type"` in `configs/default.toml`). Baseline thresholds are set once in `config.py` from standard practice; they were not tuned on the test window.

| Method | Leak events caught | Real / all alarms | False alarms per zone-week | Median hours to detect | Leaks < 5% of inflow caught |
|---|---|---|---|---|---|
| Simple flow rule (> 25%) | 10/21 (26–70%) | 36/36 | 0.0 | 22 | 0/8 |
| Flow + pressure rule | 19/21 (70–99%) | 137/154 | 0.4 | 5 | 7/8 |
| Night flow (MNF) | 18/21 (64–97%) | 44/44 | 0.0 | 13 | 6/8 |
| CUSUM on flow | 21/21 (84–100%) | 22/37 | 0.4 | 5 | 8/8 |
| Isolation Forest | 18/21 (64–97%) | 128/167 | 0.9 | 6 | 6/8 |
| Random (same alarm budget as AI) | 18/21 (64–97%) | 35/161 | 2.9 | 8 | — |

What this shows:
- **Isolation Forest does not beat the standard baselines here.**
  - The flow-and-pressure rule sees the same two signals as Isolation Forest. It catches more leaks with fewer than half the false alarms.
  - CUSUM catches every leak, including all 8 small ones.
  - Night flow raises no false alarms at all, but it detects later, because it only decides once per night.
- **The weekend fix mattered.** With the old hour-of-day profile (`--profile hour`), almost every false alarm fell on a weekend. Isolation Forest went from 5.6 to 0.9 false alarms per zone-week after the fix, and its median detection time fell from 28 to 6 hours.
- **CUSUM's alarms run on after a repair.** Its 37 alarm episodes are few, but 15 of them are false, because the build-up takes hours to fall back after a leak ends.
- **Event recall alone can be gamed.** Leaks last days, so random alarms also "catch" 18/21. Always read recall together with false alarms per zone-week and the real/all alarms column.
- **The simulator flatters simple methods.** Its demand has no holidays, events or seasonal drift, and every leak is a clean step or ramp. Real data will be harder for all methods. Treat this ranking as a hypothesis to test on NWC data, not a result.
- **Hour of week** (`--profile hour_of_week`) gives Isolation Forest similar recall but more false alarms (2.0 per zone-week), because 60 days leaves only about 8 readings per cell. It should help once there is a year of history.

## Walk-forward results (`aquawatch evaluate --dataset simulated --protocol walk-forward`)
There are 4 folds. Each trains on everything before its validation window, then has 14 days of validation and 14 days of test, moving forward 14 days per fold (first test window 2026-07-27, last ends 2026-09-21). That gives 25 test leaks in total. "Tuned" thresholds were chosen on each validation window **without labels**: the most sensitive threshold with at most 1 alarm per zone-week ([ADR 0002](../../docs/adr/0002-label-free-threshold-tuning.md)). "Default" means the fixed thresholds in `configs/default.toml`.

| Method | Thresholds | Leaks caught (95% CI) | Per-fold recall | Real / judged alarms | False alarms per zone-week | Median h to detect |
|---|---|---|---|---|---|---|
| **CUSUM on flow** | tuned | **24/25 (80–100%)** | 83–100% | 30/41 | 0.28 | 2 |
| CUSUM on flow | default | 25/25 (86–100%) | 100% | 26/51 | 0.62 | 2 |
| Flow + pressure rule | default | 22/25 (69–97%) | 83–100% | 134/151 | 0.42 | 1 |
| Isolation Forest | default | 22/25 (69–97%) | 75–100% | 124/156 | 0.80 | 2 |
| Night flow (MNF) | default | 21/25 (64–95%) | 78–100% | 36/36 | 0.00 | 2 |
| Night flow (MNF) | tuned | 14/25 (35–76%) | 25–83% | 21/21 | 0.00 | 2 |
| Simple flow rule | tuned | 13/25 (31–72%) | 44–67% | 19/19 | 0.00 | 1 |
| Isolation Forest | tuned | 11/25 (24–65%) | 25–50% | 40/44 | 0.10 | 13 |
| Flow + pressure rule | tuned | 9/25 (18–57%) | 0–67% | 21/21 | 0.00 | 3 |
| Random (same budget as tuned Isolation Forest) | — | 7/25 (12–49%) | 0–44% | 7/43 | 0.90 | 27 |

What this shows:
- **CUSUM is the strongest detector across time**, not only on one split. With thresholds tuned without labels to 1 alarm per zone-week, it catches 24 of 25 leaks with 0.28 false alarms per zone-week, a median of 2 hours after the leak starts.
- **The budget is strict here.** It counts every alarm, including those caused by real leaks in the validation window, and this simulation has a leak in each zone roughly every two weeks. So for most detectors the tuned thresholds come out stricter than the defaults: fewer false alarms, more missed leaks. The budget is a policy choice for the utility; try `--budget 2`.
- **Single splits can mislead.** Per-fold recall ranges widely (for example 25–50% for tuned Isolation Forest, 0–67% for the tuned flow + pressure rule), which is why the pooled counts with confidence intervals are the numbers to quote.
- Every detector beats random alarms with the same budget on both leaks caught and false alarms.

## Known limits (not yet simulated)
- Intermittent supply and lock-off schedules, which are common in Jamaica
- Theft or unexplained consumption
- Meter drift, flatlines and data gaps
- Seasonal or holiday demand changes
- Tank or pump operations
- Real customer counts, and calibration against any NWC network

Every result on this dataset shows how a detector behaves on a plausible simulated network, not how it performs in the field.

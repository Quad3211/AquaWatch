# AquaWatch Jamaica — data notes

## Purpose
This file documents the CSV supplied with the proof-of-concept pitch. It is **synthetic demonstration data**, not NWC telemetry, not measurements from any Jamaican community, and not a calibrated hydraulic simulation.

## Dataset summary
- File: `data/AquaWatch_Synthetic_Sensor_Data.csv`
- Records: 1,680 hourly rows
- Period: 1–14 November 2026
- Zones: five fictional zones (`Zone 01` to `Zone 05`)
- Injected scenarios: six artificial leak-like events, producing 110 labelled anomalous readings
- Time split: first 10 days for reference/training; last 4 days held out for evaluation (480 records, 58 injected anomalous readings)

## Columns
| Column | Meaning |
|---|---|
| `timestamp` | Simulated hourly timestamp |
| `zone` | Fictional service zone identifier |
| `flow_index` | Illustrative relative flow index; not litres/second or an NWC sensor value |
| `pressure_index` | Illustrative relative pressure index; not bar or an NWC sensor value |
| `hour` | Hour of day (0–23) |
| `simulated_leak_label` | Artificial ground-truth flag for evaluation only (1 = injected event reading) |
| `simulated_event_id` | ID of the injected scenario; blank for normal rows |

The simulated flow series includes a daily usage pattern and noise. Artificial leak-like events change flow and pressure by varying amounts. This intentionally creates more than one abnormal signature, rather than assuming every event is simply a large flow increase.

## Model and evaluation
- Baseline: alert when flow is more than 25% above the historical expected flow for that same zone and hour.
- AI: Isolation Forest trained on flow deviation and pressure deviation from each zone/hour's reference pattern.
- Training never reads `simulated_leak_label` or `simulated_event_id`. The zone/hour profile uses medians of all training rows, and rows that already look abnormal (robust z-score above 3.5 on flow or pressure deviation) are left out of the Isolation Forest's training set. Labels are used only to score the held-out window. (Before Phase 0, labels were used to pick "normal" training rows, which a real utility could not do.)
- Data is split chronologically, not randomly. The last four days are held out from training. They contain **3 injected events** (SIM-04, SIM-05, SIM-06; 58 readings).

### Held-out results (event-level)
Reproduce with `python scripts/AquaWatch_Evaluate.py`. An alarm episode is a run of flagged hours in one zone. Ranges are exact 95% confidence intervals. Expected flow uses a weekday/weekend × hour profile (`config.PROFILE_BY = "day_type"`); add `--profile hour` for the older hour-of-day profile.

| Method | Leak events caught | Real alarms / all alarms | False alarms per zone-week | Point-wise precision | Point-wise recall |
|---|---:|---:|---:|---:|---:|
| Simple flow rule | 3/3 (29%-100%) | 8/11 (39%-94%) | 1.1 | 86% | 33% |
| Isolation Forest | 3/3 (29%-100%) | 11/20 (32%-77%) | 3.1 | 84% | 83% |
| Random alarms (same alarm budget as AI) | 3/3 (29%-100%) | 7/17 (18%-67%) | 3.5 | 20% | 19% |

On this hand-made CSV the weekday/weekend profile is slightly *worse* than hour-of-day (the hour-of-day profile gave 0.7 and 2.1 false alarms per zone-week). The CSV has no weekly pattern, and its 10-day training window has only 3 weekend days. On the 120-day WNTR dataset, which does have a weekly pattern, the profile cuts false alarms by about 6×; see `data/simulated/DATASHEET.md`. Use the WNTR dataset for judging methods.

How to read this:
- Both detectors caught all 3 held-out events. Random alarms with the same budget as Isolation Forest (same number and length of alarms) did nearly as well, so this 4-day window cannot tell the detectors apart from chance.
- Isolation Forest flags more *hours* of each leak (higher point-wise recall), but on this CSV it is **not better** than the simple rule at the event level, and it raises more separate false alarms.
- Three events is far too few to separate the two methods: 3/3 is consistent with a true catch rate as low as 29%.
- The earlier pitch figures (91.7% precision, 75.9% vs 37.9% recall) were point-wise and used labels in training; they should not be quoted as current results.

`AquaWatch_Evaluate.py` also scores three more baselines (flow + pressure rule, night flow, CUSUM). On this CSV, night flow catches none of the 3 events: the hand-made events barely change night-time inflow. CUSUM catches 3/3 with 0.3 false alarms per zone-week. With only 3 events, none of these differences mean much.

These results do **not** show real-world effectiveness, leak-location accuracy, or real water savings.

## Assumptions and limitations
1. Flow and pressure are represented as relative indices to avoid pretending that the values are actual NWC operating units or thresholds.
2. The five zones are fictional.
3. Artificial events represent leak-like patterns only; real anomalies can also be caused by meter faults, scheduled supply changes, pump changes, valve operations, power interruptions, or sensor faults.
4. Real deployment would require access to approved telemetry, domain review of thresholds/features, labels from field investigations, privacy/security controls, and validation by water-network engineers.
5. An AquaWatch alert means **investigate this unusual pattern**, not **a leak is confirmed**.
6. Because the injected labels are known, they can be used to build a clean simulated reference set. A real pilot would need a verified normal-history period or another robust strategy; live utility data will not arrive with leak labels attached.

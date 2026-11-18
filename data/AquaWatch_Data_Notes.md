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
- The model does **not** use `simulated_leak_label` or `simulated_event_id` as input features. In this controlled simulation, `simulated_leak_label` is used to keep known-normal records in the training reference set and to score the held-out test; `simulated_event_id` is only for scenario traceability.
- Data is split chronologically, not randomly. The last four days are held out from training.

### Preliminary held-out results
| Method | Precision | Recall | True detections | False alerts | Missed injected readings |
|---|---:|---:|---:|---:|---:|
| Simple flow rule | 91.7% | 37.9% | 22 | 2 | 36 |
| Isolation Forest | 91.7% | 75.9% | 44 | 4 | 14 |

Definitions:
- Precision = true detections / all alerts.
- Recall = true detections / all injected anomalous readings.

These results show that, on this particular synthetic test, the Isolation Forest found more injected anomalous readings at the same precision, while producing two additional false alerts. They do **not** show real-world effectiveness, leak-location accuracy, or real water savings.

## Assumptions and limitations
1. Flow and pressure are represented as relative indices to avoid pretending that the values are actual NWC operating units or thresholds.
2. The five zones are fictional.
3. Artificial events represent leak-like patterns only; real anomalies can also be caused by meter faults, scheduled supply changes, pump changes, valve operations, power interruptions, or sensor faults.
4. Real deployment would require access to approved telemetry, domain review of thresholds/features, labels from field investigations, privacy/security controls, and validation by water-network engineers.
5. An AquaWatch alert means **investigate this unusual pattern**, not **a leak is confirmed**.
6. Because the injected labels are known, they can be used to build a clean simulated reference set. A real pilot would need a verified normal-history period or another robust strategy; live utility data will not arrive with leak labels attached.

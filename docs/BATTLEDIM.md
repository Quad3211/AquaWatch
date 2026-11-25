# Testing AquaWatch on the BattLeDIM 2020 benchmark

## What BattLeDIM is
BattLeDIM (Battle of the Leakage Detection and Isolation Methods, 2020) is the standard public benchmark for water leak detection. It simulates **L-Town**, a network modelled on a real town in Cyprus. It gives two years of 5-minute SCADA data:

- 2018, for training: 14 leaks
- 2019, for testing: 19 new leaks

There are 3 flow sensors, 33 pressure sensors and 82 household meters. Every leak's pipe, start, end and flow rate is published.

> Vrachimis, S. G., Eliades, D. G., Taormina, R., Ostfeld, A., Kapelan, Z., Liu, S., Kyriakou, M. S., Pavlou, P., Qiu, M., & Polycarpou, M. M. (2020). *Dataset of BattLeDIM: Battle of the Leakage Detection and Isolation Methods.* Zenodo. https://doi.org/10.5281/zenodo.4017659. Licence: CC BY 4.0.

It is still simulated data. No public dataset with real, labelled leaks at network scale was found (see `reports/AquaWatch industry readiness.md`). BattLeDIM is the closest widely used substitute.

## How to run it
```bash
python scripts/fetch_battledim.py     # about 70 MB from Zenodo, MD5-verified, resumes on drop-outs
python scripts/prepare_battledim.py   # convert to AquaWatch format
python scripts/AquaWatch_Evaluate.py --dataset battledim --profile rolling
python scripts/AquaWatch_Evaluate.py --dataset battledim --profile rolling --detect-within 24
```
Everything goes in `data/external/battledim/`, which is gitignored. The raw files are not committed.

## How it maps onto AquaWatch (`src/aquawatch/battledim.py`)
- **One zone, "L-Town".** Water enters only from reservoirs R1 and R2, through pipes p227 and p235, so their summed flow is the whole network's inflow and every leak appears in it. PUMP_1 only moves water inside the network into tank T1, so it is not added.
- **Pressure** is the median of the 33 sensors.
- Readings are converted to **hourly means**.
- **Train on 2018, test on 2019**, as in the competition. Labels are never used for training.

## How it is scored, and why it differs from the other datasets
In BattLeDIM, a leak is running in **every** hour of 2019. Many 2018 leaks are never repaired, and new leaks overlap them. Scoring "does an alarm overlap a leak?" would make every alarm look correct. Instead, following the competition's own rule that repeat alarms score zero:

- A 2019 leak counts as **caught** only if a new alarm episode **starts** within `--detect-within` hours of the leak's start (default 168 h). An alarm that was already running before the leak began carries no information about it.
- An alarm that starts later during a leak the detector already caught is a **repeat**: neither right nor wrong.
- Every other alarm is **false**. That includes alarms during leaks carried over from 2018, because the detector learned those as part of normal.
- The **random baseline raises the same number of alarms, of the same lengths, as Isolation Forest**, at random times. Matching the alarm budget, rather than the hourly rate, stops random alarms looking good just by alarming more often.

## Results (2019, 19 new leaks)
**Rolling profile** (`--profile rolling`): expected flow is the median of the previous 28 days for each hour and day type, so the baseline follows drift.

| Method | Caught within 7 days | Caught within 24 h | False alarms in 2019 (7-day / 24 h scoring) | Leaks < 5% of inflow caught (7 days) |
|---|---|---|---|---|
| Simple flow rule | 7/19 | 4/19 | 5 / 17 | 2/9 |
| Flow + pressure rule | 7/19 | 2/19 | 2 / 28 | 2/9 |
| Night flow (MNF) | 7/19 | 3/19 | 4 / 6 | 3/9 |
| CUSUM on flow | 9/19 | 2/19 | 1 / 38 | 4/9 |
| **Isolation Forest** | **13/19** | **7/19** | 4 / 14 | 6/9 |
| Random, same alarm budget as Isolation Forest | 16/19 | 2/19 | 6 / 79 | — |

**Static weekday/weekend profile** (the default for the other datasets) learns 2018 once. In 2019 the network's inflow sits permanently above that, because leaks accumulate and nothing is repaired, so every detector alarms in roughly 35–50% of all hours. That makes its recall meaningless here, so use the rolling profile for BattLeDIM.

## Walk-forward results
`aquawatch evaluate --dataset battledim --profile rolling --protocol walk-forward --train-days 180 --val-days 28 --test-days 28 --step-days 28` runs 18 monthly folds from July 2018 to December 2019. That gives 23 test leaks. Thresholds are tuned without labels to 1 alarm per week, and a leak counts as caught only if an alarm starts within 168 h of it.

| Method | Thresholds | Leaks caught (95% CI) | Real / judged alarms | False alarms per week |
|---|---|---|---|---|
| Isolation Forest | default | 15/23 (43–84%) | 50/110 | 0.83 |
| Night flow (MNF) | tuned | 14/23 (39–80%) | 41/84 | 0.60 |
| Isolation Forest | tuned | 12/23 (31–73%) | 24/57 | 0.46 |
| Simple flow rule | default | 10/23 (23–66%) | 39/74 | 0.49 |
| Flow + pressure rule | tuned | 9/23 (20–61%) | 72/142 | 0.97 |
| CUSUM on flow | default | 8/23 (16–57%) | 19/51 | 0.44 |
| **Random (same budget as tuned Isolation Forest)** | — | **15/23 (43–84%)** | 24/58 | 0.47 |

Over many folds the conclusion stands: **with one inflow meter for the whole town, no detector reliably beats random alarms with the same budget.** On the small simulated DMAs, the same method puts CUSUM far ahead of random (24/25 against 7/25). This is the DMA sizing result again: zone size, not detector choice, decides whether leaks can be found.

## What this shows
- **Only Isolation Forest clearly beats random alarms, and only when detection must be fast.** Within 24 h it catches 7 of 19 leaks with 14 false alarms. The same number of random alarms catches 2 with 79 false. With a 7-day window, random alarms do better than every detector, because alarms every few days land in most windows by chance.
- **One inflow meter for a whole town is too coarse.** L-Town takes in about 230 m³/h, and most of its 2019 leaks are only 2–7% of that, on top of seasonal changes. The competition's best teams used all 33 pressure sensors, the household meters and a calibrated hydraulic model to find leaks.
- **Implication for NWC:** zone-inflow monitoring like AquaWatch's needs **small district metered areas (DMAs)**, where a typical leak is a large share of the zone's flow. That matches the DMAs Miya built in Portmore. On the 5-zone simulated network, where zones are small, the same detectors work far better (see `data/simulated/DATASHEET.md`).
- The rolling profile is also the right default for long deployments: it adapts to seasons and to leaks that are known and accepted.

## Limits of this adaptation
AquaWatch uses only total inflow and median pressure. It does not try to localise leaks and does not use the household meters, so these results are **not** comparable to the official BattLeDIM leaderboard, which scores economic benefit and location within 300 m.

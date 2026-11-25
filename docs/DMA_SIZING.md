# DMA sizing study: how small must a metered zone be?

## Question
AquaWatch watches the inflow (and pressure) of each metered zone (district metered area, DMA). On the BattLeDIM benchmark, one meter for a whole town of about 230 m³/h could not reliably find leaks of 5–15 m³/h ([BATTLEDIM.md](BATTLEDIM.md)). On our small simulated zones it could. This study measures where the line falls, so the team can tell NWC how to size DMAs for a pilot.

## Method (`scripts/dma_sizing_study.py`)
- **Network:** each WNTR run has 5 zones side by side, with average inflows of 10, 25, 50, 100 and 200 m³/h. All are at the same elevation, and pipes are scaled to zone size. There are 4 random seeds, and each run lasts 120 days.
- **Demand:** randomness follows customer count, assuming **600 L per customer per day**, so zones range from about 400 to 8,000 customers.
  - Each household's hourly use varies a lot, but it averages out in bigger zones.
  - A day-to-day factor (weather, events, ±5%) is shared by the whole zone, so it does not average out.
- **Leaks:** each zone gets 8 leaks of **2, 5 and 10 m³/h** in turn, measured at 50 m pressure. Bursts last 6–72 h; growing leaks last 2–6 days.
- **Scoring:** the first 60 days are for training (no labels used) and the last 60 are held out. A leak is **caught** if an alarm comes **within 24 h** of it starting. Expected flow uses the weekday/weekend × hour profile.

Reproduce it:
```bash
uv run --no-project --python 3.12 --with wntr==1.5.0 --with six python scripts/dma_sizing_study.py simulate
python scripts/dma_sizing_study.py analyse
```
Results are saved in `data/simulated/sizing/` (raw runs are gitignored).

## Results
**By leak size as a share of zone inflow**, pooled over all zone sizes: leaks caught within 24 h, out of leaks tested.

| Leak as % of zone inflow | Simple flow rule | Flow + pressure | Night flow | CUSUM | Isolation Forest |
|---|---|---|---|---|---|
| < 2.5% | 0/8 | 0/8 | 0/8 | 2/8 | 1/8 |
| 2.5–5% | 0/12 | 0/12 | 2/12 | 2/12 | 3/12 |
| 5–10% | 2/17 | 1/17 | 3/17 | 7/17 | 5/17 |
| 10–20% | 7/12 | 6/12 | 7/12 | 9/12 | 8/12 |
| 20–50% | 18/20 | 17/20 | 16/20 | 19/20 | 19/20 |
| ≥ 50% | 12/12 | 12/12 | 11/12 | 12/12 | 12/12 |

**By zone size, CUSUM:** caught within 24 h, and false alarms per zone-week.

| Zone | 2 m³/h leak | 5 m³/h leak | 10 m³/h leak | False alarms/wk |
|---|---|---|---|---|
| 10 m³/h (~400 customers) | 4/4 | 8/8 | 4/4 | 0.26 |
| 25 m³/h (~1,000) | 2/5 | 8/8 | 4/4 | 0.61 |
| 50 m³/h (~2,000) | 1/4 | 6/8 | 3/4 | 0.85 |
| 100 m³/h (~4,000) | 0/4 | 3/8 | 3/4 | 0.93 |
| 200 m³/h (~8,000) | 2/4 | 1/8 | 2/4 | 0.73 |

The same table for every detector is in `data/simulated/sizing/dma_sizing_results.csv`, and in the app's **Insights: DMA size** tab.

## Rule of thumb
- A leak is caught within a day almost every time (92–100%) once it is **about 20% or more of the zone's average inflow**. At 10–20% it is caught about half to three-quarters of the time. Below 10% it is mostly missed.
- So, to catch a leak of *L* m³/h within a day, keep DMAs to about **5 × L** m³/h of average inflow. For a 5 m³/h leak, that is about 25 m³/h, roughly 1,000 customers at 600 L per customer per day.
- **CUSUM** and **Isolation Forest** find the most small leaks. The simple flow rule and night flow raise the fewest false alarms (≤ 0.12 per zone-week), but miss most small leaks. Bigger zones do not reduce false alarms. For CUSUM and Isolation Forest they rise from the smallest zone to the larger ones.

## Caveats
- This is a simulated network, not calibrated to NWC. The 600 L per customer per day figure and the ±5% day-to-day factor are assumptions. If real day-to-day variation is smaller, bigger zones would do better.
- There are only 4–12 leaks per cell, so treat single cells as rough. The pooled table is more reliable.
- Zones here have continuous supply. Intermittent supply (lock-offs and refills) would make detection harder; that is not simulated yet.
- Catching a leak "within 24 h" is a demanding target. Allowing a few days catches more leaks in big zones (see `caught_any` in the results CSV).

# ADR 0002: Tune thresholds to an alarm budget, without labels

**Status:** accepted (build guide step B1)

## Context
Detector thresholds were fixed by hand in `configs/default.toml`. Walk-forward evaluation (`aquawatch evaluate --protocol walk-forward`) needs each detector's threshold to be chosen on a validation window that comes before the test window. Two ways to choose:
1. **Maximise leaks caught on the validation window.** This needs leak labels, and a real utility does not have them; NWC's repair logs arrive late and are incomplete.
2. **Meet an alarm budget.** Pick the most sensitive threshold whose alarm rate on the validation window stays within what crews can check, for example 1 alarm per zone per week. This needs no labels.

## Decision
Use option 2. `[walk_forward] alarm_budget_per_zone_week` (default 1.0) is the budget. For each detector and fold, `tune_threshold` tries candidate thresholds from the validation scores' quantiles, lowest first, and keeps the first whose alarm episodes per zone-week are within budget. Each report also shows the fixed default thresholds next to the tuned ones.

## Consequences
- Training and threshold choice never read leak labels, so the method can run on real NWC data as it is.
- The budget counts *all* alarms, including those caused by real leaks in the validation window. Where leaks are frequent, as in the simulation, tuned thresholds are therefore stricter than the defaults: fewer false alarms, more missed leaks. That is the trade-off a fixed crew capacity imposes.
- The budget is a policy choice for the utility, not a model parameter. Try `--budget 2` or `--budget 0.5` to see the trade-off.

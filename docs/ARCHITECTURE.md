# AquaWatch architecture (Stage 0)

**Owner:** Nathanael Coote (Team Lead)  
**Status:** Stage 0 test product — layered pipeline, no microservices

## One-sentence model

CSV readings → compare each zone/hour to its own normal → rule + Isolation Forest → ranked investigation alerts in Streamlit.

## Current runtime flow

```text
data/*.csv
    │
    ▼
src/data_loader.py      load, validate, chronological split
    │
    ▼
src/model.py            zone/hour profile + deviation features
    │
    ├──────────────► src/baseline.py     25% flow rule
    │
    └──────────────► Isolation Forest    unusual combinations
                        │
                        ▼
                   src/alerts.py         reason + next step
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
     app.py (UI)              src/metrics.py
                              scripts/AquaWatch_Evaluate.py
```

## Module seams (keep stable)

| Module | Interface idea | Must not do |
|---|---|---|
| `data_loader` | `load_sensor_csv()` / `chronological_split()` | Train models |
| `model` | profile + deviations + Isolation Forest | Render UI |
| `baseline` | rule predictions from `flow_rel_dev` | Use leak labels as features |
| `alerts` | ranked table with explanation | Change model training |
| `metrics` | precision/recall comparison | Talk to Streamlit widgets |
| `app.py` | call `src/` only | Embed detection math |

## Design rules

1. **Labels are evaluation-only** — never Isolation Forest input features.  
2. **Chronological split** — no future readings in the training profile.  
3. **UI is a client of `src/`** — detection stays testable without Streamlit.  
4. **Alert language** — investigate / review, never “leak confirmed.”

## Staged evolution (research roadmap)

| Stage | Architecture change | Research focus |
|---|---|---|
| **0 (now)** | CSV → pandas → sklearn → Streamlit | Isolation Forest; NRW vs leaks; zone/hour baselines |
| **1** | Better explanations, Plotly highlight, inject demo | Alert UX; false-positive cost for field teams |
| **2** | SQLite/Postgres + field feedback loop | Labeling outcomes; privacy for utility CSVs |
| **3** | Scheduled ingest, login, hosting | DMA/pressure-zone ops; sit beside NWC/Miya, not replace |

## Team ownership of layers

- **Data & Model:** Nickel + Nicholas (`src/data_loader`, `baseline`, `model`, `metrics`, `alerts` logic)
- **Interface:** Jason + Romaro (`app.py`, charts, demo controls)
- **Test & present:** Mahatma (checklist + live demo)
- **Integrate / scope:** Nathanael (this doc, README, GitHub, gates)

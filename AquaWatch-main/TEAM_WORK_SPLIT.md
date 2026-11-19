# AquaWatch Jamaica — detailed team work split

**Goal:** ship a Phase 1 test product first (CSV → alerts → demo), prove it works, then optionally harden into a Phase 2 product.

**Deadline focus:** prototype ready by **4 December 2026**.

**Rule:** nobody builds Phase 2 (database, login, cloud, live NWC feeds) until Phase 1 passes Mahatma’s checklist.

**If you do not know what to do today:** open [`docs/STAGE0_TASK_INSTRUCTIONS.md`](docs/STAGE0_TASK_INSTRUCTIONS.md) and follow your name section step by step.  
**Board:** https://github.com/users/Quad3211/projects/1

---

## Team at a glance

| Person | Role | Effort | Owns |
|---|---|---|---|
| **Nathanael Coote** | Team Lead / Integrator | High | Scope, repo, glue, README, trainer updates |
| **Nickel Small** | Data & Model (primary) | Highest | Isolation Forest, training split, model module |
| **Nicholas Smalling** | Data & Model (support) | High | Data loader, baseline rule, metrics, data notes |
| **Jason Williams** | Interface (primary) | High | Streamlit layout, alert table, navigation |
| **Romaro Dixion** | Interface (support) | High | Charts, inject-demo controls, UI polish |
| **Mahatma Williams** | Tester & Presenter | **Lowest** | Scenario checklist, demo rehearsal, slide/demo notes |

---

## Phase plan

### Phase 1 — Test product (build this first)

Prove: *Can the AI flag unusual zone patterns and show an explainable investigation lead?*

Includes:
- Load synthetic CSV
- Zone/hour baseline + Isolation Forest
- Ranked alert table + chart
- Rule vs AI metrics
- 2-minute live demo

Does **not** include: real NWC data, accounts, cloud deploy, mobile app.

### Phase 2 — Real product (only after Phase 1 works)

Add only what is needed:
- Save alerts + field feedback (SQLite/Postgres)
- Simple login
- Hosted demo URL
- Optional scheduled CSV re-score

---

## Detailed ownership by file / module

| Path | Owner | Backup | What “done” means |
|---|---|---|---|
| `src/data_loader.py` | Nicholas | Nickel | Loads CSV, validates columns, returns clean DataFrame |
| `src/baseline.py` | Nicholas | Nickel | 25% flow rule predictions |
| `src/model.py` | Nickel | Nicholas | Builds profile, trains Isolation Forest, predicts |
| `src/alerts.py` | Nickel | Jason | Ranked alerts with short reason + next step |
| `src/metrics.py` | Nicholas | Nickel | Precision/recall table for rule vs AI |
| `app.py` | Jason | Romaro | Streamlit pages wire up to `src/` |
| Charts / inject demo UI | Romaro | Jason | Zone chart + demo inject path works |
| `tests/test_pipeline.py` | Nicholas | Nickel | Automated smoke tests pass |
| `tests/MAHATMA_TEST_CHECKLIST.md` | Mahatma | Nathanael | Manual scenarios checked off |
| `README.md` | Nathanael | Mahatma | Install, run, demo steps clear |
| `data/AquaWatch_Data_Notes.md` | Nicholas | Nathanael | Synthetic limits stay accurate |
| Pitch deck / rehearsal | Mahatma | Nathanael | Demo script rehearsed once as a group |

---

## Person-by-person task lists

### Nathanael Coote — Team Lead

**Week of 18–20 Nov**
- [x] Confirm Phase 1 scope with the group (no Phase 2 creep) — `docs/STAGE0_SCOPE.md`
- [x] Make sure everyone can run the repo (`pip install -r requirements.txt`; use `python -m streamlit run app.py`)
- [x] Assign this work-split file; track blockers daily — `docs/BLOCKERS.md` + GitHub `Quad3211/AquaWatch`
- [x] Document Stage 0 architecture — `docs/ARCHITECTURE.md`
- [x] Connect project to GitHub for team clone/push

**Week of 23–27 Nov**
- [ ] Integrate model + UI once both exist
- [ ] Keep README install/run/demo sections accurate
- [ ] Decide freeze date for features

**Week of 30 Nov–4 Dec**
- [ ] Final integration check
- [ ] Trainer update / submission packaging
- [ ] Lead Q&A on pitch day

**Do not own:** model tuning details, pixel-level UI polish, running every manual test (Mahatma does that).

---

### Nickel Small — Data & Model (primary)

**Week of 18–20 Nov**
- [ ] Review `data/AquaWatch_Synthetic_Sensor_Data.csv` + data notes
- [ ] Finish / harden `src/model.py` (profile + Isolation Forest)
- [ ] Agree feature columns with Nicholas (`flow_rel_dev`, `pressure_dev`)

**Week of 23–27 Nov**
- [ ] Deliver `detect`-style API Jason can call from Streamlit
- [ ] Help `src/alerts.py` explanations (flow/pressure language)
- [ ] Confirm held-out metrics still match pitch (~91.7% / 75.9%)

**Week of 30 Nov–4 Dec**
- [ ] Freeze model settings (`random_state`, contamination)
- [ ] Support demo if model questions come up

---

### Nicholas Smalling — Data & Model (support)

**Week of 18–20 Nov**
- [ ] Own `src/data_loader.py` and `src/baseline.py`
- [ ] Own `src/metrics.py` + keep `scripts/AquaWatch_Evaluate.py` working
- [ ] Update data notes if anything about the CSV changes

**Week of 23–27 Nov**
- [ ] Write `tests/test_pipeline.py` smoke tests
- [ ] Pair with Nickel on alert scoring edge cases
- [ ] Give Jason a sample alerts DataFrame shape

**Week of 30 Nov–4 Dec**
- [ ] Re-run evaluation before freeze
- [ ] Double-check “labels are not model features” wording in docs

---

### Jason Williams — Interface (primary)

**Week of 18–20 Nov**
- [ ] Streamlit skeleton in `app.py` (pages/sections)
- [ ] Wire “Load data” to `src.data_loader`
- [ ] Alert table page (zone, time, method, reason)

**Week of 23–27 Nov**
- [ ] Connect alerts from Nickel’s model/alert modules
- [ ] Metrics section using `src.metrics`
- [ ] Keep UI readable for a projector

**Week of 30 Nov–4 Dec**
- [ ] Bug-fix with Mahatma
- [ ] Freeze UI; no new pages after freeze

---

### Romaro Dixion — Interface (support)

**Week of 18–20 Nov**
- [ ] Plotly (or Streamlit chart) for one zone’s flow + pressure
- [ ] Highlight injected / alert window on the chart

**Week of 23–27 Nov**
- [ ] “Demo inject” control: normal zone → leak-like pattern → alert appears
- [ ] Polish spacing, titles, empty states (“no alerts”)

**Week of 30 Nov–4 Dec**
- [ ] Make demo path one-click for Mahatma
- [ ] Capture 2–3 screenshots for backup if live demo fails

---

### Mahatma Williams — Tester & Presenter (**lightest load**)

Mahatma does **not** write the model or build the dashboard.

**Week of 18–20 Nov** (light)
- [ ] Read `tests/MAHATMA_TEST_CHECKLIST.md`
- [ ] Confirm he can install deps and open the app once Nathan/Jason has a skeleton
- [ ] Skim pitch deck speaking order

**Week of 23–27 Nov** (light)
- [ ] Run checklist each time Jason says “try this build”
- [ ] File short bug notes (what you clicked → what broke → screenshot name)
- [ ] Draft 2-minute demo script (normal → inject → alert)

**Week of 30 Nov–4 Dec** (still light, but important)
- [ ] Final checklist pass
- [ ] Lead live demo on pitch day
- [ ] Keep backup screenshots ready
- [ ] Help Nathanael with slide timing only (not redesign)

**Out of scope for Mahatma**
- Isolation Forest code
- Streamlit page architecture
- Data cleaning / metrics math
- Cloud deploy / database work

---

## Week-by-week handoffs

```text
18–20 Nov   Nicholas: loader + baseline ready
            Nickel: model trains on CSV
            Jason: empty Streamlit shell
            Romaro: first chart from CSV
            Mahatma: can launch app
            Nathanael: everyone unblocked

23–27 Nov   Nickel+Nicholas: alerts + metrics API stable
            Jason+Romaro: alerts table + chart + inject demo
            Mahatma: checklist on real build
            Nathanael: integrate + README

30 Nov–4 Dec Freeze → test → rehearse → present
```

---

## Definition of done (Phase 1)

Phase 1 is done when **all** are true:

1. `python scripts/AquaWatch_Evaluate.py` prints rule vs AI metrics
2. `python -m streamlit run app.py` loads the synthetic CSV
3. Alert list shows Zone 03-style investigation leads with a reason
4. Chart shows flow up + pressure drop for an alert window
5. Mahatma’s checklist is fully checked
6. Group can demo in ≤ 2 minutes without claiming real leak confirmation

---

## Speaking order on pitch day (reminder)

1. **Nathanael** — open + problem  
2. **Jason or Romaro** — solution / UI  
3. **Nickel or Nicholas** — data + results  
4. **Mahatma** — plan + live demo  
5. **Nathanael** — close / Q&A  

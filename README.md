# AquaWatch Jamaica — Group 13

Phase 1 **test product** for the Smart Caribbean Utilities pitch: load zone flow/pressure readings, compare a simple rule to Isolation Forest, and show explainable investigation alerts.

**GitHub:** https://github.com/Quad3211/AquaWatch  
**Project board:** https://github.com/users/Quad3211/projects/1  
**Clone:** `git clone git@github.com:Quad3211/AquaWatch.git`

> Synthetic demonstration data only. Not endorsed by NWC, Miya Jamaica, or any named organisation. An alert means **investigate this pattern**, not **a leak is confirmed**.

## Stage 0 status (Team Lead)

- [x] Phase 1 scope locked — see [docs/STAGE0_SCOPE.md](docs/STAGE0_SCOPE.md)
- [x] Architecture documented — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [x] Work split assigned — see [TEAM_WORK_SPLIT.md](TEAM_WORK_SPLIT.md)
- [x] Blocker log started — see [docs/BLOCKERS.md](docs/BLOCKERS.md)
- [x] Guide gap checklist — see [docs/GUIDE_GAP_CHECKLIST.md](docs/GUIDE_GAP_CHECKLIST.md)
- [x] Research log template — see [docs/research_log.md](docs/research_log.md)
- [x] Contribution log — see [docs/CONTRIBUTION_LOG.md](docs/CONTRIBUTION_LOG.md)
- [x] Install / evaluate / Streamlit path verified
- [x] Repository connected to GitHub

## Quick start

```bash
git clone git@github.com:Quad3211/AquaWatch.git
cd AquaWatch
pip install -r requirements.txt
python scripts/AquaWatch_Evaluate.py
python scripts/train_and_save_model.py
python -m streamlit run app.py
```

If `streamlit` is not recognized in PowerShell, always use `python -m streamlit` (the Scripts folder may not be on PATH).

`train_and_save_model.py` writes `models/isolation_forest.skops` plus `model_metadata.json`. Model files are generated, not committed (pickle/joblib files can run code when loaded). If they are missing, the app trains in-session instead.

Optional checks:

```bash
python -m pytest -v
```

## Development (uv, lint, CI)

`pyproject.toml` + `uv.lock` pin exact, reproducible versions. With [uv](https://docs.astral.sh/uv/) installed:

```bash
uv sync                      # create .venv with locked versions
uv run pytest -v             # tests, including an app smoke test
uv run ruff check .          # lint
uv run pre-commit install    # optional: lint + large-file check before each commit
```

If you change dependencies, edit both `pyproject.toml` and `requirements.txt`, then run `uv lock`. GitHub Actions (`.github/workflows/ci.yml`) runs lock check, lint, tests, train + evaluate and `pip-audit` on every pull request. Dependabot opens weekly dependency PRs.

## Using the app

`python -m streamlit run app.py`, then in the sidebar:

- **Dataset:** the 120-day simulated network (default), the original 14-day demo CSV, or your own upload (you pick the training cutoff).
- **Detector:** simple flow rule, flow + pressure rule (default), night flow, CUSUM or Isolation Forest.

Tabs:

- **Overview:** headline numbers and which zones to check first.
- **Alerts:** incidents ranked by estimated extra water, each with a plain-language reason. Alarms less than 12 h apart in a zone are merged into one incident.
- **Chart:** measured vs expected flow and pressure, with injected leaks shaded and alarms marked.
- **Metrics:** every detector scored on the same window.

## Simulated dataset (WNTR)

`data/simulated/` holds a 120-day, 5-zone dataset with 40 leaks, produced by a hydraulic model (WNTR). Evaluate on it with:

```bash
python scripts/AquaWatch_Evaluate.py --dataset simulated
```

See [data/simulated/DATASHEET.md](data/simulated/DATASHEET.md) for how it was made, how to regenerate it, and its limits.

## Benchmark: BattLeDIM 2020

To test on the standard public leak-detection benchmark (two years, 33 leaks, CC BY 4.0), run `scripts/fetch_battledim.py` then `scripts/prepare_battledim.py`. See [docs/BATTLEDIM.md](docs/BATTLEDIM.md) for how the data is mapped, how it is scored, and the results.

## DMA sizing study

How small must a metered zone be for AquaWatch to find leaks? Simulated zones of 10–200 m³/h with leaks of 2–10 m³/h give a rule of thumb: keep zones to about **5 × the smallest leak you need to catch within a day**. See [docs/DMA_SIZING.md](docs/DMA_SIZING.md), or the app's Insights tab.

## Cursor agent

To let the Cursor CLI agent work on the repo with the project's limits, put `CURSOR_API_KEY` in `.env` (copy `.env.example`) and run `scripts/cursor_agent.ps1` or `scripts/cursor_agent.sh`. See [docs/CURSOR_AGENT.md](docs/CURSOR_AGENT.md).

## Building it out

[docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) lays out the path from this prototype to a pilot-ready system, step by step: package layout, a detector interface, walk-forward evaluation, supply cuts, storage, a scoring job, an incident workflow, an API, deployment and the pilot runbook.

## How results are measured

Every detector is compared with the same code (`src/pipeline.py`): the simple flow rule, a flow + pressure rule, night flow (MNF), CUSUM and Isolation Forest. Training never uses the leak labels. Results are scored **per leak event** (events caught, real vs false alarm episodes, false alarms per zone-week, time to detect) with exact 95% confidence intervals and a random-alarm baseline. See [data/AquaWatch_Data_Notes.md](data/AquaWatch_Data_Notes.md) for the current table and [reports/AquaWatch industry readiness.md](reports/AquaWatch%20industry%20readiness.md) for the roadmap.

## Project structure

```text
AquaWatch/
  app.py                      # Streamlit UI (Jason / Romaro)
  config.py                   # Shared settings (paths, cutoff, model params)
  requirements.txt
  README.md
  TEAM_WORK_SPLIT.md          # Detailed task ownership
  data/
    AquaWatch_Synthetic_Sensor_Data.csv
    AquaWatch_Data_Notes.md
    raw/  demo/               # Guide §14.2 layout stubs
  models/                     # Saved Isolation Forest + profile
  src/
    schema.py                 # Data contract (pandera), checked on every load
    data_loader.py            # Nicholas
    baseline.py               # Nicholas
    model.py                  # Nickel
    alerts.py                 # Nickel (+ Jason consumes)
    metrics.py                # Nicholas
  tests/
    test_pipeline.py
    MAHATMA_TEST_CHECKLIST.md
  scripts/
    AquaWatch_Evaluate.py
    train_and_save_model.py
  docs/
    GUIDE_GAP_CHECKLIST.md
    research_log.md
    CONTRIBUTION_LOG.md
    STAGE0_SCOPE.md
    ARCHITECTURE.md
    BLOCKERS.md
    AquaWatch_Research_and_Sources.md
    pitch/
```

## Phase plan

1. **Stage 0 / Phase 1 (now):** CSV → detect → Streamlit demo → prove metrics  
2. **Stage 1:** Alert UX polish + inject demo (still synthetic)  
3. **Phase 2 (later only):** DB, login, hosting, field feedback — only if Stage 0/1 work

See [TEAM_WORK_SPLIT.md](TEAM_WORK_SPLIT.md) for the full person-by-person plan.

## Team

| Person | Role |
|---|---|
| Nathanael Coote | Team Lead |
| Nickel Small | Data & Model (primary) |
| Nicholas Smalling | Data & Model (support) |
| Jason Williams | Interface (primary) |
| Romaro Dixion | Interface (support) |
| Mahatma Williams | Tester & Presenter |

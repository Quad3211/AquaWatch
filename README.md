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

Optional checks:

```bash
python -m pytest tests/test_pipeline.py -v
```

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

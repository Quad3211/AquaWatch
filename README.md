# AquaWatch Jamaica — Group 13

Phase 1 **test product** for the Smart Caribbean Utilities pitch: load zone flow/pressure readings, compare a simple rule to Isolation Forest, and show explainable investigation alerts.

**GitHub:** https://github.com/Quad3211/AquaWatch  
**Clone:** `git clone git@github.com:Quad3211/AquaWatch.git`

> Synthetic demonstration data only. Not endorsed by NWC, Miya Jamaica, or any named organisation. An alert means **investigate this pattern**, not **a leak is confirmed**.

## Stage 0 status (Team Lead)

- [x] Phase 1 scope locked — see [docs/STAGE0_SCOPE.md](docs/STAGE0_SCOPE.md)
- [x] Architecture documented — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [x] Work split assigned — see [TEAM_WORK_SPLIT.md](TEAM_WORK_SPLIT.md)
- [x] Blocker log started — see [docs/BLOCKERS.md](docs/BLOCKERS.md)
- [x] Install / evaluate / Streamlit path verified
- [x] Repository connected to GitHub

## Quick start

```bash
git clone git@github.com:Quad3211/AquaWatch.git
cd AquaWatch
pip install -r requirements.txt
python scripts/AquaWatch_Evaluate.py
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
  requirements.txt
  README.md
  TEAM_WORK_SPLIT.md          # Detailed task ownership
  data/
    AquaWatch_Synthetic_Sensor_Data.csv
    AquaWatch_Data_Notes.md
  src/
    data_loader.py            # Nicholas
    baseline.py               # Nicholas
    model.py                  # Nickel
    alerts.py                 # Nickel (+ Jason consumes)
    metrics.py                # Nicholas
  tests/
    test_pipeline.py          # Automated smoke tests
    MAHATMA_TEST_CHECKLIST.md # Manual demo checks (Mahatma)
  scripts/
    AquaWatch_Evaluate.py     # CLI metrics reproduction
  docs/
    STAGE0_SCOPE.md           # Team Lead scope lock
    ARCHITECTURE.md           # Team Lead architecture
    BLOCKERS.md               # Team Lead daily tracker
    AquaWatch_Research_and_Sources.md
    pitch/
      AquaWatch_Jamaica_Group13_Pitch.pptx
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

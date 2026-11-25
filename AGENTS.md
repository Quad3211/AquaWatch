# AquaWatch: instructions for AI coding agents

These instructions apply to any AI agent working in this repo (Cursor, Claude Code, Copilot and others). Stay inside the scope below. If a task needs something outside it, **stop and ask the person** instead of doing it.

## What this project is
AquaWatch Jamaica is a university group project. It is a research prototype that flags unusual zone-level water flow and pressure patterns for a human to investigate. It uses **simulated data only**. It is not a confirmed leak detector, and it is not connected to any real utility system.

## Scope: what you may work on
- Detection and evaluation code: `src/` (data loading, schema, deviation profile, baselines, Isolation Forest, metrics, alerts, simulator)
- The Streamlit app: `app.py`
- Tests: `tests/`
- Scripts: `scripts/`
- Settings: `configs/default.toml` (thresholds, cutoffs) and `src/aquawatch/config.py` (paths), but only with a stated reason, because thresholds are fixed in advance on purpose
- Docs: `README.md`, `docs/`, `data/**/DATASHEET.md`, `data/AquaWatch_Data_Notes.md`

## Out of scope: ask first
- Anything that touches a real utility system, SCADA, network devices or credentials. **Never** add code that writes to, controls or connects to operational systems. AquaWatch is read-only analytics.
- Adding, removing or upgrading dependencies (`pyproject.toml`, `requirements.txt`, `uv.lock`)
- Changing CI (`.github/`), branch settings, or git history (no force-push, rebase of shared branches, or `reset --hard`)
- Downloading datasets or files from the internet (the one approved download is `scripts/fetch_battledim.py`, into gitignored `data/external/`)
- Deleting files, or editing generated data in `data/simulated/` by hand (regenerate it with `scripts/simulate_network.py`)
- New features or tools that the task did not ask for (no new frameworks, databases, cloud services or APIs)
- `research_notes/`, `reports/`, `docs/pitch/`: read them for context only, and do not edit them

## Hard rules (results must stay honest)
1. **Never use leak labels for training.** `simulated_leak_label` and `simulated_event_id` may only be used to score results. `tests/test_pipeline.py::test_training_never_reads_labels` must keep passing.
2. **Never tune thresholds on the test window.** Defaults live in `configs/default.toml` (check them with `aquawatch config`). Any tuning must use a separate validation window, and you must say so.
3. **Report results per leak event**, using `src/aquawatch/metrics.py`: events caught, real vs false alarms, false alarms per zone-week, and time to detect, with 95% CIs and the random baseline. Do not quote point-wise precision or recall on its own.
4. **Never overstate claims.** An alert means "investigate this pattern", not "leak confirmed". Keep the simulated-data banner and wording in the app. Do not claim real-world accuracy, water savings or NWC endorsement.
5. **Never commit model files** (`models/` is gitignored; pickle/joblib can run code when loaded). Save models with skops via `src/aquawatch/model.py`.
6. **No personal or customer data, and no secrets.** The project uses zone-level aggregates only. Never read, print or commit `.env` or any API key.
7. **Do not weaken tests to make them pass.** If a quality-gate test fails, report it and explain why.

## Commands
Install once with `uv sync` (or `pip install -r requirements.txt`, which installs the package in editable mode). Then:
```bash
python -m pytest -q                                   # all tests (includes the golden-results and app smoke tests)
python -m ruff check .                                # lint (must pass)
python -m mypy                                        # type check src/aquawatch (must pass)
python -m pytest -q --cov                             # tests + coverage (CI fails below 80%)
aquawatch evaluate --dataset simulated                # compare every detector on the 120-day simulation
aquawatch evaluate --dataset simulated --protocol walk-forward  # repeated folds, thresholds tuned to an alarm budget
aquawatch evaluate --dataset battledim --profile rolling   # needs `aquawatch battledim fetch` + `prepare`
aquawatch sizing analyse                              # DMA sizing study (docs/DMA_SIZING.md)
aquawatch train                                       # recreate models/ locally
python -m streamlit run app.py                        # run the app
```
`scripts/*.py` are thin wrappers around the same commands.

WNTR (the simulator) has no Python 3.14 build. To regenerate simulated data, run:
`uv run --no-project --python 3.12 --with wntr==1.5.0 --with six --with-editable . aquawatch simulate`

If a change is *meant* to move results, update the snapshot with
`python -m pytest tests/test_golden_results.py --update-golden` and explain why in the PR.

## Where things are
| File | Purpose |
|---|---|
| `src/aquawatch/data_loader.py`, `src/aquawatch/schema.py` | Load CSVs and validate them against a pandera schema |
| `src/aquawatch/model.py` | Expected-flow profile (zone × weekday/weekend × hour), label-free training filter, Isolation Forest, skops save/load |
| `src/aquawatch/baseline.py` | Flow rule, flow + pressure rule, night flow (MNF), CUSUM (score functions) |
| `src/aquawatch/detectors.py` | The `Detector` interface (`fit` / `score` / `alarms`) and the `REGISTRY` every part reads |
| `src/aquawatch/domain.py` | Shared types: `LeakEvent`, `Alarm`, `Incident`, `RunInfo` |
| `src/aquawatch/settings.py`, `configs/default.toml` | Typed, validated settings and their fingerprint |
| `src/aquawatch/pipeline.py` | One scoring path for every detector |
| `src/aquawatch/sensor_health.py` | Flags suspect readings (flat-lined, zero, no baseline): never used for training; no leak alarms on dead (zero/no-baseline) ones |
| `src/aquawatch/metrics.py` | Event-level scoring, confidence intervals, random baseline |
| `src/aquawatch/alerts.py` | Incident table shown in the app |
| `src/aquawatch/simulate.py` | WNTR network and leak simulator |

## Definition of done
- `python -m ruff check .`, `python -m mypy` and `python -m pytest -q --cov` pass (coverage at least 80%).
- If detection or evaluation changed, re-run `scripts/AquaWatch_Evaluate.py --dataset simulated` and update the numbers in `data/simulated/DATASHEET.md` and `data/AquaWatch_Data_Notes.md`.
- Your final message says what changed, what you ran, and anything you did not verify.
- Do not commit or push unless the person asks you to.

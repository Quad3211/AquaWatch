"""File locations and fixed product wording for AquaWatch.

Owner: Nicholas Smalling (paths/cutoff) / Nickel Small (model hyperparameters)
Team Lead keeps scope comments aligned with docs/STAGE0_SCOPE.md.
"""

from __future__ import annotations

from pathlib import Path

# Paths
# src/aquawatch/config.py -> the repository root (data/, models/ and docs/ live there).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_DEMO_DIR = DATA_DIR / "demo"
MODELS_DIR = PROJECT_ROOT / "models"
DOCS_DIR = PROJECT_ROOT / "docs"

# Demo dataset (Phase 1 uses the cleaned synthetic CSV in data/)
DEMO_CSV = DATA_DIR / "AquaWatch_Synthetic_Sensor_Data.csv"
LEGACY_DEMO_CSV = DEMO_CSV  # alias while data/demo/ is introduced

# WNTR-simulated dataset (scripts/simulate_network.py, see data/simulated/DATASHEET.md)
SIM_DIR = DATA_DIR / "simulated"
SIM_CSV = SIM_DIR / "aquawatch_wntr_readings.csv"
SIM_EVENTS_CSV = SIM_DIR / "aquawatch_wntr_events.csv"

# BattLeDIM 2020 benchmark (scripts/fetch_battledim.py + prepare_battledim.py).
# Downloaded and derived files stay in data/external/ (gitignored).
BATTLEDIM_DIR = DATA_DIR / "external" / "battledim"
BATTLEDIM_CSV = BATTLEDIM_DIR / "aquawatch_battledim_hourly.csv"
BATTLEDIM_EVENTS_CSV = BATTLEDIM_DIR / "aquawatch_battledim_events.csv"

# Detector thresholds, dataset cutoffs and app behaviour are *settings*, not
# constants: see configs/default.toml and src/aquawatch/settings.py.

MODEL_PATH = MODELS_DIR / "isolation_forest.skops"  # generated, not committed
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"
PROFILE_PATH = MODELS_DIR / "zone_hour_profile.csv"

# UI honesty banner (guide §14.3 / §15)
SIMULATED_DATA_BANNER = "Research Prototype: Simulated Utility Data"

# Product claim (do not change without Team Lead + trainer)
PRODUCT_CLAIM = "AquaWatch flags unusual patterns for investigation."

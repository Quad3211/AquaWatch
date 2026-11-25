"""Central settings for AquaWatch Stage 0 / Phase 1.

Owner: Nicholas Smalling (paths/cutoff) / Nickel Small (model hyperparameters)
Team Lead keeps scope comments aligned with docs/STAGE0_SCOPE.md.
"""
from __future__ import annotations

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
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
SIM_TRAIN_CUTOFF = "2026-07-31"  # 60 days to learn from, 60 days held out

# BattLeDIM 2020 benchmark (scripts/fetch_battledim.py + prepare_battledim.py).
# Downloaded and derived files stay in data/external/ (gitignored).
BATTLEDIM_DIR = DATA_DIR / "external" / "battledim"
BATTLEDIM_CSV = BATTLEDIM_DIR / "aquawatch_battledim_hourly.csv"
BATTLEDIM_EVENTS_CSV = BATTLEDIM_DIR / "aquawatch_battledim_events.csv"
BATTLEDIM_TRAIN_CUTOFF = "2019-01-01"  # train on 2018, test on 2019, as in the competition
# Leaks there often run for months, so an alarm only "detects" a leak within
# this many hours of its start; later alarms on it are repeats.
BATTLEDIM_DETECT_WITHIN_HOURS = 168

# Chronological split: train before this timestamp, hold out from this day onward
TRAIN_CUTOFF = "2026-11-11"

# Expected-flow profile: "hour" (zone x hour of day), "day_type" (zone x
# weekday/weekend x hour) or "hour_of_week" (zone x day of week x hour).
PROFILE_BY = "day_type"

# Window for the opt-in "rolling" profile (src.model.add_rolling_deviations).
ROLLING_PROFILE_DAYS = 28

# Baseline
FLOW_RULE_THRESHOLD = 0.25

# Baselines in src/baseline.py. Set in advance from standard practice, NOT tuned
# on the test window (threshold tuning belongs on a validation window).
FP_RULE_FLOW_Z = 2.5        # flow-and-pressure rule: flow this many robust SDs high...
FP_RULE_PRESSURE_Z = 1.0    # ...and pressure this many robust SDs low, together
MNF_NIGHT_HOURS = (2, 3, 4)  # minimum night flow window (local time)
MNF_LOOKBACK_NIGHTS = 14     # baseline = median of previous nights
MNF_K_MAD = 3.0              # flag nights this many robust SDs above the baseline...
MNF_MIN_RISE = 0.05          # ...and at least this much higher (fraction)
CUSUM_K = 0.5                # CUSUM allowance (robust SDs per hour)
CUSUM_H = 8.0                # CUSUM alarm level (robust SDs)

# Isolation Forest (freeze these before board review unless metrics break)
IFOREST_N_ESTIMATORS = 300
IFOREST_CONTAMINATION = 0.01
IFOREST_RANDOM_STATE = 17
# Training rows with a robust z-score above this on flow or pressure deviation
# are treated as already-abnormal and left out of training (no labels used).
ROBUST_Z_CUTOFF = 3.5
MODEL_PATH = MODELS_DIR / "isolation_forest.skops"  # generated, not committed
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"
PROFILE_PATH = MODELS_DIR / "zone_hour_profile.csv"

# App: alarms in the same zone less than this many hours apart are shown as one
# incident in the Alerts tab (metrics still count raw 1-hour-gap episodes).
INCIDENT_MERGE_HOURS = 12
DEFAULT_APP_DETECTOR = "Flow + pressure rule"

# UI honesty banner (guide §14.3 / §15)
SIMULATED_DATA_BANNER = "Research Prototype: Simulated Utility Data"

# Product claim (do not change without Team Lead + trainer)
PRODUCT_CLAIM = "AquaWatch flags unusual patterns for investigation."

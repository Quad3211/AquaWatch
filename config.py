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

# Chronological split: train before this timestamp, hold out from this day onward
TRAIN_CUTOFF = "2026-11-11"

# Baseline
FLOW_RULE_THRESHOLD = 0.25

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

# UI honesty banner (guide §14.3 / §15)
SIMULATED_DATA_BANNER = "Research Prototype: Simulated Utility Data"

# Product claim (do not change without Team Lead + trainer)
PRODUCT_CLAIM = "AquaWatch flags unusual patterns for investigation."

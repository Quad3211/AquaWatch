"""Train Isolation Forest once and save artifacts for demos.

Owner: Nickel Small

Run from project root:
    python scripts/train_and_save_model.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import chronological_split, load_sensor_csv
from src.model import (
    add_deviations,
    build_zone_hour_profile,
    save_model_artifacts,
    train_isolation_forest,
)


def main() -> None:
    df = load_sensor_csv()
    train, _test = chronological_split(df)
    normal_train = train[train["simulated_leak_label"] == 0].copy()
    profile = build_zone_hour_profile(normal_train)
    train_features = add_deviations(normal_train, profile)
    model = train_isolation_forest(train_features)
    model_path, profile_path = save_model_artifacts(model, profile)
    print(f"Saved model:   {model_path}")
    print(f"Saved profile: {profile_path}")


if __name__ == "__main__":
    main()

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
from src.model import fit_detector, save_model_artifacts


def main() -> None:
    df = load_sensor_csv()
    train, _test = chronological_split(df)
    model, profile = fit_detector(train)
    model_path, profile_path, metadata_path = save_model_artifacts(model, profile, train=train)
    print(f"Saved model:    {model_path}")
    print(f"Saved profile:  {profile_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()

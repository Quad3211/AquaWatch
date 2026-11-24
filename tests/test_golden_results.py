"""Golden results: evaluation numbers must not change by accident.

Refactors must leave every detector's event-level counts identical. If a change
is *meant* to move results (a new feature, a new threshold), re-run with
``pytest tests/test_golden_results.py --update-golden`` and explain why in the PR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from src.data_loader import chronological_split, load_sensor_csv
from src.metrics import compare_methods
from src.pipeline import score_all_methods

GOLDEN = Path(__file__).parent / "golden" / "event_results.json"
FIELDS = ["events_total", "events_detected", "alarm_episodes", "false_episodes", "repeat_episodes"]
DATASETS = {
    "demo": (config.DEMO_CSV, config.TRAIN_CUTOFF),
    "simulated": (config.SIM_CSV, config.SIM_TRAIN_CUTOFF),
}


def current_results() -> dict:
    out = {}
    for name, (path, cutoff) in DATASETS.items():
        train, test = chronological_split(load_sensor_csv(path), cutoff)
        table = compare_methods(score_all_methods(train, test)).set_index("method")
        out[name] = {
            method: {field: int(table.loc[method, field]) for field in FIELDS} for method in table.index
        }
    return out


def test_event_results_match_golden(request):
    results = current_results()
    if request.config.getoption("--update-golden"):
        GOLDEN.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        pytest.skip(f"Golden results rewritten: {GOLDEN}")
    expected = json.loads(GOLDEN.read_text())
    differences = [
        f"{dataset} / {method} / {field}: expected {expected[dataset][method][field]}, "
        f"got {results[dataset][method][field]}"
        for dataset in expected
        for method in expected[dataset]
        for field in FIELDS
        if results.get(dataset, {}).get(method, {}).get(field) != expected[dataset][method][field]
    ]
    assert not differences, "Results changed:\n" + "\n".join(differences)

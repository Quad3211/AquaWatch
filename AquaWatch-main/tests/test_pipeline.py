"""Smoke tests for the Phase 1 detection pipeline.

Owner: Nicholas Smalling
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.alerts import build_alert_table
from src.baseline import predict_rule
from src.data_loader import chronological_split, load_sensor_csv
from src.metrics import compare_rule_and_ai
from src.model import run_detection


def test_load_and_split():
    df = load_sensor_csv()
    assert len(df) == 1680
    train, test = chronological_split(df)
    assert len(train) == 1200
    assert len(test) == 480


def test_rule_vs_ai_pitch_metrics():
    df = load_sensor_csv()
    train, test = chronological_split(df)
    scored, _ = run_detection(train, test)
    scored = scored.copy()
    scored["rule_pred"] = predict_rule(scored)
    table = compare_rule_and_ai(scored).set_index("method")

    rule = table.loc["Simple flow rule"]
    ai = table.loc["Isolation Forest"]
    assert round(rule["precision"], 3) == 0.917
    assert round(rule["recall"], 3) == 0.379
    assert round(ai["precision"], 3) == 0.917
    assert round(ai["recall"], 3) == 0.759


def test_alerts_not_empty_on_held_out():
    df = load_sensor_csv()
    train, test = chronological_split(df)
    scored, _ = run_detection(train, test)
    alerts = build_alert_table(scored)
    assert not alerts.empty
    assert "reason" in alerts.columns
    assert "next_step" in alerts.columns

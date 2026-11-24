"""Tests for the `aquawatch` command line (src/aquawatch/cli.py, report.py, sizing.py)."""

from __future__ import annotations

import json

import pytest

from aquawatch import config, report
from aquawatch.cli import build_parser, main


def test_help_lists_every_command(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    for command in ("evaluate", "train", "simulate", "sizing", "battledim", "config"):
        assert command in out


def test_evaluate_prints_run_info_and_every_detector(capsys):
    assert main(["evaluate", "--dataset", "demo"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Run ")
    assert "Settings fingerprint:" in out
    for method in ("Simple flow rule", "CUSUM on flow", "Isolation Forest", "Random alarms"):
        assert method in out


def test_evaluate_simulated_prints_leak_size_table(capsys):
    assert main(["evaluate", "--dataset", "simulated", "--profile", "hour"]) == 0
    out = capsys.readouterr().out
    assert "expected-flow profile: hour" in out
    assert "Leak events caught, by leak size" in out


def test_evaluate_missing_dataset_explains_how_to_get_it(monkeypatch, tmp_path):
    missing = (tmp_path / "nope.csv", tmp_path / "nope_events.csv", True)
    monkeypatch.setitem(report.DATASETS, "battledim", missing)
    with pytest.raises(SystemExit, match="aquawatch battledim fetch"):
        main(["evaluate", "--dataset", "battledim"])


def test_config_shows_settings_and_fingerprint(capsys):
    assert main(["config"]) == 0
    out = capsys.readouterr().out
    body, fingerprint_line = out.rsplit("fingerprint:", 1)
    assert json.loads(body)["cusum"]["h"] == 8.0
    assert len(fingerprint_line.strip()) == 12


def test_train_saves_model_metadata(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(config, "MODEL_PATH", tmp_path / "m.skops")
    monkeypatch.setattr(config, "PROFILE_PATH", tmp_path / "p.csv")
    monkeypatch.setattr(config, "MODEL_METADATA_PATH", tmp_path / "meta.json")
    assert main(["train"]) == 0
    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["settings_fingerprint"] and meta["sklearn_version"]
    assert "Saved model" in capsys.readouterr().out


def test_sizing_analyse_without_simulations_explains_next_step(monkeypatch, tmp_path):
    from aquawatch import sizing

    monkeypatch.setattr(sizing, "RAW_DIR", tmp_path)
    with pytest.raises(SystemExit, match="simulate"):
        main(["sizing", "analyse"])


def test_unknown_dataset_is_rejected():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["evaluate", "--dataset", "nowhere"])


def test_sizing_analyse_end_to_end_on_small_input(monkeypatch, tmp_path, capsys):
    """Run the analysis step on the committed simulation, relabelled as sizing zones."""
    import pandas as pd

    from aquawatch import sizing

    readings = pd.read_csv(config.SIM_CSV)
    events = pd.read_csv(config.SIM_EVENTS_CSV)
    zones = sorted(readings["zone"].unique())
    names = {z: sizing.zone_name(s) for z, s in zip(zones, sizing.ZONE_SIZES_M3H, strict=True)}
    readings["zone"] = readings["zone"].map(names)
    events["zone"] = events["zone"].map(names)
    raw = tmp_path / "raw"
    raw.mkdir()
    readings.to_csv(raw / "readings_seed1.csv", index=False)
    events.to_csv(raw / "events_seed1.csv", index=False)
    monkeypatch.setattr(sizing, "RAW_DIR", raw)
    monkeypatch.setattr(sizing, "OUT_DIR", tmp_path)
    monkeypatch.setattr(sizing, "RESULTS_CSV", tmp_path / "results.csv")
    monkeypatch.setattr(sizing, "SEEDS", (1,))

    assert main(["sizing", "analyse"]) == 0
    results = pd.read_csv(tmp_path / "results.csv")
    assert set(results["zone_m3h"]) == set(sizing.ZONE_SIZES_M3H)
    assert (results["caught_24h"] <= results["leaks"]).all()
    assert "share of zone inflow" in capsys.readouterr().out

"""Tests for typed settings (configs/default.toml + environment overrides)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aquawatch.settings import DEFAULT_CONFIG, SettingsError, load_settings


def test_defaults_load_and_match_documented_values():
    s = load_settings(environ={})
    assert s.profile.by == "day_type"
    assert s.rules.flow_threshold == 0.25
    assert s.night_flow.hours == (2, 3, 4)
    assert s.dataset("simulated").cutoff == "2026-07-31"
    assert s.dataset("battledim").detect_within_hours == 168
    assert s.dataset("demo").detect_within_hours is None


def test_environment_overrides_and_fingerprint():
    base = load_settings(environ={})
    tuned = load_settings(environ={"AQUAWATCH__CUSUM__H": "10", "AQUAWATCH__NIGHT_FLOW__HOURS": "[1, 2]"})
    assert tuned.cusum.h == 10
    assert tuned.night_flow.hours == (1, 2)
    assert tuned.fingerprint() != base.fingerprint()
    # App-only settings do not change results, so they do not change the fingerprint.
    app_only = load_settings(environ={"AQUAWATCH__APP__INCIDENT_MERGE_HOURS": "6"})
    assert app_only.fingerprint() == base.fingerprint()


@pytest.mark.parametrize(
    "environ, message",
    [
        ({"AQUAWATCH__CUSUM__TYPO": "1"}, "Unknown setting"),
        ({"AQUAWATCH__ISOLATION_FOREST__CONTAMINATION": "0.9"}, "contamination"),
        ({"AQUAWATCH__PROFILE__BY": "weekly"}, "profile.by"),
        ({"AQUAWATCH__DATASETS__DEMO__CUTOFF": "next tuesday"}, "YYYY-MM-DD"),
        ({"AQUAWATCH__NIGHT_FLOW__HOURS": "[25]"}, "hours"),
    ],
)
def test_invalid_settings_fail_loudly(environ, message):
    with pytest.raises(SettingsError, match=message):
        load_settings(environ=environ)


def test_alternative_config_file(tmp_path: Path):
    custom = tmp_path / "custom.toml"
    text = DEFAULT_CONFIG.read_text(encoding="utf-8").replace("h = 8.0", "h = 12.0")
    custom.write_text(text, encoding="utf-8")
    assert load_settings(environ={"AQUAWATCH_CONFIG": str(custom)}).cusum.h == 12.0

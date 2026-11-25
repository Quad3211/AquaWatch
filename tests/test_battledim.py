"""Tests for BattLeDIM conversion, overlapping-leak scoring and the rolling profile.

Owner: Nickel Small

The real BattLeDIM files are downloaded on demand (gitignored), so most tests
build tiny files in the same format instead. The last test runs on the real
data only if it has been downloaded and prepared.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from src.battledim import convert, read_leak_list
from src.metrics import alarm_episodes, compare_methods, event_scores, random_alarms
from src.model import add_rolling_deviations

CONFIG_YAML = """leakages:
- # linkID, startTime, endTime, leakDiameter (m), leakType, peakTime
- p10, 2018-01-02 00:00, 2019-12-31 23:55, 0.01, incipient, 2018-01-03 00:00
- p20,  2019-01-01 06:00, 2019-01-01 18:00, 0.02, abrupt, 2019-01-01 06:00
pressure_sensors:
- n1
"""


def _write_scada(path: Path, columns: dict[str, np.ndarray], index: pd.DatetimeIndex) -> None:
    frame = pd.DataFrame(columns, index=index)
    frame.index.name = "Timestamp"
    frame.to_csv(path, sep=";", decimal=",")


@pytest.fixture()
def tiny_battledim(tmp_path: Path) -> Path:
    """Two days (one per year) of 5-minute BattLeDIM-format files."""
    for year in (2018, 2019):
        idx = pd.date_range(f"{year}-01-01", periods=24 * 12, freq="5min")
        n = len(idx)
        flows = {"p227": np.full(n, 70.5), "p235": np.full(n, 30.0), "PUMP_1": np.full(n, 99.0)}
        pressures = {"n1": np.full(n, 40.0), "n4": np.full(n, 50.0), "n31": np.full(n, 60.0)}
        _write_scada(tmp_path / f"{year}_SCADA_Flows.csv", flows, idx)
        _write_scada(tmp_path / f"{year}_SCADA_Pressures.csv", pressures, idx)
        leak = {"p10": np.full(n, 2.0 if year == 2019 else 0.0)}
        _write_scada(tmp_path / f"{year}_Leakages.csv", leak, idx)
    (tmp_path / "dataset_configuration.yaml").write_text(CONFIG_YAML)
    return tmp_path


def test_leak_list_is_parsed(tiny_battledim):
    leaks = read_leak_list(tiny_battledim / "dataset_configuration.yaml")
    assert list(leaks["event_id"]) == ["BDIM-p10", "BDIM-p20"]
    assert leaks.loc[1, "kind"] == "abrupt"
    assert leaks.loc[1, "start"] == pd.Timestamp("2019-01-01 06:00")


def test_convert_sums_reservoir_inflows_only(tiny_battledim):
    readings, events = convert(tiny_battledim)
    assert len(readings) == 48  # two separate days, hourly
    assert (readings["zone"] == "L-Town").all()
    # p227 + p235 with decimal commas parsed; the internal pump flow is not added
    assert readings["flow_index"].iloc[0] == pytest.approx(100.5)
    assert readings["pressure_index"].iloc[0] == pytest.approx(50.0)  # median of the sensors
    assert readings["simulated_leak_label"].sum() == 24  # leak p10 releasing water on the 2019 day
    assert events.loc[events["event_id"] == "BDIM-p10", "peak_leak_m3h"].iloc[0] == pytest.approx(2.0)


def _frame(hours: int, start: str = "2019-01-01") -> pd.DataFrame:
    ts = pd.date_range(start, periods=hours, freq="h")
    return pd.DataFrame(
        {"zone": "L-Town", "timestamp": ts, "simulated_leak_label": 1, "simulated_event_id": "", "pred": 0}
    )


def test_overlapping_leaks_scored_by_alarm_start():
    """With leaks running all the time: an alarm during a leak that began before
    the test window is false, a new alarm must start within the window to count,
    and later alarms on a caught leak are repeats."""
    scored = _frame(24 * 10)
    events = pd.DataFrame(
        {
            "event_id": ["old", "new"],
            "zone": "L-Town",
            "start": pd.to_datetime(["2018-06-01 00:00", "2019-01-05 00:00"]),
            "end": pd.to_datetime(["2019-12-31 00:00", "2019-01-08 00:00"]),
        }
    )
    ts = scored["timestamp"]
    scored.loc[ts.between("2019-01-02 00:00", "2019-01-02 03:00"), "pred"] = 1  # during "old" only
    scored.loc[ts.between("2019-01-05 05:00", "2019-01-05 07:00"), "pred"] = 1  # 5 h after "new" starts
    scored.loc[ts.between("2019-01-06 10:00", "2019-01-06 11:00"), "pred"] = 1  # "new" again, later

    strict = event_scores(scored, "pred", events=events, detect_within_hours=2)
    assert strict["events_total"] == 1  # only leaks starting in the window are scored
    assert strict["events_detected"] == 0  # first alarm came after 5 h; window is 2 h

    lenient = event_scores(scored, "pred", events=events, detect_within_hours=24)
    assert lenient["events_detected"] == 1
    assert lenient["median_hours_to_detect"] == 5
    assert lenient["false_episodes"] == 1  # the alarm during the 2018 leak
    assert lenient["repeat_episodes"] == 1  # the later alarm on the caught leak


def test_random_baseline_matches_alarm_budget():
    scored = _frame(24 * 20)
    scored["zone"] = np.where(scored.index % 2, "A", "B")
    scored["ai_pred"] = 0
    scored.loc[[10, 12, 14, 100, 102, 300], "ai_pred"] = 1  # zone B: one 3-h run, one 2-h run, one 1-h
    budget = alarm_episodes(scored, "ai_pred")
    rand = random_alarms(scored, like_col="ai_pred")
    # Same episode lengths placed at random: never more flagged hours or episodes.
    assert 0 < rand.sum() <= budget["hours"].sum()
    assert len(alarm_episodes(scored.assign(r=rand), "r")) <= len(budget)


def test_rolling_profile_uses_only_the_past():
    ts = pd.date_range("2026-01-05", periods=24 * 60, freq="h")
    df = pd.DataFrame(
        {"zone": "A", "timestamp": ts, "hour": ts.hour, "flow_index": 100 + ts.hour.to_numpy() * 1.0,
         "pressure_index": 50.0}
    )
    history, frame = df[ts < "2026-02-20"], df[ts >= "2026-02-20"].copy()
    frame.loc[frame["timestamp"] >= "2026-03-01", "flow_index"] += 20  # a step change
    _, out = add_rolling_deviations(history, frame)
    before = out[out["timestamp"] < "2026-03-01"]
    first_day = out[(out["timestamp"] >= "2026-03-01") & (out["timestamp"] < "2026-03-02")]
    assert before["flow_rel_dev"].abs().max() == pytest.approx(0)
    assert (first_day["flow_rel_dev"] > 0.1).all()  # the new step is not in the baseline yet


@pytest.mark.skipif(not config.BATTLEDIM_CSV.exists(), reason="BattLeDIM not downloaded and prepared")
def test_real_battledim_runs_end_to_end():
    from src.data_loader import chronological_split, load_sensor_csv
    from src.pipeline import score_all_methods

    df = load_sensor_csv(config.BATTLEDIM_CSV)
    events = pd.read_csv(config.BATTLEDIM_EVENTS_CSV, parse_dates=["start", "end"])
    train, test = chronological_split(df, config.BATTLEDIM_TRAIN_CUTOFF)
    table = compare_methods(
        score_all_methods(train, test, profile_by="rolling"),
        events=events,
        detect_within_hours=config.BATTLEDIM_DETECT_WITHIN_HOURS,
    )
    assert (table["events_total"] == 19).all()

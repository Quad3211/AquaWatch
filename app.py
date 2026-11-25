"""AquaWatch Jamaica: Streamlit test product.

Owners: Jason Williams (layout) / Romaro Dixion (charts & demo controls)

Run:
    python -m streamlit run app.py
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from aquawatch import config
from aquawatch.alerts import build_alert_table, build_event_alerts
from aquawatch.data_loader import chronological_split, load_sensor_csv
from aquawatch.metrics import (
    METHODS,
    compare_methods,
    detection_by_leak_size,
    event_scores,
    format_comparison,
    true_events,
)
from aquawatch.model import add_deviations, load_model_artifacts, predict_isolation_forest
from aquawatch.pipeline import score_all_methods
from aquawatch.schema import find_gaps
from aquawatch.settings import get_settings

cfg = get_settings()

UPLOAD = "Upload a CSV"
DATASETS = {
    "Simulated network (WNTR, 120 days, 40 leaks)": {
        "path": config.SIM_CSV,
        "cutoff": cfg.dataset("simulated").cutoff,
        "events": config.SIM_EVENTS_CSV,
        "flow_unit": "m³/h",
        "pressure_unit": "m",
    },
    "Original demo CSV (14 days, 6 events)": {
        "path": config.DEMO_CSV,
        "cutoff": cfg.dataset("demo").cutoff,
        "events": None,
        "flow_unit": "units/h",
        "pressure_unit": "units",
    },
}
DETECTOR_HELP = {
    "Simple flow rule": "Flow more than 25% above expected. Very few false alarms, misses small leaks.",
    "Flow + pressure rule": "Flow clearly up and pressure down together. Best balance on the simulated data.",
    "Night flow (MNF)": "Compares 02:00-04:00 inflow with previous nights. The classic utility check; "
    "decides once per night.",
    "CUSUM on flow": "Builds up evidence hour by hour. Catches the smallest leaks; alarms run on "
    "after a repair.",
    "Isolation Forest": "Machine-learning anomaly detector on flow and pressure deviation.",
}

st.set_page_config(page_title="AquaWatch Jamaica", page_icon="💧", layout="wide")
st.warning(config.SIMULATED_DATA_BANNER)
st.title("AquaWatch Jamaica")
st.caption(
    f"{config.PRODUCT_CLAIM} Research prototype on simulated data. "
    "An alert means *investigate this zone*, not *a leak is confirmed*."
)


@st.cache_data(show_spinner=False)
def _load_path(path: str) -> pd.DataFrame:
    return load_sensor_csv(path)


@st.cache_data(show_spinner=False)
def _load_upload(data: bytes) -> pd.DataFrame:
    # Cached on the file's bytes, so a different upload always reloads.
    return load_sensor_csv(BytesIO(data))


@st.cache_data(show_spinner="Training on the history and scoring every detector...")
def _score(df: pd.DataFrame, cutoff: str) -> tuple[pd.DataFrame, int]:
    train, test = chronological_split(df, cutoff)
    return score_all_methods(train, test), len(train)


def _midpoint(df: pd.DataFrame) -> str:
    start, end = df["timestamp"].min(), df["timestamp"].max()
    return str((start + (end - start) / 2).normalize().date())


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Data")
    choice = st.radio("Dataset", [*DATASETS, UPLOAD], index=0)
    uploaded = st.file_uploader("CSV file", type=["csv"]) if choice == UPLOAD else None

    st.header("Detector")
    names = list(METHODS)
    detector = st.selectbox(
        "Raise alerts with",
        names,
        index=names.index(cfg.app.default_detector),
        help="All detectors are scored in the Metrics tab; this one drives Overview, Alerts and Chart.",
    )
    st.caption(DETECTOR_HELP[detector])
    prefer_saved = False
    saved_model_ready = config.MODEL_PATH.exists() and config.PROFILE_PATH.exists()
    if choice != UPLOAD and DATASETS[choice]["path"] == config.DEMO_CSV and detector == "Isolation Forest":
        prefer_saved = st.checkbox(
            "Use saved Isolation Forest (models/)",
            value=saved_model_ready,
            disabled=not saved_model_ready,
            help="The demo should not need to retrain live. Run `aquawatch train` first "
            "(it writes the model and its profile to models/).",
        )
    st.markdown("---")
    st.caption("Labels are used only to score results, never to train.")

# ---------------------------------------------------------------- load + score
try:
    if choice == UPLOAD:
        if uploaded is None:
            st.info("Upload a CSV with the AquaWatch columns to begin (see data/AquaWatch_Data_Notes.md).")
            st.stop()
        df = _load_upload(uploaded.getvalue())
        settings = {"events": None, "flow_unit": "units/h", "pressure_unit": "units"}
        cutoff = str(
            st.sidebar.date_input(
                "Train on data before",
                value=pd.Timestamp(_midpoint(df)),
                min_value=df["timestamp"].min(),
                max_value=df["timestamp"].max(),
            )
        )
    else:
        settings = DATASETS[choice]
        df = _load_path(str(settings["path"]))
        cutoff = settings["cutoff"]

    gaps = find_gaps(df)
    if not gaps.empty:
        st.sidebar.warning(
            f"{int(gaps['missing_readings'].sum())} hourly readings are missing across "
            f"{len(gaps)} zone(s); results near gaps are less reliable."
        )

    scored, train_rows = _score(df, cutoff)
    scored = scored.copy()
    suspect = int(scored["sensor_suspect"].sum())
    if suspect:
        st.sidebar.warning(
            f"{suspect:,} readings look like a sensor fault (flat-lined or no usable baseline). "
            "No leak alarms are raised on them; check those meters."
        )
    if prefer_saved and config.MODEL_PATH.exists() and config.PROFILE_PATH.exists():
        model, profile = load_model_artifacts()
        derived = [
            "expected_flow", "expected_pressure", "flow_rel_dev", "pressure_dev", "day_of_week", "day_type",
        ]
        raw = scored.drop(columns=[c for c in derived if c in scored.columns])
        saved_alarms = predict_isolation_forest(model, add_deviations(raw, profile)).to_numpy()
        # Same rule as the pipeline: no leak alarms on readings that look like sensor faults.
        scored["ai_pred"] = pd.Series(saved_alarms, index=scored.index).where(~scored["sensor_suspect"], 0)
        st.sidebar.success("Using saved Isolation Forest artifacts")
except (ValueError, KeyError, FileNotFoundError, pd.errors.ParserError) as exc:
    st.error(f"Could not run AquaWatch on this data: {exc}")
    st.stop()

pred_col = METHODS[detector]
flow_unit, pressure_unit = settings["flow_unit"], settings["pressure_unit"]
volume_unit = flow_unit.split("/")[0]
has_labels = scored["simulated_leak_label"].sum() > 0
incidents = build_event_alerts(
    scored,
    prediction_col=pred_col,
    flow_unit=flow_unit,
    pressure_unit=pressure_unit,
    max_gap_hours=cfg.app.incident_merge_hours,
)
stats = event_scores(scored, pred_col)
test_start, test_end = scored["timestamp"].min(), scored["timestamp"].max()
test_days = (test_end - test_start).days + 1

tab_overview, tab_alerts, tab_chart, tab_metrics, tab_insights = st.tabs(
    ["Overview", "Alerts", "Chart", "Metrics", "Insights: DMA size"]
)

# ---------------------------------------------------------------- overview
with tab_overview:
    st.subheader(f"Monitoring window: {test_start:%d %b} to {test_end:%d %b %Y} ({test_days} days)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Zones monitored", scored["zone"].nunique())
    c2.metric("Open incidents", len(incidents))
    c3.metric(
        f"Est. extra water flagged ({volume_unit})",
        f"{incidents[f'est_volume_lost_{volume_unit}'].sum():,.0f}" if len(incidents) else "0",
    )
    c4.metric("False alarms per zone-week", f"{stats['false_alarms_per_zone_week']:.1f}")
    if has_labels:
        st.markdown(
            f"**{detector}** caught **{stats['events_detected']} of {stats['events_total']}** injected "
            f"leaks in this window (median {stats['median_hours_to_detect']:.0f} h after the leak began). "
            f"{stats['alarm_episodes'] - stats['false_episodes']} of {stats['alarm_episodes']} raw "
            "alarms overlapped a real leak."
        )
    st.caption(
        f"Learned the normal pattern from {train_rows:,} readings before {cutoff}; "
        f"scored {len(scored):,} readings from then on. Expected flow is looked up by zone, "
        f"hour and {'weekday/weekend' if cfg.profile.by == 'day_type' else cfg.profile.by}. "
        f"Settings fingerprint {cfg.fingerprint()}."
    )
    if len(incidents):
        by_zone = (
            incidents.groupby("zone")
            .agg(incidents=("priority", "size"), volume=(f"est_volume_lost_{volume_unit}", "sum"))
            .reset_index()
            .sort_values("volume", ascending=False)
            .round({"volume": 0})
        )
        st.markdown("**Where to look first**")
        st.dataframe(
            by_zone.rename(columns={"volume": f"est. extra water ({volume_unit})"}),
            hide_index=True,
            width="stretch",
        )

# ---------------------------------------------------------------- alerts
with tab_alerts:
    st.subheader(f"Incidents to investigate ({detector})")
    st.caption(
        f"Alarms in the same zone less than {cfg.app.incident_merge_hours} h apart are merged into one "
        "incident and ranked by estimated extra water. Extra flow is measured against the zone's "
        "usual level for that hour and day type."
    )
    if incidents.empty:
        st.info("No incidents in this window.")
    else:
        zones_sel = st.multiselect("Zones", sorted(incidents["zone"].unique()))
        view = incidents if not zones_sel else incidents[incidents["zone"].isin(zones_sel)]
        if has_labels and st.checkbox("Hide alarms that matched no injected leak", value=False):
            view = view[view["matches_injected_leak"] != "no (false alarm)"]
        if not has_labels:
            view = view.drop(columns=["matches_injected_leak"])
        st.dataframe(
            view,
            hide_index=True,
            width="stretch",
            column_config={
                "start": st.column_config.DatetimeColumn(format="ddd D MMM, HH:mm"),
                "end": st.column_config.DatetimeColumn(format="ddd D MMM, HH:mm"),
                f"extra_flow_{flow_unit}": st.column_config.NumberColumn(
                    f"extra flow ({flow_unit})", format="%.1f"
                ),
                f"est_volume_lost_{volume_unit}": st.column_config.NumberColumn(
                    f"est. extra water ({volume_unit})", format="%.0f"
                ),
                "peak_flow_rise": st.column_config.NumberColumn("peak flow rise", format="percent"),
                f"pressure_change_{pressure_unit}": st.column_config.NumberColumn(
                    f"pressure change ({pressure_unit})", format="%.1f"
                ),
                "matches_injected_leak": "matches injected leak?",
            },
        )
        with st.expander("Hour-by-hour flagged readings"):
            hourly = build_alert_table(scored, prediction_col=pred_col, source=detector)
            hourly = hourly.drop(columns=["rank_score"], errors="ignore")
            st.dataframe(hourly, hide_index=True, width="stretch")

# ---------------------------------------------------------------- chart
with tab_chart:
    zones = sorted(scored["zone"].unique())
    busiest = incidents["zone"].value_counts().idxmax() if len(incidents) else zones[0]
    left, right = st.columns([1, 2])
    zone = left.selectbox("Zone", zones, index=zones.index(busiest))
    window = right.slider(
        "Dates",
        min_value=test_start.to_pydatetime(),
        max_value=test_end.to_pydatetime(),
        value=(test_start.to_pydatetime(), min(test_end, test_start + pd.Timedelta(days=14)).to_pydatetime()),
        format="DD MMM",
    )
    z = scored[(scored["zone"] == zone) & scored["timestamp"].between(*window)].sort_values("timestamp")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        subplot_titles=(f"Inflow ({flow_unit})", f"Pressure ({pressure_unit})"))
    fig.add_trace(go.Scatter(x=z["timestamp"], y=z["expected_flow"], name="expected flow",
                             line={"color": "#9aa5b1", "dash": "dot"}), row=1, col=1)
    fig.add_trace(go.Scatter(x=z["timestamp"], y=z["flow_index"], name="measured flow",
                             line={"color": "#1f6fb2"}), row=1, col=1)
    alarms = z[z[pred_col] == 1]
    fig.add_trace(go.Scatter(x=alarms["timestamp"], y=alarms["flow_index"], mode="markers",
                             name=f"alarm ({detector})", marker={"color": "#d1495b", "size": 7}),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=z["timestamp"], y=z["expected_pressure"], name="expected pressure",
                             line={"color": "#9aa5b1", "dash": "dot"}, showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=z["timestamp"], y=z["pressure_index"], name="measured pressure",
                             line={"color": "#2a9d8f"}), row=2, col=1)
    if has_labels:
        leaks = true_events(z)
        for ev in leaks.itertuples():
            fig.add_vrect(x0=ev.start, x1=ev.end + pd.Timedelta(hours=1), fillcolor="#f4a261",
                          opacity=0.18, line_width=0, row="all", col=1)
    fig.update_layout(height=560, margin={"l": 10, "r": 10, "t": 40, "b": 10},
                      legend={"orientation": "h", "y": -0.08})
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Dotted lines are the zone's usual level for that hour and day type. "
        + ("Orange bands are the injected leaks (simulation ground truth). " if has_labels else "")
        + "Red dots are hours the selected detector flagged."
    )

# ---------------------------------------------------------------- metrics
with tab_metrics:
    st.subheader("How every detector did on this window (simulated data only)")
    st.caption(
        "Scored per leak event. An alarm episode is a run of flagged hours in one zone. Ranges are exact "
        "95% confidence intervals. The random row raises as many alarms as Isolation Forest, just as "
        "long, at random times: the floor any detector must beat. Read leaks caught together with false "
        "alarms: long leaks make recall easy to game."
    )
    if has_labels:
        st.dataframe(format_comparison(compare_methods(scored)), hide_index=True, width="stretch")
        if settings["events"] is not None and settings["events"].exists():
            st.markdown("**Leaks caught, by size** (leak flow as % of the zone's average inflow)")
            events_table = pd.read_csv(settings["events"])
            st.dataframe(detection_by_leak_size(scored, METHODS, events_table), hide_index=True,
                         width="stretch")
    else:
        st.info("This data has no leak labels, so detectors cannot be scored. Alerts still work.")
    st.warning("Simulated test only; not validated on NWC sensor data.")

# ---------------------------------------------------------------- insights
with tab_insights:
    st.subheader("How small must a metered zone (DMA) be?")
    st.caption(
        "From scripts/dma_sizing_study.py: zones of 10-200 m³/h simulated side by side, each with leaks "
        "of 2, 5 and 10 m³/h, over 4 seeds, with the last 60 days held out. Demand noise follows "
        "customer count (assumed 600 L per customer per day). Independent of the dataset chosen in the "
        "sidebar."
    )
    sizing_csv = config.SIM_DIR / "sizing" / "dma_sizing_results.csv"
    share_csv = config.SIM_DIR / "sizing" / "dma_sizing_by_leak_share.csv"
    if not sizing_csv.exists():
        st.info("Run scripts/dma_sizing_study.py (simulate, then analyse) to create these results.")
    else:
        sizing = pd.read_csv(sizing_csv)
        st.markdown(
            "**Rule of thumb:** a leak is caught within a day almost every time once it is about "
            "**20% or more of the zone's average inflow**, and mostly missed below 10%. So to catch a "
            "leak of *L* m³/h quickly, keep zones to about **5 × L** m³/h. For a 5 m³/h leak that is "
            "about 25 m³/h, roughly 1,000 customers."
        )
        pick = st.selectbox("Detector", list(METHODS), index=list(METHODS).index(detector),
                            key="insights_detector")
        part = sizing[sizing["method"] == pick].assign(rate=lambda d: d["caught_24h"] / d["leaks"])
        grid = part.pivot(index="zone_m3h", columns="leak_m3h", values="rate").sort_index()
        counts = part.pivot(index="zone_m3h", columns="leak_m3h", values="leaks").sort_index()
        caught = part.pivot(index="zone_m3h", columns="leak_m3h", values="caught_24h").sort_index()
        text = caught.astype(int).astype(str) + "/" + counts.astype(int).astype(str)
        heat = go.Figure(
            go.Heatmap(
                z=grid.to_numpy(),
                x=[f"{c:g} m³/h leak" for c in grid.columns],
                y=[f"{r:g} m³/h zone" for r in grid.index],
                text=text.to_numpy(),
                texttemplate="%{text}",
                colorscale="Blues",
                zmin=0,
                zmax=1,
                colorbar={"title": "caught<br>within 24 h"},
            )
        )
        heat.update_layout(height=380, margin={"l": 10, "r": 10, "t": 10, "b": 10})
        st.plotly_chart(heat, width="stretch")
        fa = part.groupby("zone_m3h")["false_alarms_per_week"].first()
        st.caption(
            "Cells show leaks caught within 24 h out of leaks tested. False alarms per zone-week for "
            f"{pick}: " + ", ".join(f"{z:g} m³/h: {v:.2f}" for z, v in fa.items()) + "."
        )
        if share_csv.exists():
            st.markdown("**All detectors, by leak size as a share of zone inflow** (caught within 24 h)")
            st.dataframe(pd.read_csv(share_csv), hide_index=True, width="stretch")
        st.warning(
            "Simulated network, not calibrated to NWC. Small samples per cell (4-12 leaks). "
            "Use this to plan DMA sizes for a pilot, then confirm on real data."
        )

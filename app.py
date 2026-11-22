"""AquaWatch Phase 1 Streamlit test product.

Owners: Jason Williams (layout) / Romaro Dixion (charts & demo controls)

Run:
    python -m streamlit run app.py
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

import config
from src.alerts import build_alert_table
from src.baseline import predict_rule
from src.data_loader import DEFAULT_DATA, chronological_split, load_sensor_csv
from src.metrics import compare_methods, format_comparison
from src.model import (
    add_deviations,
    load_model_artifacts,
    predict_isolation_forest,
    run_detection,
)
from src.schema import find_gaps

st.set_page_config(page_title="AquaWatch Jamaica", page_icon="💧", layout="wide")

st.warning(config.SIMULATED_DATA_BANNER)
st.title("AquaWatch Jamaica")
st.caption(
    f"{config.PRODUCT_CLAIM} "
    "Phase 1 test product — synthetic data only. Not a confirmed leak detector."
)


@st.cache_data(show_spinner=False)
def _load_default(path: str) -> pd.DataFrame:
    return load_sensor_csv(path)


@st.cache_data(show_spinner=False)
def _load_upload(data: bytes) -> pd.DataFrame:
    # Cached on the file's bytes, so a different upload always reloads.
    return load_sensor_csv(BytesIO(data))


with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload a compatible CSV (optional)", type=["csv"])
    use_default = st.checkbox(
        "Use project synthetic CSV",
        value=True,
        disabled=uploaded is not None,
        help="An uploaded CSV takes priority over the project CSV.",
    )
    prefer_saved = st.checkbox(
        "Use saved model (models/)",
        value=config.MODEL_PATH.exists(),
        help="Guide §14.3: demo should not need to retrain live.",
    )
    st.markdown("---")
    st.markdown("**Team reminder:** labels are for evaluation only, not model features.")

try:
    if uploaded is not None:
        df = _load_upload(uploaded.getvalue())
        st.sidebar.success(f"Loaded uploaded CSV: {uploaded.name}")
    elif use_default and DEFAULT_DATA.exists():
        df = _load_default(str(DEFAULT_DATA))
        st.sidebar.success(f"Loaded {DEFAULT_DATA.name}")
    else:
        st.info("Load the synthetic CSV or upload one from the sidebar to begin.")
        st.stop()

    gaps = find_gaps(df)
    if not gaps.empty:
        st.sidebar.warning(
            f"{int(gaps['missing_readings'].sum())} hourly readings are missing across "
            f"{len(gaps)} zone(s); results near gaps are less reliable."
        )

    train, test = chronological_split(df)
    if prefer_saved and config.MODEL_PATH.exists() and config.PROFILE_PATH.exists():
        model, profile = load_model_artifacts()
        scored = add_deviations(test, profile)
        scored["ai_pred"] = predict_isolation_forest(model, scored)
        st.sidebar.success("Using saved Isolation Forest artifacts")
    else:
        scored, _model = run_detection(train, test)
        st.sidebar.info("Trained Isolation Forest in-session (run train_and_save_model.py for offline demo)")
    scored = scored.copy()
    scored["rule_pred"] = predict_rule(scored)
    alerts = build_alert_table(scored, prediction_col="ai_pred")
    metrics_table = format_comparison(compare_methods(scored))
except (ValueError, KeyError, FileNotFoundError, pd.errors.ParserError) as exc:
    st.error(f"Could not run AquaWatch on this data: {exc}")
    if prefer_saved and uploaded is not None:
        st.caption(
            "Tip: the saved model only knows the zones it was trained on. "
            "Untick 'Use saved model' to train on the uploaded data instead."
        )
    st.stop()

tab_overview, tab_alerts, tab_chart, tab_metrics = st.tabs(
    ["Overview", "Alerts", "Chart", "Metrics"]
)

with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Zones", df["zone"].nunique())
    c3.metric("Held-out rows", f"{len(test):,}")
    c4.metric("AI alerts", f"{len(alerts):,}")
    st.write(
        f"Training window ends before **{config.TRAIN_CUTOFF}**; "
        f"readings from then on ({len(test):,} rows) are held out."
    )
    st.dataframe(df.head(20), use_container_width=True)

with tab_alerts:
    st.subheader("Investigation leads (Isolation Forest)")
    st.caption("An alert means review this pattern — not that a leak is confirmed.")
    if alerts.empty:
        st.warning("No AI alerts on the held-out window.")
    else:
        show = alerts.drop(columns=["rank_score"], errors="ignore")
        st.dataframe(show, use_container_width=True)

with tab_chart:
    st.subheader("Zone signal chart")
    zones = sorted(df["zone"].unique())
    default_zone = "Zone 03" if "Zone 03" in zones else zones[0]
    zone = st.selectbox("Zone", zones, index=zones.index(default_zone))
    zone_df = df[df["zone"] == zone].sort_values("timestamp")
    chart_df = zone_df.set_index("timestamp")[["flow_index", "pressure_index"]]
    st.line_chart(chart_df)
    st.caption("Romaro: replace/extend with Plotly + alert-window highlight in Phase 1 polish.")

with tab_metrics:
    st.subheader("Held-out results (synthetic data only)")
    st.caption(
        "Scored per leak event: an alarm episode is a run of flagged hours in one zone. "
        "Ranges are exact 95% confidence intervals; with only a few events they are wide. "
        "The random row is the floor any detector must beat."
    )
    st.dataframe(metrics_table, use_container_width=True, hide_index=True)
    st.warning("Simulated test only — not validated on NWC sensor data.")

"""AquaWatch Phase 1 Streamlit test product.

Owners: Jason Williams (layout) / Romaro Dixion (charts & demo controls)

Run:
    python -m streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import config
from src.alerts import build_alert_table
from src.baseline import predict_rule
from src.data_loader import DEFAULT_DATA, chronological_split, load_sensor_csv
from src.metrics import compare_rule_and_ai
from src.model import (
    add_deviations,
    load_model_artifacts,
    predict_isolation_forest,
    run_detection,
)

st.set_page_config(page_title="AquaWatch Jamaica", page_icon="💧", layout="wide")

st.warning(config.SIMULATED_DATA_BANNER)
st.title("AquaWatch Jamaica")
st.caption(
    f"{config.PRODUCT_CLAIM} "
    "Phase 1 test product — synthetic data only. Not a confirmed leak detector."
)


@st.cache_data(show_spinner=False)
def _load(path: str) -> pd.DataFrame:
    return load_sensor_csv(path)


with st.sidebar:
    st.header("Data")
    use_default = st.checkbox("Use project synthetic CSV", value=True)
    uploaded = st.file_uploader("Or upload a compatible CSV", type=["csv"])
    prefer_saved = st.checkbox(
        "Use saved model (models/)",
        value=config.MODEL_PATH.exists(),
        help="Guide §14.3: demo should not need to retrain live.",
    )
    st.markdown("---")
    st.markdown("**Team reminder:** labels are for evaluation only, not model features.")

df: pd.DataFrame | None = None
if use_default and DEFAULT_DATA.exists():
    df = _load(str(DEFAULT_DATA))
    st.sidebar.success(f"Loaded {DEFAULT_DATA.name}")
elif uploaded is not None:
    tmp = Path("data") / "_upload_tmp.csv"
    tmp.write_bytes(uploaded.getvalue())
    df = _load(str(tmp))
    st.sidebar.success("Loaded uploaded CSV")
else:
    st.info("Load the synthetic CSV from the sidebar to begin.")
    st.stop()

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
metrics_table = compare_rule_and_ai(scored)

tab_overview, tab_alerts, tab_chart, tab_metrics = st.tabs(
    ["Overview", "Alerts", "Chart", "Metrics"]
)

with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Zones", df["zone"].nunique())
    c3.metric("Held-out rows", f"{len(test):,}")
    c4.metric("AI alerts", f"{len(alerts):,}")
    st.write("Training window ends before **2026-11-11**. Last 4 days are held out.")
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
    pretty = metrics_table.copy()
    pretty["precision"] = pretty["precision"].map(lambda x: f"{x:.1%}")
    pretty["recall"] = pretty["recall"].map(lambda x: f"{x:.1%}")
    st.dataframe(pretty, use_container_width=True)
    st.warning("Simulated test only — not validated on NWC sensor data.")

import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

from utils import (
    find_country_files,
    coerce_numeric,
    daylight_filter,
)

st.set_page_config(page_title="Solar Dashboard (MVP)", layout="wide")

# =========================
# Header
# =========================
st.title("☀️ Solar Dashboard (MVP)")
st.caption("Minimal dashboard: country selection, boxplot, and top regions table. Upload or auto-detect cleaned CSVs.")

# =========================
# Data Input (robust, no blank screen)
# =========================
st.sidebar.header("Data Input")

data_dir = Path("./data")
detected = find_country_files(data_dir)

mode = st.sidebar.radio(
    "Choose data source",
    ["Use local ./data CSVs", "Upload CSVs"],
    index=0 if detected else 1,
)

dfs = []
status_msgs = []

if mode == "Use local ./data CSVs":
    if not detected:
        st.sidebar.warning("No CSVs auto-detected in ./data. Switch to 'Upload CSVs'.")
    else:
        st.sidebar.success(f"Detected {len(detected)} file(s) in ./data.")
        for country, path in detected.items():
            try:
                df = pd.read_csv(path)
                df["Country"] = country
                dfs.append(df)
                status_msgs.append(f"Loaded: {country} ← {path}")
            except Exception as e:
                status_msgs.append(f"❌ Failed to read {path}: {e}")
else:
    files = st.sidebar.file_uploader("Upload 1–3 cleaned CSVs", type="csv", accept_multiple_files=True)
    if files:
        for f in files:
            try:
                df = pd.read_csv(f)
                # Guess country label from filename; let user override
                guess = f.name.split(".")[0].replace("_", " ").title()
                label = st.sidebar.text_input(f"Label for {f.name}", value=guess, key=f"lbl_{f.name}")
                df["Country"] = label
                dfs.append(df)
                status_msgs.append(f"Loaded upload: {label} ({f.name})")
            except Exception as e:
                status_msgs.append(f"❌ Failed to read {f.name}: {e}")

with st.expander("Data load status", expanded=True):
    if status_msgs:
        for m in status_msgs:
            st.write("•", m)
    else:
        st.info("No files loaded yet. Choose a source or upload CSVs from the sidebar.")

if not dfs:
    st.warning("No data available yet. The dashboard will appear once at least one CSV is loaded.")
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# =========================
# Widgets / Filters
# =========================
metrics_available = [c for c in ["GHI", "DNI", "DHI"] if c in df_all.columns]
if not metrics_available:
    st.error("No irradiance metrics (GHI/DNI/DHI) found in the data. Check your CSVs.")
    st.dataframe(df_all.head())
    st.stop()

countries = sorted(df_all["Country"].dropna().unique().tolist())
if not countries:
    st.error("Could not detect any country labels. Ensure each CSV gets a 'Country' column.")
    st.dataframe(df_all.head())
    st.stop()

st.sidebar.header("Controls")
selected_countries = st.sidebar.multiselect("Select countries", countries, default=countries)
metric_choice = st.sidebar.selectbox("Metric for boxplot", metrics_available, index=0)
daylight_only = st.sidebar.checkbox("Daylight only (GHI > threshold)", value=True)
ghi_thr = st.sidebar.slider("Daylight threshold (W/m²)", 5, 150, 20, step=5)

# Filter + numeric coercion
df_view = df_all[df_all["Country"].isin(selected_countries)].copy()
df_view = coerce_numeric(df_view, metrics_available + ["GHI"])
if daylight_only and "GHI" in df_view.columns:
    df_view = daylight_filter(df_view, "GHI", ghi_thr)

# =========================
# Layout
# =========================
tab1, tab2 = st.tabs(["📊 Boxplot", "🏆 Top Regions"])

# ---- Tab 1: Boxplot
with tab1:
    st.subheader(f"{metric_choice} by Country")
    fig = px.box(
        df_view,
        x="Country", y=metric_choice, color="Country",
        points="outliers", template="plotly_white",
        title=f"Distribution of {metric_choice} (by Country)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Summary (mean / median / std)")
    summary = (
        df_view.groupby("Country")[metrics_available]
               .agg(["mean", "median", "std"])
               .round(2)
    )
    st.dataframe(summary, use_container_width=True)

# ---- Tab 2: Top Regions
with tab2:
    st.subheader("Rank by Average GHI")
    if "GHI" in df_view.columns:
        rank = (
            df_view.groupby("Country")["GHI"]
                   .mean()
                   .dropna()
                   .sort_values(ascending=False)
                   .round(2)
        )
        st.dataframe(rank.rename("Mean_GHI").reset_index(), use_container_width=True)

        fig2 = px.bar(
            rank,
            title="Average GHI (higher is better)",
            labels={"value": "Mean GHI (W/m²)", "index": "Country"},
            template="plotly_white",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("GHI not found; cannot compute ranking.")

st.caption("Tip: Place cleaned CSVs in ./data (ignored by git) or upload via the sidebar. Columns expected: GHI/DNI/DHI (+ Country).")

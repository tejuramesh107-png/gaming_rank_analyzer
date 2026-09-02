import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Gaming Rank & Latency Analyzer", layout="wide")

st.title("🎮 Gaming Rank & Latency Analyzer")
st.subheader("Interactive Browser Dashboard")

# Load sessions data (tries SQL database first, falls back to CSV)
@st.cache_data
def load_data():
    if os.path.exists("gaming_data.db"):
        try:
            conn = sqlite3.connect("gaming_data.db")
            df = pd.read_sql_query("SELECT * FROM raw_sessions", conn)
            conn.close()
            return df
        except Exception:
            pass
    if os.path.exists("raw_sessions.csv"):
        return pd.read_csv("raw_sessions.csv")
    elif os.path.exists("raw_players.csv"):
        return pd.read_csv("raw_players.csv")
    else:
        return pd.DataFrame()

df = load_data()

# Identify ping column automatically
ping_col = "ping_ms" if "ping_ms" in df.columns else ("ping" if "ping" in df.columns else None)

# Sidebar options
st.sidebar.header("Filter Options")
if not df.empty and "region" in df.columns:
    selected_region = st.sidebar.multiselect(
        "Select Region:",
        options=df["region"].unique(),
        default=df["region"].unique()
    )
    filtered_df = df[df["region"].isin(selected_region)]
else:
    filtered_df = df

# Display Raw Data Toggle
if st.checkbox("Show Raw Data Table", value=True):
    st.dataframe(filtered_df.head(10))

# Visualizations and AI Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Ping Latency Distribution")
    if not filtered_df.empty and ping_col:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(filtered_df[ping_col], kde=True, ax=ax, color="#6c5ce7")
        ax.set_xlabel("Ping (ms)")
        ax.set_ylabel("Session Count")
        ax.set_title("Ping Latency Distribution")
        st.pyplot(fig)
    else:
        st.info("No ping latency data available for plot.")

with col2:
    st.markdown("### 🤖 Generative AI Executive Summary")
    if os.path.exists("reports/ai_summary.txt"):
        with open("reports/ai_summary.txt", "r", encoding="utf-8") as f:
            summary = f.read()
        st.success(summary)
    else:
        st.warning("No summary report found in reports/ai_summary.txt")
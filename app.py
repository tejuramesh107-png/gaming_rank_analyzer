import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Gaming Rank & Latency Analyzer", layout="wide")

st.title("🎮 Gaming Rank & Latency Analyzer")
st.subheader("Interactive Browser Dashboard")

# Load and join relational data from SQLite or CSV fallback
@st.cache_data
def load_data():
    if os.path.exists("gaming_data.db"):
        try:
            conn = sqlite3.connect("gaming_data.db")
            # Join session data with player region data
            query = """
            SELECT s.*, p.region, p.rank_tier 
            FROM raw_sessions s
            LEFT JOIN raw_players p ON s.player_id = p.player_id
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception:
            pass
            
    # CSV Fallback
    if os.path.exists("raw_sessions.csv"):
        df_sessions = pd.read_csv("raw_sessions.csv")
        if os.path.exists("raw_players.csv"):
            df_players = pd.read_csv("raw_players.csv")
            return pd.merge(df_sessions, df_players, on="player_id", how="left")
        return df_sessions
    return pd.DataFrame()

df = load_data()

# Identify ping column automatically
ping_col = "ping_ms" if "ping_ms" in df.columns else ("ping" if "ping" in df.columns else None)

# --- SIDEBAR FILTER CONTROLS ---
st.sidebar.header("Filter Options")

filtered_df = df.copy()

if not df.empty:
    # Region Multi-Select Filter
    if "region" in df.columns and df["region"].notna().any():
        available_regions = list(df["region"].dropna().unique())
        selected_regions = st.sidebar.multiselect(
            "Select Server Region(s):",
            options=available_regions,
            default=available_regions
        )
        filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]
    
    # Ping Slider Filter
    if ping_col and not filtered_df.empty:
        min_ping = int(df[ping_col].min())
        max_ping = int(df[ping_col].max())
        selected_ping_range = st.sidebar.slider(
            "Ping Range (ms):",
            min_value=min_ping,
            max_value=max_ping,
            value=(min_ping, max_ping)
        )
        filtered_df = filtered_df[
            (filtered_df[ping_col] >= selected_ping_range[0]) & 
            (filtered_df[ping_col] <= selected_ping_range[1])
        ]

# Toggle Raw Data Table
show_raw_data = st.checkbox("Show Raw Data Table", value=True)
if show_raw_data:
    st.dataframe(filtered_df.head(10))

# --- DASHBOARD VISUALIZATIONS ---
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
        st.info("No ping latency data available for selected filters.")

with col2:
    st.markdown("### 🤖 Generative AI Executive Summary")
    if os.path.exists("reports/ai_summary.txt"):
        with open("reports/ai_summary.txt", "r", encoding="utf-8") as f:
            summary = f.read()
        st.success(summary)
    else:
        st.warning("No summary report found in reports/ai_summary.txt")
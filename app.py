import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Gaming Telemetry & Latency Analyzer", layout="wide")

# --- HEADER & OBJECTIVE ---
st.title("🎮 Gaming Rank & Server Latency Analyzer")

st.markdown("""
### 🎯 Project Objective
Analyze gaming telemetry data to understand how server region and network latency affect a player's connectivity, match outcomes, and competitive performance.

> **❓ Main Analytical Question:**  
> *How do server region and network latency influence player's connectivity, match outcomes, and competitive performance?*
""")

# --- USER GUIDE EXPANDER ---
with st.expander("ℹ️ **How to navigate and use this dashboard**", expanded=False):
    st.markdown("""
    * **Sidebar Filters:** Use the left sidebar to select specific **Server Regions** or adjust the **Ping Range (ms)** slider.
    * **KPI Metrics:** Track real-time changes in average latency, total sessions, disconnect rates, and high lag spikes ($>150\\text{ ms}$).
    * **Visualizations:**
      * **Server Ping Distribution:** View frequency distribution of connection latency across active player sessions.
      * **Match Outcome Breakdown:** Analyze win/loss/disconnect ratios under the selected filter criteria.
    * **Raw Telemetry Explorer:** Inspect individual player session logs at the bottom of the page.
    """)

# --- DATABASE CONNECTION ---
@st.cache_data
def load_data():
    conn = sqlite3.connect("gaming_data.db")
    
    sessions_df = pd.read_sql_query("""
        SELECT 
            s.session_id,
            s.player_id,
            p.username,
            p.region,
            s.ping_ms,
            s.disconnected
        FROM sessions s
        LEFT JOIN players p ON s.player_id = p.player_id;
    """, conn)
    
    matches_df = pd.read_sql_query("SELECT * FROM matches;", conn)
    conn.close()
    
    outcome_col = "match_outcome" if "match_outcome" in matches_df.columns else "outcome"
    
    if "player_id" in matches_df.columns:
        sessions_df = sessions_df.merge(matches_df[["player_id", outcome_col]], on="player_id", how="left")
    else:
        sessions_df["match_outcome"] = matches_df[outcome_col].reindex(sessions_df.index).values

    sessions_df["match_outcome"] = sessions_df["match_outcome"].fillna("Unknown")
    return sessions_df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading telemetry database: {e}")
    st.stop()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🔍 Telemetry Filters")

all_regions = sorted(df["region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Select Server Region(s)",
    options=all_regions,
    default=all_regions,
    help="Filter data to analyze specific global game server clusters."
)

min_ping, max_ping = int(df["ping_ms"].min()), int(df["ping_ms"].max())
ping_range = st.sidebar.slider(
    "Filter by Ping Range (ms)",
    min_value=min_ping,
    max_value=max_ping,
    value=(min_ping, max_ping),
    help="Isolate smooth sessions (<50ms) vs severe lag spikes (>150ms)."
)

filtered_df = df[
    (df["region"].isin(selected_regions)) &
    (df["ping_ms"] >= ping_range[0]) &
    (df["ping_ms"] <= ping_range[1])
]

# --- 1. KPI METRIC CARDS ---
st.markdown("### 📈 Real-Time Connectivity Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_sessions = len(filtered_df)
avg_ping = round(filtered_df["ping_ms"].mean(), 1) if total_sessions > 0 else 0
dc_rate = round((filtered_df["disconnected"].sum() / total_sessions * 100), 1) if total_sessions > 0 else 0
high_lag_spikes = len(filtered_df[filtered_df["ping_ms"] > 150])

kpi1.metric("Average Ping", f"{avg_ping} ms")
kpi2.metric("Total Sessions", f"{total_sessions:,}")
kpi3.metric("Disconnect Rate", f"{dc_rate}%")
kpi4.metric("High Lag Spikes (>150ms)", f"{high_lag_spikes}")

st.markdown("---")

# --- 2. CHARTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📶 Server Ping Distribution")
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(data=filtered_df, x="ping_ms", bins=25, kde=True, ax=ax, color="#6c5ce7")
        ax.set_xlabel("Ping Latency (ms)")
        ax.set_ylabel("Active Sessions")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No session telemetry data found for selected filter.")

with col2:
    st.subheader("🏆 Match Outcome Breakdown")
    if not filtered_df.empty:
        outcome_counts = filtered_df["match_outcome"].value_counts()
        if not outcome_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            ax2.pie(
                outcome_counts, 
                labels=outcome_counts.index, 
                autopct="%1.1f%%", 
                colors=["#55efc4", "#ff7675", "#ffeaa7", "#b2bec3"],
                startangle=140
            )
            st.pyplot(fig2)
        else:
            st.warning("⚠️ No match outcomes found in this range.")
    else:
        st.warning("⚠️ No outcome data available for selected range.")

# --- 3. EXECUTIVE SUMMARY ---
st.markdown("---")
st.subheader("🤖 Analytical Insights Summary")
if not filtered_df.empty:
    st.info(
        f"**Findings:** Across **{len(selected_regions)}** regions, players experience an average latency of **{avg_ping} ms** "
        f"and a **{dc_rate}% disconnect rate**. A total of **{high_lag_spikes} sessions** suffer from latency spikes exceeding 150 ms, "
        f"which negatively impacts player performance and connection stability."
    )

# --- 4. DATA TABLE ---
st.markdown("---")
st.subheader("📋 Session Telemetry Explorer")
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["session_id", "player_id", "username", "region", "ping_ms", "disconnected", "match_outcome"]],
        use_container_width=True
    )
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Gaming Telemetry & Latency Analyzer",
    layout="wide",
    page_icon="🎮"
)

# --- 2. POP-UP DIALOG (MODAL) ---
@st.dialog("📖 App Guide & Network Terminology")
def show_guide_modal():
    st.markdown("""
    ### 🎯 Project Context
    This dashboard analyzes player telemetry for high-stakes tactical esports servers (e.g., *Valorant* / *Counter-Strike 2* style infrastructure).
    
    ---
    
    ### ⚡ Key Concepts Explained
    * **What is Ping (Latency)?**  
      Measured in milliseconds ($\text{ms}$), ping is the round-trip travel time for data between a player's PC and the server.  
      * **$<50\text{ ms}$:** Ideal competitive latency.  
      * **$>150\text{ ms}$:** Severe delay (causes rubberbanding and input lag).
    * **What is Server Region?**  
      The geographic cluster hosting game matches (e.g., NA, EU, APAC). Distance to server directly impacts ping.
    * **Disconnect Rate:**  
      Percentage of total sessions abruptly terminated due to severe network instability.

    ---
    
    ### 💡 How to Interact with the Dashboard
    1. **Sidebar Filters:** Select target server regions or narrow down the **Ping Range** slider.
    2. **KPI Metrics:** Track live variations in average latency, total sessions, and lag spikes.
    3. **Visual Distribution:** View latency curves and match win/loss/forfeit proportions.
    4. **Telemetry Explorer:** Search individual player log records at the bottom table.
    """)
    if st.button("Got it!", type="primary"):
        st.rerun()

# --- 3. DATABASE LOAD & DATA CLEANING ---
@st.cache_data
def load_data():
    conn = sqlite3.connect("gaming_data.db")
    
    # Read telemetry tables
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
    
    # Match outcome column identification
    outcome_col = "match_outcome" if "match_outcome" in matches_df.columns else "outcome"
    
    # Merge matches with session records
    if "session_id" in matches_df.columns:
        sessions_df = sessions_df.merge(matches_df[["session_id", outcome_col]], on="session_id", how="left")
    elif "player_id" in matches_df.columns:
        sessions_df = sessions_df.merge(matches_df[["player_id", outcome_col]], on="player_id", how="left")
    else:
        sessions_df["match_outcome"] = matches_df[outcome_col].reindex(sessions_df.index).values

    # Clean out missing outcome rows to eliminate "Unknown" pie slice completely
    sessions_df["match_outcome"] = sessions_df[outcome_col]
    sessions_df = sessions_df.dropna(subset=["match_outcome"])
    sessions_df = sessions_df[~sessions_df["match_outcome"].isin(["Unknown", "none", ""])]
    
    return sessions_df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# --- 4. HEADER & OBJECTIVE SECTION ---
st.title("🎮 Gaming Rank & Server Latency Analyzer")
st.caption("📍 Benchmark Context: Tactical FPS Esports Telemetry Data")

st.markdown("""
### 🎯 Project Objective
Analyze gaming telemetry data to understand how server region and network latency affect a player's connectivity, match outcomes, and competitive performance.

> **❓ Main Analytical Question:**  
> *How do server region and network latency influence player's connectivity, match outcomes, and competitive performance?*
""")

st.markdown("---")

# --- 5. SIDEBAR CONTROLS ---
st.sidebar.header("🔍 Controls & Guidance")

# Trigger button for Pop-up Modal
if st.sidebar.button("ℹ️ App & Network Guide", use_container_width=True):
    show_guide_modal()

st.sidebar.markdown("---")
st.sidebar.subheader("Telemetry Filters")

all_regions = sorted(df["region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Select Server Region(s)",
    options=all_regions,
    default=all_regions,
    help="Filter data to isolate specific global server regions."
)

min_ping, max_ping = int(df["ping_ms"].min()), int(df["ping_ms"].max())
ping_range = st.sidebar.slider(
    "Filter by Ping Range (ms)",
    min_value=min_ping,
    max_value=max_ping,
    value=(min_ping, max_ping),
    help="Isolate smooth sessions (<50ms) vs severe latency (>150ms)."
)

# Apply active filters
filtered_df = df[
    (df["region"].isin(selected_regions)) &
    (df["ping_ms"] >= ping_range[0]) &
    (df["ping_ms"] <= ping_range[1])
]

# --- 6. KPI METRICS ---
st.subheader("📈 Real-Time Connectivity Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_sessions = len(filtered_df)
avg_ping = round(filtered_df["ping_ms"].mean(), 1) if total_sessions > 0 else 0
dc_rate = round((filtered_df["disconnected"].sum() / total_sessions * 100), 1) if total_sessions > 0 else 0
high_lag_spikes = len(filtered_df[filtered_df["ping_ms"] > 150])

kpi1.metric("Average Ping", f"{avg_ping} ms", help="Target latency for competitive balance is <50 ms")
kpi2.metric("Total Active Sessions", f"{total_sessions:,}")
kpi3.metric("Disconnect Rate", f"{dc_rate}%", help="Percentage of network drops")
kpi4.metric("High Lag Spikes (>150ms)", f"{high_lag_spikes}", help="Sessions with severe lag impact")

st.markdown("---")

# --- 7. CHARTS & VISUALIZATIONS ---
col1, col2 = st.columns(2)

sns.set_theme(style="whitegrid")

with col1:
    st.subheader("📶 Server Ping Distribution")
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(data=filtered_df, x="ping_ms", bins=25, kde=True, ax=ax, color="#6c5ce7")
        ax.set_xlabel("Ping Latency (ms)")
        ax.set_ylabel("Active Sessions")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No telemetry records found for current filter selection.")

with col2:
    st.subheader("🏆 Match Outcome Breakdown")
    if not filtered_df.empty:
        outcome_counts = filtered_df["match_outcome"].value_counts()
        
        if not outcome_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            colors = ["#ff7675", "#55efc4", "#ffeaa7", "#74b9ff"]
            
            ax2.pie(
                outcome_counts, 
                labels=outcome_counts.index, 
                autopct="%1.1f%%", 
                colors=colors[:len(outcome_counts)],
                startangle=140,
                explode=[0.03] * len(outcome_counts)
            )
            st.pyplot(fig2)
        else:
            st.warning("⚠️ No valid match outcomes found for selected range.")
    else:
        st.warning("⚠️ No outcome data available for current filter selection.")

# --- 8. EXECUTIVE SUMMARY & RAW DATA ---
st.markdown("---")
st.subheader("🤖 Analytical Insights Summary")
if not filtered_df.empty:
    st.info(
        f"**Findings:** Across **{len(selected_regions)}** server regions, players average **{avg_ping} ms** connection latency "
        f"with a **{dc_rate}% disconnect rate**. A total of **{high_lag_spikes} sessions** suffer from lag spikes exceeding 150 ms, "
        f"which directly degrades player performance and session stability."
    )

st.markdown("---")
st.subheader("📋 Session Telemetry Explorer")
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["session_id", "player_id", "username", "region", "ping_ms", "disconnected", "match_outcome"]],
        use_container_width=True
    )
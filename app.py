import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. PAGE CONFIG & DARK GAMING THEME CSS ---
st.set_page_config(
    page_title="Gaming Rank & Server Latency Analyzer",
    layout="wide",
    page_icon="🎮"
)

# Custom Dark Gaming CSS
st.markdown("""
    <style>
    /* Dark Backgrounds */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. POP-UP GUIDE MODAL ---
@st.dialog("📖 App Guide & Network Terminology")
def show_guide_modal():
    st.markdown("""
    ### 🎯 Benchmark Context: Tactical FPS Esports
    This control room measures connection quality for competitive tactical shooters like **Valorant** and **Counter-Strike 2 (CS2)**.

    ---
    ### ⚡ Network Metrics Explained
    * **Ping (Latency):** Travel time (in milliseconds) between player and server. Lower is better ($<50\\text{ ms}$).
    * **Disconnect Rate:** Percentage of total sessions interrupted by network drops.
    * **High Lag Spikes ($>150\\text{ ms}$):** Severe delay causing rubberbanding and match forfeits.
    
    ---
    ### 💡 How to Use
    * Use the **Sidebar Filters** to select server regions or ping limits. Charts update instantly!
    """)
    if st.button("Close Guide", type="primary"):
        st.rerun()

# --- 3. DATABASE LOADING ---
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
    
    if "session_id" in matches_df.columns:
        sessions_df = sessions_df.merge(matches_df[["session_id", outcome_col]], on="session_id", how="left")
    elif "player_id" in matches_df.columns:
        sessions_df = sessions_df.merge(matches_df[["player_id", outcome_col]], on="player_id", how="left")
    else:
        sessions_df["match_outcome"] = matches_df[outcome_col].reindex(sessions_df.index).values

    # Clean missing outcomes so "Unknown" never appears in pie chart
    sessions_df["match_outcome"] = sessions_df[outcome_col]
    sessions_df = sessions_df.dropna(subset=["match_outcome"])
    sessions_df = sessions_df[~sessions_df["match_outcome"].isin(["Unknown", "none", ""])]
    
    return sessions_df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# --- 4. HEADER & CONTEXT ---
st.title("🎮 Gaming Rank & Server Latency Analyzer")
st.caption("🎮 **Benchmark Game Context:** Tactical FPS Esports Infrastructure (Valorant / CS2 Telemetry)")

st.markdown("""
### 🎯 Project Objective
Analyze gaming telemetry data to understand how server region and network latency affect a player's connectivity, match outcomes, and competitive performance.

> **❓ Main Analytical Question:**  
> *How do server region and network latency influence player's connectivity, match outcomes, and competitive performance?*
""")

st.markdown("---")

# --- 5. SIDEBAR FILTERS (AUTOMATIC UPDATES) ---
st.sidebar.header("🔍 Controls & Filters")

if st.sidebar.button("ℹ️ App & Network Guide", use_container_width=True):
    show_guide_modal()

st.sidebar.markdown("---")

# Modern Region Selector (Single / All Region dropdown for clean UI)
all_regions = sorted(df["region"].dropna().unique().tolist())
region_option = st.sidebar.selectbox(
    "Select Server Region",
    options=["All Regions"] + all_regions,
    help="Filter data by specific server location."
)

if region_option == "All Regions":
    selected_regions = all_regions
else:
    selected_regions = [region_option]

# Ping Slider (Triggers instant automatic chart reruns)
min_ping, max_ping = int(df["ping_ms"].min()), int(df["ping_ms"].max())
ping_range = st.sidebar.slider(
    "Filter by Ping Range (ms)",
    min_value=min_ping,
    max_value=max_ping,
    value=(min_ping, max_ping),
    help="Drag sliders to isolate smooth gameplay vs lag spikes."
)

# Apply Filter
filtered_df = df[
    (df["region"].isin(selected_regions)) &
    (df["ping_ms"] >= ping_range[0]) &
    (df["ping_ms"] <= ping_range[1])
]

# --- 6. LIVE METRIC CARDS ---
st.subheader("📈 Real-Time Connectivity Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_sessions = len(filtered_df)
avg_ping = round(filtered_df["ping_ms"].mean(), 1) if total_sessions > 0 else 0
dc_rate = round((filtered_df["disconnected"].sum() / total_sessions * 100), 1) if total_sessions > 0 else 0
high_lag_spikes = len(filtered_df[filtered_df["ping_ms"] > 150])

kpi1.metric("Average Ping", f"{avg_ping} ms")
kpi2.metric("Total Active Sessions", f"{total_sessions:,}")
kpi3.metric("Disconnect Rate", f"{dc_rate}%")
kpi4.metric("High Lag Spikes (>150ms)", f"{high_lag_spikes}")

st.markdown("---")

# --- 7. AUTOMATIC CHARTS ---
col1, col2 = st.columns(2)

# Dark Plot Theme
plt.style.use("dark_background")

with col1:
    st.subheader("📶 Server Ping Distribution")
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#161b22')
        sns.histplot(data=filtered_df, x="ping_ms", bins=25, kde=True, ax=ax, color="#a29bfe")
        ax.set_xlabel("Ping Latency (ms)")
        ax.set_ylabel("Active Sessions")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No records match current filter settings.")

with col2:
    st.subheader("🏆 Match Outcome Breakdown")
    if not filtered_df.empty:
        outcome_counts = filtered_df["match_outcome"].value_counts()
        
        if not outcome_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            fig2.patch.set_facecolor('#0e1117')
            colors = ["#00b894", "#ff7675", "#fdcb6e", "#0984e3"]
            
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
            st.warning("⚠️ No valid outcomes found.")
    else:
        st.warning("⚠️ No outcome data available.")

# --- 8. EXECUTIVE SUMMARY & DATA TABLE ---
st.markdown("---")
st.subheader("🤖 Analytical Insights Summary")
if not filtered_df.empty:
    st.info(
        f"**Findings:** Across **{len(selected_regions)}** selected regions, players average **{avg_ping} ms** connection latency "
        f"with a **{dc_rate}% disconnect rate**. A total of **{high_lag_spikes} sessions** suffer from lag spikes exceeding 150 ms."
    )

st.markdown("---")
st.subheader("📋 Session Telemetry Explorer")
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["session_id", "player_id", "username", "region", "ping_ms", "disconnected", "match_outcome"]],
        use_container_width=True
    )
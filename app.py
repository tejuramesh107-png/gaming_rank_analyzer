import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. PAGE CONFIG & CREATIVE ESPORTS CSS ---
st.set_page_config(
    page_title="Esports Latency Analyzer",
    layout="wide",
    page_icon="🎮"
)

# Custom High-End Esports UI Styling
st.markdown("""
    <style>
    /* Dark Cyber Esports Background with Grid Overlay */
    .stApp {
        background-color: #0b0d19;
        background-image: 
            radial-gradient(circle at 15% 15%, rgba(124, 58, 237, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 85% 85%, rgba(0, 242, 254, 0.12) 0%, transparent 40%),
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
        color: #f1f5f9;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #06070e !important;
        border-right: 1px solid #1e1b4b;
    }
    
    /* Dropdown and Input Box Styling */
    div[data-baseweb="select"] > div {
        background-color: #121528 !important;
        color: #ffffff !important;
        border: 1px solid #6366f1 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    /* Neon Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(18, 21, 40, 0.85);
        border: 1px solid #6366f1;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 15px;
    }
    div[data-testid="stMetricLabel"] p {
        color: #a5b4fc !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #00f2fe !important;
        font-weight: 900 !important;
        font-size: 2rem !important;
        text-shadow: 0 0 8px rgba(0, 242, 254, 0.6);
    }

    /* Custom Esports Dark Table Styling */
    .esports-table-container {
        background-color: #121528;
        border: 1px solid #312e81;
        border-radius: 10px;
        padding: 10px;
        overflow-x: auto;
    }
    .esports-table {
        width: 100%;
        border-collapse: collapse;
        color: #e2e8f0;
        font-family: sans-serif;
        font-size: 0.9rem;
    }
    .esports-table th {
        background-color: #1e1b4b;
        color: #00f2fe;
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid #6366f1;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
    }
    .esports-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #1e293b;
    }
    .esports-table tr:hover {
        background-color: #1e1b4b;
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
    * Use the **Sidebar Filters** to select server regions or ping limits.
    """)
    if st.button("Close Guide", type="primary"):
        st.rerun()

# --- 3. DATA LOADING & CLEANING ---
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

    # Clean out unknown outcome entries
    sessions_df["match_outcome"] = sessions_df[outcome_col]
    sessions_df = sessions_df.dropna(subset=["match_outcome"])
    sessions_df = sessions_df[~sessions_df["match_outcome"].isin(["Unknown", "none", ""])]
    
    return sessions_df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# --- 4. HEADER ---
st.title("⚡ Gaming Rank & Server Latency Analyzer")
st.caption("🎮 **Domain Benchmark:** Esports Tactical FPS Servers (Valorant / CS2 Telemetry)")

st.markdown("""
### 🎯 Project Objective
Analyze gaming telemetry data to understand how server region and network latency affect player connectivity, match outcomes, and competitive performance.

> **❓ Main Analytical Question:**  
> *How do server region and network latency influence player connectivity, match outcomes, and competitive performance?*
""")

st.markdown("---")

# --- 5. SIDEBAR FILTERS ---
st.sidebar.header("🕹️ Telemetry Controls")

if st.sidebar.button("ℹ️ App & Network Guide", use_container_width=True):
    show_guide_modal()

st.sidebar.markdown("---")

all_regions = sorted(df["region"].dropna().unique().tolist())
region_option = st.sidebar.selectbox(
    "Select Server Region",
    options=["All Regions"] + all_regions,
    help="Filter data by server cluster."
)

if region_option == "All Regions":
    selected_regions = all_regions
else:
    selected_regions = [region_option]

min_ping, max_ping = int(df["ping_ms"].min()), int(df["ping_ms"].max())
ping_range = st.sidebar.slider(
    "Filter by Ping Range (ms)",
    min_value=min_ping,
    max_value=max_ping,
    value=(min_ping, max_ping)
)

filtered_df = df[
    (df["region"].isin(selected_regions)) &
    (df["ping_ms"] >= ping_range[0]) &
    (df["ping_ms"] <= ping_range[1])
]

# --- 6. KPI METRIC CARDS ---
st.subheader("📈 Real-Time Connectivity Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_sessions = len(filtered_df)
avg_ping = round(filtered_df["ping_ms"].mean(), 1) if total_sessions > 0 else 0
dc_rate = round((filtered_df["disconnected"].sum() / total_sessions * 100), 1) if total_sessions > 0 else 0
high_lag_spikes = len(filtered_df[filtered_df["ping_ms"] > 150])

kpi1.metric("Average Ping", f"{avg_ping} ms")
kpi2.metric("Total Active Sessions", f"{total_sessions:,}")
kpi3.metric("Disconnect Rate", f"{dc_rate}%")
kpi4.metric("Lag Spikes (>150ms)", f"{high_lag_spikes}")

st.markdown("---")

# --- 7. CHARTS ---
col1, col2 = st.columns(2)

plt.style.use("dark_background")

with col1:
    st.subheader("📶 Server Ping Distribution")
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0b0d19')
        ax.set_facecolor('#121528')
        sns.histplot(data=filtered_df, x="ping_ms", bins=25, kde=True, ax=ax, color="#00f2fe")
        ax.set_xlabel("Ping Latency (ms)", color="#a5b4fc")
        ax.set_ylabel("Active Sessions", color="#a5b4fc")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No matching records found.")

with col2:
    st.subheader("🏆 Match Outcome Breakdown")
    if not filtered_df.empty:
        outcome_counts = filtered_df["match_outcome"].value_counts()
        
        if not outcome_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            fig2.patch.set_facecolor('#0b0d19')
            colors = ["#00f2fe", "#ff4757", "#ffa502", "#2ed573"]
            
            ax2.pie(
                outcome_counts, 
                labels=outcome_counts.index, 
                autopct="%1.1f%%", 
                colors=colors[:len(outcome_counts)],
                startangle=140,
                explode=[0.03] * len(outcome_counts),
                textprops={'color': '#ffffff', 'weight': 'bold'}
            )
            st.pyplot(fig2)
        else:
            st.warning("⚠️ No outcome data available.")
    else:
        st.warning("⚠️ No outcome data available.")

# --- 8. EXECUTIVE SUMMARY & DARK TABLE ---
st.markdown("---")
st.subheader("🤖 Analytical Insights Summary")
if not filtered_df.empty:
    st.info(
        f"**Findings:** Across **{len(selected_regions)}** server regions, players average **{avg_ping} ms** connection latency "
        f"with a **{dc_rate}% disconnect rate**. A total of **{high_lag_spikes} sessions** suffer from lag spikes exceeding 150 ms."
    )

st.markdown("---")
st.subheader("📋 Session Telemetry Explorer")
if not filtered_df.empty:
    # Display table as styled HTML to guarantee dark theme integration
    table_df = filtered_df[["session_id", "player_id", "username", "region", "ping_ms", "disconnected", "match_outcome"]].head(100)
    html_table = table_df.to_html(classes="esports-table", index=False)
    
    st.markdown(f'<div class="esports-table-container">{html_table}</div>', unsafe_allow_html=True)
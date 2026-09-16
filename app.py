import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. PAGE CONFIG & ESPORTS GAMING THEME CSS ---
st.set_page_config(
    page_title="Gaming Rank & Server Latency Analyzer",
    layout="wide",
    page_icon="🎮"
)

# Creative Esports Dark Theme CSS (Neon Purple / Cyan Accents + High Contrast Text)
st.markdown("""
    <style>
    /* Esports Gradient App Background */
    .stApp {
        background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #060913 100%);
        color: #ffffff;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0b0818 !important;
        border-right: 1px solid #2d1f47;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    /* Fixed KPI Metric Cards: Bright High-Contrast Text */
    div[data-testid="stMetric"] {
        background: rgba(23, 15, 48, 0.85);
        border: 1px solid #7c3aed;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
        border-radius: 12px;
        padding: 15px;
    }
    div[data-testid="stMetricLabel"] p {
        color: #a7f3d0 !important; /* Bright Mint Green Label */
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #00f2fe !important; /* Bright Electric Cyan Numbers */
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    /* Styled Telemetry Data Table to match Esports Dark Theme */
    [data-testid="stDataFrame"] {
        background-color: #120e24 !important;
        border-radius: 10px;
        border: 1px solid #3b0764;
    }

    /* Primary Accent Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #7c3aed 0%, #00f2fe 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
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
    * Use the **Sidebar Filters** to select server regions or ping limits. Charts update automatically!
    """)
    if st.button("Close Guide", type="primary"):
        st.rerun()

# --- 3. DATABASE LOADING & CLEANUP ---
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

# --- 4. HEADER SECTION ---
st.title("🎮 Esports Network Telemetry Dashboard")
st.caption("📍 Benchmark Context: Tactical FPS Infrastructure (Valorant / CS2 Regional Telemetry)")

st.markdown("""
### 🎯 Project Objective
Analyze gaming telemetry data to understand how server region and network latency affect connectivity, match outcomes, and competitive performance.

> **❓ Main Analytical Question:**  
> *How do server region and network latency influence connectivity, match outcomes, and competitive performance?*
""")

st.markdown("---")

# --- 5. SIDEBAR FILTERS ---
st.sidebar.header("⚡ Control Panel")

if st.sidebar.button("ℹ️ App & Network Guide", use_container_width=True):
    show_guide_modal()

st.sidebar.markdown("---")

# Server Region Dropdown
all_regions = sorted(df["region"].dropna().unique().tolist())
region_option = st.sidebar.selectbox(
    "Select Server Region",
    options=["All Regions"] + all_regions,
    help="Filter data by specific global server location."
)

if region_option == "All Regions":
    selected_regions = all_regions
else:
    selected_regions = [region_option]

# Latency Range Slider
min_ping, max_ping = int(df["ping_ms"].min()), int(df["ping_ms"].max())
ping_range = st.sidebar.slider(
    "Filter by Ping Range (ms)",
    min_value=min_ping,
    max_value=max_ping,
    value=(min_ping, max_ping),
    help="Drag sliders to isolate smooth gameplay (<50ms) vs severe lag."
)

# Apply Filter
filtered_df = df[
    (df["region"].isin(selected_regions)) &
    (df["ping_ms"] >= ping_range[0]) &
    (df["ping_ms"] <= ping_range[1])
]

# --- 6. HIGH-CONTRAST METRIC CARDS ---
st.subheader("📈 Connectivity Metrics")
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

# --- 7. CHARTS & VISUALIZATIONS ---
col1, col2 = st.columns(2)

plt.style.use("dark_background")

with col1:
    st.subheader("📶 Latency Distribution")
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0f0c20')
        ax.set_facecolor('#15102a')
        sns.histplot(data=filtered_df, x="ping_ms", bins=25, kde=True, ax=ax, color="#00f2fe")
        ax.set_xlabel("Ping Latency (ms)", color="#e2e8f0")
        ax.set_ylabel("Active Sessions", color="#e2e8f0")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No records match current filter settings.")

with col2:
    st.subheader("🏆 Match Outcome Ratio")
    if not filtered_df.empty:
        outcome_counts = filtered_df["match_outcome"].value_counts()
        
        if not outcome_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            fig2.patch.set_facecolor('#0f0c20')
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
            st.warning("⚠️ No valid outcomes found.")
    else:
        st.warning("⚠️ No outcome data available.")

# --- 8. EXECUTIVE SUMMARY & TELEMETRY EXPLORER ---
st.markdown("---")
st.subheader("🤖 Analytical Insights Summary")
if not filtered_df.empty:
    st.info(
        f"**Findings:** Across **{len(selected_regions)}** server regions, players average **{avg_ping} ms** connection latency "
        f"with a **{dc_rate}% disconnect rate**. A total of **{high_lag_spikes} sessions** suffer from severe lag spikes exceeding 150 ms."
    )

st.markdown("---")
st.subheader("📋 Session Telemetry Explorer")
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["session_id", "player_id", "username", "region", "ping_ms", "disconnected", "match_outcome"]],
        use_container_width=True
    )
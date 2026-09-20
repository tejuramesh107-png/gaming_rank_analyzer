import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import requests
from sklearn.linear_model import LogisticRegression

# --- 1. PAGE CONFIG & GAMING AESTHETIC CSS ---
st.set_page_config(
    page_title="Esports Latency Analyzer",
    layout="wide",
    page_icon="🎮"
)

# Cyberpunk Animated Grid & Esports Overlay
st.markdown("""
    <style>
    /* ANIMATED GAMING BACKGROUND GRID */
    .stApp {
        background-color: #05070f;
        background-image: 
            linear-gradient(rgba(0, 242, 254, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 242, 254, 0.05) 1px, transparent 1px),
            radial-gradient(circle at 50% 20%, rgba(124, 58, 237, 0.25) 0%, transparent 60%);
        background-size: 40px 40px, 40px 40px, 100% 100%;
        color: #ffffff !important;
    }
    
    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #03040a !important;
        border-right: 1px solid #1e1b4b;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(90deg, #7c3aed 0%, #00f2fe 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
    }

    div[data-baseweb="select"] > div {
        background-color: #0f1225 !important;
        color: #ffffff !important;
        border: 1px solid #00f2fe !important;
        border-radius: 8px !important;
    }

    /* NEON GLASSMORPHISM KPI CARDS */
    div[data-testid="stMetric"] {
        background: rgba(15, 18, 37, 0.85);
        border: 1px solid #7c3aed;
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.3), inset 0 0 15px rgba(0, 242, 254, 0.1);
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(5px);
    }
    div[data-testid="stMetricLabel"] p {
        color: #a5b4fc !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #00f2fe !important;
        font-weight: 900 !important;
        font-size: 2rem !important;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.8);
    }

    /* ESPORTS TABLE STYLING */
    .esports-table-container {
        background-color: rgba(15, 18, 37, 0.9);
        border: 1px solid #7c3aed;
        border-radius: 10px;
        padding: 10px;
        overflow-x: auto;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.2);
    }
    .esports-table {
        width: 100%;
        border-collapse: collapse;
        color: #e2e8f0;
        font-family: sans-serif;
        font-size: 0.9rem;
    }
    .esports-table th {
        background-color: #1a103c;
        color: #00f2fe;
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid #00f2fe;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
    }
    .esports-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #1e1b4b;
    }
    .esports-table tr:hover {
        background-color: #241454;
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
    * Use the **Sidebar Filters** or **Upload CSV** to load custom network data.
    * Use the **Live Ping Tester** or **Match Predictor** to simulate network health.
    """)
    if st.button("Close Guide", type="primary"):
        st.rerun()

# --- 3. DATA LOADING & CLEANING ---
@st.cache_data
def load_default_data():
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

    sessions_df["match_outcome"] = sessions_df[outcome_col]
    sessions_df = sessions_df.dropna(subset=["match_outcome"])
    sessions_df = sessions_df[~sessions_df["match_outcome"].isin(["Unknown", "none", ""])]
    
    return sessions_df

# --- 4. SIDEBAR CONTROLS & GIF HEADER ---
st.sidebar.markdown("""
    <div style="text-align: center; padding-bottom: 10px;">
        <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3ZydWJmcGV1cGtkZmh0eXlyZXE5czQ1aXo1ZXB6cnExZDdrOHZzaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPnAiaMCws8nOsE/giphy.gif" width="120" style="border-radius: 10px;">
        <h2 style="color: #00f2fe; margin-top: 5px;">Control Room</h2>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("ℹ️ App & Network Guide", use_container_width=True):
    show_guide_modal()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📁 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload Telemetry CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("Custom CSV Loaded Successfully!")
    except Exception as e:
        st.sidebar.error(f"Error loading CSV: {e}")
        df = load_default_data()
else:
    try:
        df = load_default_data()
    except Exception as e:
        st.error(f"Error loading database: {e}")
        st.stop()

# --- 5. DASHBOARD HEADER WITH GAMING BANNER ---
head_col1, head_col2 = st.columns([3, 1])

with head_col1:
    st.title("⚡ Gaming Rank & Server Latency Analyzer")
    st.caption("🎮 **Domain Benchmark:** Esports Tactical FPS Servers (Valorant / CS2 Telemetry)")

with head_col2:
    st.markdown("""
        <div style="text-align: right;">
            <img src="https://media.giphy.com/media/LpdlqTkgO2L6g/giphy.gif" width="100" style="border-radius: 10px; border: 1px solid #00f2fe;">
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
### 🎯 Project Objective
Analyze gaming telemetry data to understand how server region and network latency affect player connectivity, match outcomes, and competitive performance.
""")

st.markdown("---")

# --- 6. SIDEBAR FILTERS ---
all_regions = sorted(df["region"].dropna().unique().tolist()) if "region" in df.columns else ["N/A"]
region_option = st.sidebar.selectbox(
    "Select Server Region",
    options=["All Regions"] + all_regions,
    help="Filter data by server cluster."
)

if region_option == "All Regions":
    selected_regions = all_regions
else:
    selected_regions = [region_option]

min_ping, max_ping = int(df["ping_ms"].min()), int(df["ping_ms"].max()) if "ping_ms" in df.columns else (0, 100)
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
] if "region" in df.columns and "ping_ms" in df.columns else df

# --- 7. KPI METRIC CARDS ---
st.subheader("📈 Real-Time Connectivity Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_sessions = len(filtered_df)
avg_ping = round(filtered_df["ping_ms"].mean(), 1) if total_sessions > 0 and "ping_ms" in filtered_df.columns else 0
dc_rate = round((filtered_df["disconnected"].sum() / total_sessions * 100), 1) if total_sessions > 0 and "disconnected" in filtered_df.columns else 0
high_lag_spikes = len(filtered_df[filtered_df["ping_ms"] > 150]) if "ping_ms" in filtered_df.columns else 0

kpi1.metric("Average Ping", f"{avg_ping} ms")
kpi2.metric("Total Active Sessions", f"{total_sessions:,}")
kpi3.metric("Disconnect Rate", f"{dc_rate}%")
kpi4.metric("Lag Spikes (>150ms)", f"{high_lag_spikes}")

st.markdown("---")

# --- 8. CHARTS ---
col1, col2 = st.columns(2)
plt.style.use("dark_background")

with col1:
    st.subheader("📶 Server Ping Distribution")
    if not filtered_df.empty and "ping_ms" in filtered_df.columns:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#05070f')
        ax.set_facecolor('#0f1225')
        sns.histplot(data=filtered_df, x="ping_ms", bins=25, kde=True, ax=ax, color="#00f2fe")
        ax.set_xlabel("Ping Latency (ms)", color="#a5b4fc")
        ax.set_ylabel("Active Sessions", color="#a5b4fc")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No matching records found.")

with col2:
    st.subheader("🏆 Match Outcome Breakdown")
    if not filtered_df.empty and "match_outcome" in filtered_df.columns:
        outcome_counts = filtered_df["match_outcome"].value_counts()
        if not outcome_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            fig2.patch.set_facecolor('#05070f')
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

st.markdown("---")

# --- 9. PING TEST SIMULATOR ---
st.subheader("⚡ Live Regional Ping Test Simulator")
st.caption("Measure live HTTP round-trip latency to global public endpoints.")

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    target_region = st.selectbox(
        "Select Server Endpoint",
        ["NA (North America)", "EU (Europe)", "APAC (Asia-Pacific)"]
    )
    run_ping = st.button("🚀 Run Live Ping Test", use_container_width=True)

with sim_col2:
    if run_ping:
        endpoint_urls = {
            "NA (North America)": "https://1.1.1.1",
            "EU (Europe)": "https://8.8.8.8",
            "APAC (Asia-Pacific)": "https://1.0.0.1"
        }
        target_url = endpoint_urls[target_region]
        
        with st.spinner("Pinging server cluster..."):
            try:
                start_time = time.time()
                response = requests.get(target_url, timeout=3)
                latency = round((time.time() - start_time) * 1000, 1)
                
                if latency < 50:
                    st.success(f"🟢 **{target_region} Ping:** {latency} ms — **Tournament Ready** (Optimal connection)")
                elif latency <= 100:
                    st.warning(f"🟡 **{target_region} Ping:** {latency} ms — **Playable** (Minor latency detected)")
                else:
                    st.error(f"🔴 **{target_region} Ping:** {latency} ms — **Lag Prone** (High risk of packet loss)")
            except Exception:
                st.error("❌ Connection timed out or server unreachable.")

st.markdown("---")

# --- 10. ML MATCH PREDICTOR ---
st.subheader("🤖 ML Match Outcome Predictor")
st.caption("Predict match win probability based on simulated connection quality.")

ml_col1, ml_col2 = st.columns(2)

with ml_col1:
    input_ping = st.number_input("Enter Simulated Ping (ms)", min_value=5, max_value=300, value=45)
    input_dc = st.selectbox("Simulate Disconnect Issue?", ["No Disconnects (0)", "Disconnected (1)"])
    dc_value = 1 if "Disconnected (1)" in input_dc else 0

with ml_col2:
    if "ping_ms" in df.columns and "match_outcome" in df.columns:
        model_df = df.copy().dropna(subset=["ping_ms", "disconnected", "match_outcome"])
        model_df["win"] = model_df["match_outcome"].apply(lambda x: 1 if str(x).strip().lower() == "win" else 0)
        
        if len(model_df["win"].unique()) > 1:
            X = model_df[["ping_ms", "disconnected"]]
            y = model_df["win"]
            
            clf = LogisticRegression()
            clf.fit(X, y)
            
            prob_win = clf.predict_proba([[input_ping, dc_value]])[0][1] * 100
            
            st.markdown("#### **Prediction Results:**")
            st.progress(int(prob_win))
            
            if prob_win >= 60:
                st.success(f"🏆 **Estimated Win Probability:** {prob_win:.1f}% — Optimal connectivity favored.")
            elif prob_win >= 40:
                st.warning(f"⚠️ **Estimated Win Probability:** {prob_win:.1f}% — Moderate latency penalty.")
            else:
                st.error(f"🚨 **Estimated Win Probability:** {prob_win:.1f}% — High risk of defeat/forfeit due to severe lag.")
        else:
            st.info("Insufficient label distribution to train predictor model.")

st.markdown("---")

# --- 11. EXPORT & TELEMETRY EXPLORER ---
st.subheader("📋 Session Telemetry Explorer & Audit Report")

if not filtered_df.empty:
    cols_to_show = [c for c in ["session_id", "player_id", "username", "region", "ping_ms", "disconnected", "match_outcome"] if c in filtered_df.columns]
    table_df = filtered_df[cols_to_show].head(100)
    
    csv_data = filtered_df[cols_to_show].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Telemetry Audit (CSV)",
        data=csv_data,
        file_name="telemetry_audit_report.csv",
        mime="text/csv"
    )
    
    html_table = table_df.to_html(classes="esports-table", index=False)
    st.markdown(f'<div class="esports-table-container">{html_table}</div>', unsafe_allow_html=True)
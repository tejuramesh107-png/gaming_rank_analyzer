# 🎮 Gaming Rank & Server Latency Analyzer

An interactive telemetry control room built with **Streamlit**, **SQLite**, and **Pandas** designed to evaluate how regional server performance and network latency impact competitive esports match outcomes (*Valorant*, *CS2*).

---

## 🎯 Purpose & Analytical Focus

In competitive tactical shooters, milliseconds decide victory. This project analyzes real-time server telemetry data to answer a core analytical question:

> **❓ Main Analytical Question:**  
> *How do server region and network latency influence player connectivity, match outcomes, and overall competitive performance?*

### Key Analytical Objectives
* **Identify Network Bottlenecks:** Distinguish between player skill variations and network degradation (lag spikes, high ping, disconnects).
* **Evaluate Regional Server Clusters:** Track connectivity health across global server regions (EU, NA, APAC, LATAM, OCE).
* **Measure Outcome Impacts:** Visualize how latency thresholds ($>50\text{ ms}$ vs $>150\text{ ms}$) correlate with forfeits, wins, and losses.

---

## ⚡ Features & UI Architecture

* **High-Contrast Esports Dark Theme:** Built with glowing purple/cyan styling, custom neon metrics, and fully responsive dark telemetry tables.
* **Real-Time KPI Metrics:** Key connectivity indicators including *Average Ping*, *Total Active Sessions*, *Disconnect Rate*, and *Lag Spike Count ($>150\text{ ms}$)*.
* **Interactive Control Panel:** Filter server metrics dynamically by geographic region and ping thresholds using sidebar controls.
* **Visual Telemetry Analytics:** Seaborn & Matplotlib distributions mapping ping density curves alongside match outcome ratios.
* **In-App Educational Guide:** Integrated dialog window explaining network metrics (latency, packet drops, disconnect thresholds) for tactical FPS infrastructure.

---

## 🛠️ Tech Stack

* **Frontend Framework:** Streamlit
* **Database Management:** SQLite3
* **Data Manipulation:** Pandas
* **Data Visualization:** Matplotlib, Seaborn
* **Custom Styling:** HTML5 / CSS3 (Dark Theme Overlays)

---

## 🕹️ How to Run Locally

### 1. Clone the Repository
```bash
git clone [https://github.com/tejuramesh107-png/gaming_rank_analyzer.git](https://github.com/tejuramesh107-png/gaming_rank_analyzer.git)
cd gaming_rank_analyzer
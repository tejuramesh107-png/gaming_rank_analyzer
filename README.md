# 🎮 Gaming Telemetry & Server Latency Analyzer

## 🎯 Objective
Analyze gaming telemetry data to understand how server region and network latency affect a player's connectivity, match outcomes, and competitive performance.

## ❓ Main Analytical Question
> **How do server region and network latency influence player's connectivity, match outcomes, and competitive performance?**

---

## 🚀 Key Features
* **Global Regional Telemetry:** Filters telemetry across server clusters (NA, SA, EU, APAC, LATAM, ME, OCE).
* **Latency Isolation:** Interactive ping ranges to analyze smooth vs high-lag sessions (>150ms).
* **Connectivity Tracking:** Monitors disconnect rates and performance stability.
* **Match Outcome Analysis:** Correlates network lag against match win/loss ratios.

---

## 🛠️ Tech Stack
* **Python** (Pandas, Matplotlib, Seaborn)
* **SQLite3** (Relational Telemetry Database)
* **Streamlit** (Interactive Web Dashboard)
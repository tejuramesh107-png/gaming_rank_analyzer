import sqlite3
from faker import Faker
import numpy as np
import pandas as pd

fake = Faker()
np.random.seed(42)

# 1. Generate Players Data
n_players = 100
players_data = {
    "player_id": [f"P_{1000+i}" for i in range(n_players)],
    "username": [fake.user_name() for _ in range(n_players)],
    "region": np.random.choice(["NA", "EU", "APAC", "LATAM"], size=n_players),
    "join_date": [
        fake.date_between(start_date="-1y", end_date="today")
        for _ in range(n_players)
    ],
}
df_players = pd.DataFrame(players_data)

# 2. Generate Matches Data (with some missing outcomes)
n_matches = 500
matches_data = {
    "match_id": [f"M_{5000+i}" for i in range(n_matches)],
    "player_id": np.random.choice(df_players["player_id"], size=n_matches),
    "outcome": np.random.choice(
        ["Win", "Loss", "Draw", None], size=n_matches, p=[0.45, 0.45, 0.08, 0.02]
    ),
    "mmr_change": np.random.randint(-25, 30, size=n_matches),
    "timestamp": [
        fake.date_time_between(start_date="-30d", end_date="now")
        for _ in range(n_matches)
    ],
}
df_matches = pd.DataFrame(matches_data)

# 3. Generate Sessions Data (with outliers and missing logs)
sessions_data = {
    "session_id": [f"S_{9000+i}" for i in range(n_matches)],
    "player_id": df_matches["player_id"],
    "ping_ms": np.random.choice(
        [20, 45, 60, 150, 999, -5], size=n_matches, p=[0.5, 0.3, 0.1, 0.05, 0.03, 0.02]
    ),  # Includes outliers (-5, 999)
    "disconnected": np.random.choice(
        [0, 1], size=n_matches, p=[0.9, 0.1]
    ),
}
df_sessions = pd.DataFrame(sessions_data)

# Save to raw CSV files
df_players.to_csv("raw_players.csv", index=False)
df_matches.to_csv("raw_matches.csv", index=False)
df_sessions.to_csv("raw_sessions.csv", index=False)

print("Raw CSV files generated successfully!")
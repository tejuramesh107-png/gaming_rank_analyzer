import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
np.random.seed(42)

# 1. Generate Players Data
n_players = 100
players_data = {
    "player_id": [f"P_{1000+i}" for i in range(n_players)],
    "username": [fake.user_name() for _ in range(n_players)],
    "region": np.random.choice(["APAC", "LATAM", "EU", "NA", "SA"], size=n_players),
    "join_date": [fake.date_between(start_date="-1y", end_date="today") for _ in range(n_players)]
}
df_players = pd.DataFrame(players_data)
df_players.to_csv("raw_players.csv", index=False)

# 2. Generate Matches Data
n_matches = 500
matches_data = {
    "match_id": [f"M_{5000+i}" for i in range(n_matches)],
    "region": np.random.choice(["APAC", "LATAM", "EU", "NA", "SA"], size=n_matches),
    "match_outcome": np.random.choice(["Win", "Loss", "Forfeit", None], size=n_matches, p=[0.45, 0.45, 0.08, 0.02])
}
df_matches = pd.DataFrame(matches_data)
df_matches.to_csv("raw_matches.csv", index=False)

# 3. Generate Sessions Data
n_sessions = 1000
pings = np.concatenate([
    np.random.normal(loc=40, scale=15, size=950),
    np.random.uniform(low=200, high=1000, size=50)
])
pings = np.clip(pings, a_min=10, a_max=1000)

sessions_data = {
    "session_id": [f"S_{9000+i}" for i in range(n_sessions)],
    "player_id": np.random.choice(df_players["player_id"], size=n_sessions),
    "ping_ms": np.round(pings, 1),
    "disconnected": np.random.choice([0, 1], size=n_sessions, p=[0.92, 0.08])
}
df_sessions = pd.DataFrame(sessions_data)
df_sessions.to_csv("raw_sessions.csv", index=False)

print("Data successfully generated with NA and SA regions added!")
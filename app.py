# Database Connection
@st.cache_data
def load_data():
    conn = sqlite3.connect("gaming_data.db")
    
    # Query sessions merged with players
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
    
    # Fetch matches table
    matches_df = pd.read_sql_query("SELECT * FROM matches;", conn)
    conn.close()
    
    # Safely attach match outcomes without SQL join crashes
    outcome_col = "match_outcome" if "match_outcome" in matches_df.columns else "outcome"
    sessions_df["match_outcome"] = matches_df[outcome_col].reindex(sessions_df.index).values
    
    return sessions_df

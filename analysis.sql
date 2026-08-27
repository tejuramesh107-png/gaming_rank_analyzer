-- Query 1: Regional Leaderboards using DENSE_RANK()
SELECT 
    p.player_id,
    p.username,
    p.region,
    SUM(m.mmr_change) AS total_mmr,
    DENSE_RANK() OVER (PARTITION BY p.region ORDER BY SUM(m.mmr_change) DESC) AS regional_rank
FROM players p
JOIN matches m ON p.player_id = m.player_id
GROUP BY p.player_id, p.username, p.region;

-- Query 2: High-Ping Performance Impact
SELECT 
    p.region,
    ROUND(AVG(s.ping_ms), 2) AS avg_ping,
    COUNT(CASE WHEN m.outcome = 'Win' THEN 1 END) * 100.0 / COUNT(m.match_id) AS win_rate_percentage
FROM players p
JOIN matches m ON p.player_id = m.player_id
JOIN sessions s ON p.player_id = s.player_id
GROUP BY p.region;
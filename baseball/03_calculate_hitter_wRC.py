from sqlalchemy import create_engine, text

# DB 접속 설정
db_config = {
    'user': 'niscom',
    'password': 'niscom',
    'host': '116.37.91.221',
    'port': 3306,
    'database': 'baseball'
}

# SQLAlchemy 연결 문자열
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
                    f"{db_config['host']}:{db_config['port']}/{db_config['database']}")

select_league_runs_query = text("""
    SELECT (SUM(away_score) + SUM(home_score)) league_runs
    FROM game_schedule;
""")

select_league_pa_query = text("""
    SELECT SUM(pa) as league_pa
    FROM hitters;
""")

select_league_wOBA_query = text("""
    SELECT AVG(wOBA) as league_wOBA
    FROM hitter_metrics;
""")

select_league_OBP_query = text("""
    SELECT AVG(obp) as league_OBP
    FROM hitters;
""")

select_league_slg_query = text("""
    SELECT AVG(slg) as league_slg
    FROM hitters;
""")

select_league_games_query = text("""
    SELECT COUNT(*) AS league_games
    FROM game_schedule;
""")

select_hitter_wOBA_query = text("""
    SELECT hitter_id, wOBA
    FROM hitter_metrics;
""")

select_hitter_pa_query = text("""
    SELECT pa
    FROM hitters
    WHERE hitter_id = :hitter_id
""")

select_hitter_team_query = text("""
    SELECT team_name
    FROM hitters
    WHERE hitter_id = :hitter_id
""")

select_team_games_query = text("""
    SELECT COUNT(*) AS team_games
    FROM game_schedule
    WHERE away_team = :team_name OR home_team = :team_name
""")

with engine.connect() as conn:
    select_league_runs_result = conn.execute(select_league_runs_query)
    league_runs = int(select_league_runs_result.scalar())

    select_league_pa_result = conn.execute(select_league_pa_query)
    league_pa = int(select_league_pa_result.scalar())

    select_league_wOBA_result = conn.execute(select_league_wOBA_query)
    league_wOBA = float(select_league_wOBA_result.scalar())

    select_league_OBP_result = conn.execute(select_league_OBP_query)
    league_OBP = float(select_league_OBP_result.scalar())

    select_league_slg_result = conn.execute(select_league_slg_query)
    league_slg = float(select_league_slg_result.scalar())

    select_hitter_wOBA_results = conn.execute(select_hitter_wOBA_query)

    select_league_games_result = conn.execute(select_league_games_query)
    league_games = int(select_league_games_result.scalar())

upsert_hitter_wRC_query = text("""
    INSERT INTO hitter_metrics (hitter_id, wRC)
    VALUES (:hitter_id, :wRC)
    ON DUPLICATE KEY UPDATE wRC = VALUES(wRC);
""")

wOBA_scale = (league_wOBA - league_OBP) / (league_slg - league_OBP)

for row in select_hitter_wOBA_results:
    hitter_id, wOBA = row

    with engine.connect() as conn:
        select_hitter_pa_result = conn.execute(select_hitter_pa_query, {"hitter_id": hitter_id})
        pa = int(select_hitter_pa_result.scalar())

        select_hitter_team_result = conn.execute(select_hitter_team_query, {"hitter_id": hitter_id})
        team = select_hitter_team_result.fetchone()
        team = team[0]

        select_team_games_result = conn.execute(select_team_games_query, {"team_name": team})
        team_games = int(select_team_games_result.scalar())

    wRC = (((wOBA - league_wOBA) / wOBA_scale) * (league_pa / league_games) * team_games) + ((league_runs / league_games) * team_games)

    data = {"hitter_id": hitter_id, "wRC": wRC}
    with engine.begin() as conn:
        conn.execute(upsert_hitter_wRC_query, data)
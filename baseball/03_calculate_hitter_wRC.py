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

select_hitter_wOBA_query = text("""
    SELECT hitter_id, wOBA
    FROM hitter_metrics;
""")

select_hitter_pa_query = text("""
    SELECT pa
    FROM hitters
    WHERE hitter_id = :hitter_id
""")

with engine.connect() as conn:
    select_league_runs_result = conn.execute(select_league_runs_query)
    league_runs = int(select_league_runs_result.scalar())

    select_league_pa_result = conn.execute(select_league_pa_query)
    league_pa = int(select_league_pa_result.scalar())

    select_league_wOBA_result = conn.execute(select_league_wOBA_query)
    league_wOBA = float(select_league_wOBA_result.scalar())

    select_hitter_wOBA_results = conn.execute(select_hitter_wOBA_query)

upsert_hitter_wRC_query = text("""
    INSERT INTO hitter_metrics (hitter_id, wRC)
    VALUES (:hitter_id, :wRC)
    ON DUPLICATE KEY UPDATE wRC = VALUES(wRC);
""")

for row in select_hitter_wOBA_results:
    hitter_id, wOBA = row

    with engine.connect() as conn:
        select_hitter_pa_result = conn.execute(select_hitter_pa_query, {"hitter_id": hitter_id})
        pa = int(select_hitter_pa_result.scalar())
    wRC = (((wOBA - league_wOBA) / ((league_runs / league_pa) / league_wOBA)) + (league_runs / league_pa)) * pa

    data = {"hitter_id": hitter_id, "wRC": wRC}
    with engine.begin() as conn:
        conn.execute(upsert_hitter_wRC_query, data)
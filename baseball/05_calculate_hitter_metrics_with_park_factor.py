from sqlalchemy import create_engine, text
from collections import defaultdict

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

park_factor_dic = defaultdict(float)

select_park_factor_query = text("""
    SELECT stadium, park_factor
    FROM park_factor;
""")

with engine.connect() as conn:
    select_park_factor_results = conn.execute(select_park_factor_query)

for row in select_park_factor_results:
    stadium, park_factor = row
    park_factor_dic[stadium] = park_factor

select_league_runs_query = text("""
    SELECT (SUM(away_score) + SUM(home_score)) league_runs
    FROM game_schedule;
""")

select_league_wRC_query = text("""
    SELECT SUM(wRC) league_wRC
    FROM hitter_metrics;
""")

select_league_obp_query = text("""
    SELECT AVG(obp) league_obp
    FROM hitters;
""")

select_league_slg_query = text("""
    SELECT AVG(slg) league_slg
    FROM hitters;
""")

with engine.connect() as conn:
    select_league_runs_result = conn.execute(select_league_runs_query)
    league_runs = int(select_league_runs_result.scalar())

    select_league_wRC_result = conn.execute(select_league_wRC_query)
    league_wRC = float(select_league_wRC_result.scalar())

    select_league_obp_result = conn.execute(select_league_obp_query)
    league_obp = float(select_league_obp_result.scalar())

    select_league_slg_result = conn.execute(select_league_slg_query)
    league_slg = float(select_league_slg_result.scalar())

select_today_lineup_query = text("""
    SELECT player, team, position, stadium
    FROM today_lineup;
""")

with engine.connect() as conn:
    select_today_lineup_results = conn.execute(select_today_lineup_query)

select_hitter_id_query = text("""
    SELECT hitter_id
    FROM hitters
    WHERE player_name = :player AND team_name = :team
""")

select_hitter_wRC_query = text("""
    SELECT wRC
    FROM hitter_metrics
    WHERE hitter_id = :hitter_id
""")

select_hitter_obp_query = text("""
    SELECT obp
    FROM hitters
    WHERE hitter_id = :hitter_id
""")

select_hitter_slg_query = text("""
    SELECT slg
    FROM hitters
    WHERE hitter_id = :hitter_id
""")

upsert_hitter_metric_query = text("""
    INSERT INTO hitter_metrics (hitter_id, wRC_plus, OPS_plus)
    VALUES (:hitter_id, :wRC_plus, :OPS_plus)
    ON DUPLICATE KEY UPDATE
        wRC_plus = VALUES(wRC_plus),
        OPS_plus = VALUES(OPS_plus);
""")

for row in select_today_lineup_results:
    player, team, position, stadium = row
    # 타자일 경우
    if position != 0:
        with engine.connect() as conn:
            # hitter_id 가져오기
            select_hitter_id_result = conn.execute(select_hitter_id_query, {"player": player, "team": team})
            hitter_id = int(select_hitter_id_result.scalar())
            try:
                # 타자의 wRC 가져오기
                select_hitter_wRC_result = conn.execute(select_hitter_wRC_query, {"hitter_id": hitter_id})
                wRC = float(select_hitter_wRC_result.scalar())
                # 타자의 OPS 가져오기
                select_hitter_obp_result = conn.execute(select_hitter_obp_query, {"hitter_id": hitter_id})
                obp = float(select_hitter_obp_result.scalar())
                # 타자의 slg 가져오기
                select_hitter_slg_result = conn.execute(select_hitter_slg_query, {"hitter_id": hitter_id})
                slg = float(select_hitter_slg_result.scalar())
            except:
                continue
        # 파크팩터 가져오기
        park_factor = park_factor_dic[stadium]
        # wRC_plus 계산
        wRC_plus = ((wRC + ((1 - park_factor) * league_runs)) / league_wRC) * 100
        # OPS_plus 계산
        ops_plus = (100 / park_factor) * ((obp / league_obp) + (slg / league_slg) - 1)

        data = {
            "hitter_id": hitter_id,
            "wRC_plus": wRC_plus,
            "OPS_plus": ops_plus
        }

        with engine.begin() as conn:
            conn.execute(upsert_hitter_metric_query, data)
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

select_today_lineup_query = text("""
    SELECT game_date, player, team, position, opponent, stadium
    FROM today_lineup;
""")

select_hitter_stats_query = text("""
    SELECT hitter_id, avg, games, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, sac, sf, bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba
    FROM hitters
    WHERE player_name = :player AND team_name = :team
""")

select_hitter_metrics_query = text("""
    SELECT wOBA, wRC, wRC_plus, OPS_plus, k_rate, bb_rate, BABIP
    FROM hitter_metrics
    WHERE hitter_id = :hitter_id
""")

select_hitter_opponents_query = text("""
    SELECT games, avg, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, bb, hbp, so, gdp
    FROM hitter_opponents
    WHERE hitter_id = :hitter_id AND opponent_team = :opponent
""")

select_hitter_stadiums_query = text("""
    SELECT games, avg, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, bb, hbp, so, gdp
    FROM hitter_stadium
    WHERE hitter_id = :hitter_id AND stadium = :stadium
""")

with engine.connect() as conn:
    select_today_lineup_results = conn.execute(select_today_lineup_query)

for row in select_today_lineup_results:
    game_date, player, team, position, opponent, stadium = row
    # 타자일 경우
    if position != 0:
        with engine.connect() as conn:
            # hitters 테이블에서 정보 가져오기
            select_hitter_stats_result = conn.execute(select_hitter_stats_query, {"player": player, "team": team})
            hitter_id, avg, games, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, sac, sf, bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba = select_hitter_stats_result
            
            # hitter_metrics 테이블에서 정보 가져오기
            select_hitter_metrics_result = conn.execute(select_hitter_stats_query, {"hitter_id": hitter_id})
            wOBA, wRC, wRC_plus, OPS_plus, k_rate, bb_rate, babip = select_hitter_metrics_result

            # hitter_opponents 테이블에서 정보 가져오기
            select_hitter_opponents_result = conn.execute(select_hitter_opponents_query, {"hitter_id": hitter_id, "opponent": opponent})
            o_games, o_avg, o_pa, o_ab, o_runs, o_hits, o_doubles, o_triples, o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp = select_hitter_opponents_result

            # hitter_stadiums 테이블에서 정보 가져오기
            select_hitter_stadiums_result = conn.execute(select_hitter_stadiums_query, {"hitter_id": hitter_id, "stadium": stadium})
            s_games, s_avg, s_pa, s_ab, s_runs, s_hits, s_doubles, s_triples, s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp = select_hitter_stadiums_result

            # hitter_games 테이블에서 game_date를 기준으로 최근 10경기 데이터를 가져온 뒤 CSV 파일 형식으로 저장하여 해당 경로 DB에 저장
            
import os
import pandas as pd
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
    FROM hitter_stadiums
    WHERE hitter_id = :hitter_id AND stadium = :stadium
""")

select_hitter_recent_games_query = text("""
    SELECT game_date, opponent_team, avg, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, bb, hbp, so, gdp
    FROM hitter_games
    WHERE hitter_id = :hitter_id
    ORDER BY game_date DESC
    LIMIT 5;
""")

insert_hitter_records_query = text("""
    INSERT INTO hitter_records (
        hitter_id, player_name, team_name, game_date, position, avg, games, pa, ab, runs, hits,
        doubles, triples, hr, rbi, sb, cs, sac, sf, bb, ibb, hbp, so, gdp, slg, obp, errors,
        sb_percentage, mh, ops, risp, ph_ba, wOBA, wRC, wRC_plus, OPS_plus, k_rate, bb_rate, BABIP,
        opponent_team, opponent_games, opponent_avg, opponent_pa, opponent_ab, opponent_runs,
        opponent_hits, opponent_doubles, opponent_triples, opponent_hr, opponent_rbi, opponent_sb,
        opponent_cs, opponent_bb, opponent_hbp, opponent_so, opponent_gdp,
        stadium, stadium_games, stadium_avg, stadium_pa, stadium_ab, stadium_runs,
        stadium_hits, stadium_doubles, stadium_triples, stadium_hr, stadium_rbi,
        stadium_sb, stadium_cs, stadium_bb, stadium_hbp, stadium_so, stadium_gdp,
        recent_games_file_path
    )
    VALUES (
        :hitter_id, :player_name, :team_name, :game_date, :position, :avg, :games, :pa, :ab, :runs, :hits,
        :doubles, :triples, :hr, :rbi, :sb, :cs, :sac, :sf, :bb, :ibb, :hbp, :so, :gdp, :slg, :obp, :errors,
        :sb_percentage, :mh, :ops, :risp, :ph_ba, :wOBA, :wRC, :wRC_plus, :OPS_plus, :k_rate, :bb_rate, :BABIP,
        :opponent_team, :opponent_games, :opponent_avg, :opponent_pa, :opponent_ab, :opponent_runs,
        :opponent_hits, :opponent_doubles, :opponent_triples, :opponent_hr, :opponent_rbi, :opponent_sb,
        :opponent_cs, :opponent_bb, :opponent_hbp, :opponent_so, :opponent_gdp,
        :stadium, :stadium_games, :stadium_avg, :stadium_pa, :stadium_ab, :stadium_runs,
        :stadium_hits, :stadium_doubles, :stadium_triples, :stadium_hr, :stadium_rbi,
        :stadium_sb, :stadium_cs, :stadium_bb, :stadium_hbp, :stadium_so, :stadium_gdp,
        :recent_games_file_path
    )
""")

with engine.connect() as conn:
    select_today_lineup_results = conn.execute(select_today_lineup_query)

for row in select_today_lineup_results:
    game_date, player, team, position, opponent, stadium = row
    # 타자일 경우
    if position != 0:
        with engine.connect() as conn:
            # hitters 테이블에서 정보 가져오기
            select_hitter_stats_result = conn.execute(select_hitter_stats_query, {"player": player, "team": team}).fetchone()
            if select_hitter_stats_result is None:
                print(f"No stats found for player {player} from team {team}")
                continue
            hitter_id, avg, games, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, sac, sf, bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba = select_hitter_stats_result
            
            # hitter_metrics 테이블에서 정보 가져오기
            select_hitter_metrics_result = conn.execute(select_hitter_metrics_query, {"hitter_id": hitter_id}).fetchone()
            if select_hitter_metrics_result is None:
                print(f"No metrics found for hitter_id {hitter_id}")
                wOBA, wRC, wRC_plus, OPS_plus, k_rate, bb_rate, babip = None, None, None, None, None, None, None
            else:
                wOBA, wRC, wRC_plus, OPS_plus, k_rate, bb_rate, babip = select_hitter_metrics_result

            # hitter_opponents 테이블에서 정보 가져오기
            select_hitter_opponents_result = conn.execute(select_hitter_opponents_query, {"hitter_id": hitter_id, "opponent": opponent}).fetchone()
            if select_hitter_opponents_result is None:
                print(f"No opponent stats found for hitter_id {hitter_id} against {opponent}")
                o_games, o_avg, o_pa, o_ab, o_runs, o_hits, o_doubles, o_triples, o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
            else:
                o_games, o_avg, o_pa, o_ab, o_runs, o_hits, o_doubles, o_triples, o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp = select_hitter_opponents_result

            # hitter_stadiums 테이블에서 정보 가져오기
            select_hitter_stadiums_result = conn.execute(select_hitter_stadiums_query, {"hitter_id": hitter_id, "stadium": stadium}).fetchone()
            if select_hitter_stadiums_result is None:
                print(f"No stadium stats found for hitter_id {hitter_id} at {stadium}")
                s_games, s_avg, s_pa, s_ab, s_runs, s_hits, s_doubles, s_triples, s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
            else:
                s_games, s_avg, s_pa, s_ab, s_runs, s_hits, s_doubles, s_triples, s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp = select_hitter_stadiums_result

            # hitter_games 테이블에서 game_date를 기준으로 최근 10경기 데이터를 가져온 뒤 CSV 파일 형식으로 저장하여 해당 경로 DB에 저장
            select_hitter_recent_games_result = pd.read_sql(select_hitter_recent_games_query, conn, params={"hitter_id": hitter_id})
            output_path = f"{game_date}/{hitter_id}.csv"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            select_hitter_recent_games_result.to_csv(output_path, index=False)

            data = (hitter_id, player, team, game_date, position,
                    avg, games, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, sac, sf,
                    bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba,
                    wOBA, wRC, wRC_plus, OPS_plus, k_rate, bb_rate, babip,
                    opponent, o_games, o_avg, o_pa, o_ab, o_runs, o_hits, o_doubles, o_triples,
                    o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp,
                    stadium, s_games, s_avg, s_pa, s_ab, s_runs, s_hits, s_doubles, s_triples,
                    s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp, output_path)
            # 먼저 컬럼 리스트 정의
            columns = [
                "hitter_id", "player_name", "team_name", "game_date", "position",
                "avg", "games", "pa", "ab", "runs", "hits", "doubles", "triples", "hr", "rbi", "sb", "cs", "sac", "sf",
                "bb", "ibb", "hbp", "so", "gdp", "slg", "obp", "errors", "sb_percentage", "mh", "ops", "risp", "ph_ba",
                "wOBA", "wRC", "wRC_plus", "OPS_plus", "k_rate", "bb_rate", "BABIP",
                "opponent_team", "opponent_games", "opponent_avg", "opponent_pa", "opponent_ab", "opponent_runs",
                "opponent_hits", "opponent_doubles", "opponent_triples", "opponent_hr", "opponent_rbi", "opponent_sb",
                "opponent_cs", "opponent_bb", "opponent_hbp", "opponent_so", "opponent_gdp",
                "stadium", "stadium_games", "stadium_avg", "stadium_pa", "stadium_ab", "stadium_runs",
                "stadium_hits", "stadium_doubles", "stadium_triples", "stadium_hr", "stadium_rbi",
                "stadium_sb", "stadium_cs", "stadium_bb", "stadium_hbp", "stadium_so", "stadium_gdp",
                "recent_games_file_path"
            ]

            # 컬럼과 값을 매핑하여 dict 생성
            data_dict = dict(zip(columns, data))

            conn.execute(insert_hitter_records_query, data_dict)
            conn.commit()


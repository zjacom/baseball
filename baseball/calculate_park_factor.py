import pandas as pd
import pandasql as ps
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

# park_factor 테이블 삭제 쿼리
drop_table_qeury = text("""
DROP TABLE IF EXISTS park_factor;
""")

# park_factor 테이블 생성 쿼리
create_table_query = text("""
CREATE TABLE IF NOT EXISTS park_factor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stadium VARCHAR(50) NOT NULL,
    park_factor FLOAT NOT NULL
);
""")

# 트랜잭션 불필요 - connect()
with engine.connect() as conn:
    conn.execute(drop_table_qeury)
    conn.execute(create_table_query)

# game_schedule 데이터 읽기
df = pd.read_sql("SELECT * FROM game_schedule", engine)

stats_case_by_stadium = df.groupby('stadium').agg(
    scored=('home_score', 'sum'),
    allowed_score=('away_score', 'sum'),
    games=('id', 'count')
).reset_index()

for _, row in stats_case_by_stadium.iterrows():
    cur_stadium = row["stadium"]
    cur_scored = row["scored"]
    cur_allowd_score = row["allowed_score"]
    cur_games = row["games"]

    # SQL 쿼리 작성
    query = f"""
    SELECT
        SUM(get_scored) AS home_score_sum,
        SUM(allow_scored) AS away_score_sum,
        SUM(games) AS game_count
    FROM stats_case_by_stadium
    WHERE stadium != '{cur_stadium}'
    """

    # SQL 실행
    result = ps.sqldf(query, locals())

    # 결과를 파이썬 변수에 저장
    other_scored = result.at[0, 'home_score_sum']
    other_allowed_score = result.at[0, 'away_score_sum']
    other_games = result.at[0, 'game_count']

    park_factor = ((cur_scored + cur_allowd_score) / cur_games) / ((other_scored + other_allowed_score) / other_games)
    
    insert_query = text("""
        INSERT INTO park_factor (stadium, park_factor)
        VALUES (:stadium, :park_factor);
    """)

    # 트랜잭션 필요 - begin()
    with engine.begin() as conn:
        conn.execute(insert_query, {"stadium": cur_stadium, "park_factor": park_factor})
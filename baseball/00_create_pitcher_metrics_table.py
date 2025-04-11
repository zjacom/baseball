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

create_table_query = text("""
    CREATE TABLE pitcher_metrics (
    pitcher_id INT PRIMARY KEY,
    FIP FLOAT,
    k_rate FLOAT,
    bb_rate FLOAT,
    hr_rate FLOAT
);
""")

with engine.connect() as conn:
    conn.execute(create_table_query)
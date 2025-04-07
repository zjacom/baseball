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

select_hitter_details_query = text("""
    SELECT hitter_id, bb, ibb, hbp, hits, doubles, triples, hr, sb, cs, pa, sac
    FROM hitters;
""")

with engine.connect() as conn:
    results = conn.execute(select_hitter_details_query)

upsert_hitter_wOBA_query = text("""
    INSERT INTO hitter_metrics (hitter_id, wOBA)
    VALUES (:hitter_id, :wOBA)
    ON DUPLICATE KEY UPDATE wOBA = VALUES(wOBA);
""")

for row in results:
    hitter_id, bb, ibb, hbp, hits, doubles, triples, hr, sb, cs, pa, sac = row
    if (pa - ibb - sac) == 0:
        continue
    wOBA = ((0.7 * (bb + ibb + hbp)) + (0.9 * hits) + (1.25 * doubles) + (1.6 * triples) + (2 * hr) + (0.25 * sb) - (0.5 * cs)) / (pa - ibb - sac)
    data = {"hitter_id": hitter_id, "wOBA": wOBA}
    with engine.begin() as conn:
        conn.execute(upsert_hitter_wOBA_query, data)
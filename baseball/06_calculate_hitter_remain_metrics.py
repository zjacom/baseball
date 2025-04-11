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

select_hitter_stats_query = text("""
    SELECT hitter_id, so, bb, pa, hits, hr, ab, sf, ops
    FROM hitters;
""")

with engine.connect() as conn:
    select_hitter_stats_results = conn.execute(select_hitter_stats_query)

upsert_hitter_remain_metrics_query = text("""
    INSERT INTO hitter_metrics (hitter_id, OPS, k_rate, bb_rate, BABIP)
    VALUES (:hitter_id, :OPS, :k_rate, :bb_rate, :BABIP)
    ON DUPLICATE KEY UPDATE
        OPS = VALUES(OPS),
        k_rate = VALUES(k_rate),
        bb_rate = VALUES(bb_rate),
        BABIP = VALUES(BABIP);
""")

for row in select_hitter_stats_results:
    hitter_id, so, bb, pa, hits, hr, ab, sf, ops = row
    if pa == 0:
        continue
    if int(ab) - int(so) - int(hr) + int(sf) == 0:
        continue
    k_rate = int(so) / int(pa)
    bb_rate = int(bb) / int(pa)
    babip = ((int(hits) - int(hr)) / (int(ab) - int(so) - int(hr) + int(sf)))

    data = {"hitter_id": hitter_id, "OPS": ops, "k_rate": k_rate, "bb_rate": bb_rate, "BABIP": babip}
    with engine.begin() as conn:
        conn.execute(upsert_hitter_remain_metrics_query, data)
from sqlalchemy import create_engine, text

import re

def convert_pitcher_ip_to_float(ip_str):
    ip_str = ip_str.strip()
    
    if " " in ip_str:
        # "정수 분수" 형태
        whole, frac = ip_str.split()
        numerator, denominator = frac.split("/")
        return int(whole) + int(numerator) / int(denominator)
    elif "/" in ip_str:
        # "분수" 형태
        numerator, denominator = ip_str.split("/")
        return int(numerator) / int(denominator)
    else:
        # 그냥 정수
        return float(ip_str)


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

select_league_pitcher_metrics_query = text("""
    SELECT SUM(hr) as league_hr, SUM(bb) as league_bb, SUM(so) as league_so, SUM(ip) as league_ip, AVG(era) as league_era
    FROM pitchers;
""")

select_pitcher_stats_query = text("""
    SELECT pitcher_id, hr, bb, so, ip, era
    FROM pitchers;
""")

with engine.connect() as conn:
    select_pitcher_stats_results = list(conn.execute(select_pitcher_stats_query))

league_hr = 0
league_bb = 0
league_so = 0
league_ip = 0
league_era = 0

error_count = 0

for row in select_pitcher_stats_results:
    pitcher_id, hr, bb, so, ip_str, era = row
    ip = convert_pitcher_ip_to_float(ip_str)
    league_hr += int(hr)
    league_bb += int(bb)
    league_so += int(so)
    league_ip += ip
    try:
        league_era += float(era)
    except:
        error_count += 1
        print(f"스탯 오류 발생!: {pitcher_id}")
        continue
league_era = league_era / (len(select_pitcher_stats_results) - error_count)

fip_constant = league_era - (((13 * league_hr) + (3 * league_bb) - (2 * league_so)) / league_ip)

upsert_pitcher_metrics_query = text("""
    INSERT INTO pitcher_metrics (pitcher_id, FIP, k_rate, bb_rate, hr_rate)
    VALUES (:pitcher_id, :FIP, :k_rate, :bb_rate, :hr_rate)
    ON DUPLICATE KEY UPDATE
        FIP = VALUES(FIP),
        k_rate = VALUES(k_rate),
        bb_rate = VALUES(bb_rate),
        hr_rate = VALUES(hr_rate);
""")

for row in select_pitcher_stats_results:
    pitcher_id, hr, bb, so, ip_str, _ = row
    ip = convert_pitcher_ip_to_float(ip_str)
    if ip == 0:
        continue
    fip = (((13 * int(hr)) + (3 * int(bb)) - (2 * int(so))) / ip) + fip_constant
    k_rate = (int(so) * 9) / ip
    bb_rate = (int(bb) * 9) / ip
    hr_rate = (int(hr) * 9) / ip

    data = {"pitcher_id": pitcher_id, "FIP": fip, "k_rate": k_rate, "bb_rate": bb_rate, "hr_rate": hr_rate}
    with engine.begin() as conn:
        conn.execute(upsert_pitcher_metrics_query, data)
import mysql.connector

# MySQL 연결 설정
db_config = {
    "host": "116.37.91.221",
    "user": "niscom",
    "password": "niscom",
    "database": "baseball",
}

# MySQL 연결 생성
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

# 테이블 삭제
delete_table_query = "DROP TABLE IF EXISTS hitters;"
cursor.execute(delete_table_query)
print("hitters 테이블이 삭제되었습니다.")

# 테이블 생성
create_table_query = """
CREATE TABLE hitters (
    hitter_id INT PRIMARY KEY COMMENT '타자 고유 ID',
    player_name VARCHAR(50) COMMENT '선수 이름',
    team_name VARCHAR(50) COMMENT '소속 팀 이름',
    avg DECIMAL(5, 3) COMMENT '타율',
    games INT COMMENT '경기 수',
    pa INT COMMENT '타석',
    ab INT COMMENT '타수',
    runs INT COMMENT '득점',
    hits INT COMMENT '안타',
    doubles INT COMMENT '2루타',
    triples INT COMMENT '3루타',
    hr INT COMMENT '홈런',
    rbi INT COMMENT '타점',
    sb INT COMMENT '도루',
    cs INT COMMENT '도루 실패',
    sac INT COMMENT '희생 번트',
    sf INT COMMENT '희생 플라이',
    bb INT COMMENT '볼넷',
    ibb INT COMMENT '고의 4구',
    hbp INT COMMENT '몸에 맞는 공',
    so INT COMMENT '삼진',
    gdp INT COMMENT '병살타',
    slg DECIMAL(5, 3) COMMENT '장타율',
    obp DECIMAL(5, 3) COMMENT '출루율',
    errors INT COMMENT '실책',
    sb_percentage DECIMAL(5, 3) COMMENT '도루 성공률',
    mh INT COMMENT '멀티 히트',
    ops DECIMAL(5, 3) COMMENT '출루율 + 장타율',
    risp DECIMAL(5, 3) COMMENT '득점권 타율',
    ph_ba DECIMAL(5, 3) COMMENT '대타 타율',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '데이터 생성 시각',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '데이터 수정 시각'
) COMMENT = '타자 기본 기록 통계 테이블';
"""
cursor.execute(create_table_query)
print("hitters 테이블이 생성되었습니다.")

# 테이블 삭제
delete_table_query = "DROP TABLE IF EXISTS hitter_games;"
cursor.execute(delete_table_query)
print("hitter_games 테이블이 삭제되었습니다.")

# 테이블 생성
create_table_query = """
CREATE TABLE hitter_games (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '게임별 고유 ID',
    hitter_id INT NOT NULL COMMENT '타자 고유 ID (hitters 테이블의 외래키)',
    game_date DATE NOT NULL COMMENT '경기 날짜',
    opponent_team VARCHAR(50) COMMENT '상대 팀 이름',
    avg DECIMAL(5, 3) COMMENT '타율',
    pa INT COMMENT '타석',
    ab INT COMMENT '타수',
    runs INT COMMENT '득점',
    hits INT COMMENT '안타 수',
    doubles INT COMMENT '2루타',
    triples INT COMMENT '3루타',
    hr INT COMMENT '홈런',
    rbi INT COMMENT '타점',
    sb INT COMMENT '도루 성공',
    cs INT COMMENT '도루 실패',
    bb INT COMMENT '볼넷',
    hbp INT COMMENT '몸에 맞는 공',
    so INT COMMENT '삼진',
    gdp INT COMMENT '병살타',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 저장 시각',
    UNIQUE KEY unique_hitter_game (hitter_id, game_date)  -- UNIQUE 제약 추가
) COMMENT = '경기별 타자 성적 테이블';
"""
cursor.execute(create_table_query)
print("hitter_games 테이블이 생성되었습니다.")

# 테이블 삭제
delete_table_query = "DROP TABLE IF EXISTS hitter_opponents;"
cursor.execute(delete_table_query)
print("hitter_opponents 테이블이 삭제되었습니다.")

# 테이블 생성
create_table_query = """
CREATE TABLE hitter_opponents (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '상대별 고유 ID',
    hitter_id INT NOT NULL COMMENT '타자 고유 ID (hitters 테이블의 외래키)',
    opponent_team VARCHAR(50) COMMENT '상대 팀 이름',
    games INT COMMENT '경기수',
    avg DECIMAL(5, 3) COMMENT '타율',
    pa INT COMMENT '타석',
    ab INT COMMENT '타수',
    runs INT COMMENT '득점',
    hits INT COMMENT '안타 수',
    doubles INT COMMENT '2루타',
    triples INT COMMENT '3루타',
    hr INT COMMENT '홈런',
    rbi INT COMMENT '타점',
    sb INT COMMENT '도루 성공',
    cs INT COMMENT '도루 실패',
    bb INT COMMENT '볼넷',
    hbp INT COMMENT '몸에 맞는 공',
    so INT COMMENT '삼진',
    gdp INT COMMENT '병살타',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 저장 시각',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 업데이트 시각',
    UNIQUE KEY unique_hitter_opponent (hitter_id, opponent_team)  -- UNIQUE 제약 추가
) COMMENT = '상대별 타자 성적 테이블';
"""
cursor.execute(create_table_query)
print("hitter_opponents 테이블이 생성되었습니다.")

# 테이블 삭제
delete_table_query = "DROP TABLE IF EXISTS hitter_stadiums;"
cursor.execute(delete_table_query)
print("hitter_stadiums 테이블이 삭제되었습니다.")

# 테이블 생성
create_table_query = """
CREATE TABLE hitter_stadiums (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '구장별 고유 ID',
    hitter_id INT NOT NULL COMMENT '타자 고유 ID (hitters 테이블의 외래키)',
    stadium VARCHAR(50) COMMENT '구장',
    games INT COMMENT '경기수',
    avg DECIMAL(5, 3) COMMENT '타율',
    pa INT COMMENT '타석',
    ab INT COMMENT '타수',
    runs INT COMMENT '득점',
    hits INT COMMENT '안타 수',
    doubles INT COMMENT '2루타',
    triples INT COMMENT '3루타',
    hr INT COMMENT '홈런',
    rbi INT COMMENT '타점',
    sb INT COMMENT '도루 성공',
    cs INT COMMENT '도루 실패',
    bb INT COMMENT '볼넷',
    hbp INT COMMENT '몸에 맞는 공',
    so INT COMMENT '삼진',
    gdp INT COMMENT '병살타',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 저장 시각',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 업데이트 시각',
    UNIQUE KEY unique_hitter_stadium (hitter_id, stadium)  -- UNIQUE 제약 추가
) COMMENT = '구장별 타자 성적 테이블';
"""
cursor.execute(create_table_query)
print("hitter_stadiums 테이블이 생성되었습니다.")

# 테이블 삭제
delete_table_query = "DROP TABLE IF EXISTS hitter_situations;"
cursor.execute(delete_table_query)
print("hitter_situations 테이블이 삭제되었습니다.")

# 테이블 생성
create_table_query = """
CREATE TABLE hitter_situations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '상황별 고유 ID',
    hitter_id INT NOT NULL COMMENT '타자 고유 ID (hitters 테이블의 외래키)',
    situation VARCHAR(50) COMMENT '상황',
    avg DECIMAL(5, 3) COMMENT '타율',
    ab INT COMMENT '타수',
    hits INT COMMENT '안타 수',
    doubles INT COMMENT '2루타',
    triples INT COMMENT '3루타',
    hr INT COMMENT '홈런',
    rbi INT COMMENT '타점',
    bb INT COMMENT '볼넷',
    hbp INT COMMENT '몸에 맞는 공',
    so INT COMMENT '삼진',
    gdp INT COMMENT '병살타',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 저장 시각',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '기록 업데이트 시각',
    UNIQUE KEY unique_hitter_situation (hitter_id, situation)  -- UNIQUE 제약 추가
) COMMENT = '상황별 타자 성적 테이블';
"""
cursor.execute(create_table_query)
print("hitter_situations 테이블이 생성되었습니다.")
# CREATE TABLE game_schedule (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     game_date DATETIME NOT NULL,
#     away_team VARCHAR(50) NOT NULL,
#     away_score INT NOT NULL, 
#     home_team VARCHAR(50) NOT NULL,
#     home_score INT NOT NULL,
#     stadium VARCHAR(50) NOT NULL,
#     UNIQUE KEY unique_game (game_date, away_team)  -- ✅ UNIQUE 제약 조건 추가
# );

# 연결 종료
cursor.close()
connection.close()

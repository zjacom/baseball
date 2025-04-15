from sqlalchemy.ext.asyncio import create_async_engine

def create_async_sqlalchemy_engine(db_config):
    # DB 접속 설정
    db_config = {
        'user': 'niscom',
        'password': 'niscom',
        'host': '116.37.91.221',
        'port': 3306,
        'database': 'baseball'
    }

    # 비동기 SQLAlchemy 연결 문자열 (asyncmy 드라이버 사용)
    engine = create_async_engine(
        f"mysql+asyncmy://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}",
        echo=True  # 디버깅용 쿼리 출력 (필요 없으면 제거)
    )

    return engine

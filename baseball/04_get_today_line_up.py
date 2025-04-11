import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple, Optional
from datetime import datetime
import re

import mysql.connector
from mysql.connector import pooling
from playwright.async_api import async_playwright, Page

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 풀 설정
class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="baseball_pool",
            pool_size=5,
            pool_reset_session=True,
            host=host,
            user=user,
            password=password,
            database=database
        )

    @asynccontextmanager
    async def get_connection(self):
        conn = self.connection_pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    async def execute_upsert(self, query: str, data: Tuple):
        async with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, data)
                conn.commit()
                # logger.info("데이터 삽입/업데이트 성공")
            except mysql.connector.Error as err:
                logger.error(f"데이터베이스 오류: {err}")
                raise
            finally:
                cursor.close()

class BaseballDataScraper:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.count = 0

    def parse_bundle(self, game_result: str):
        match = re.match(r"(\D+)(\d+)vs(\d+)(\D+)", game_result)
        if match:
            away_team, away_score, home_score, home_team = match.groups()
            return (
                away_team.strip(),
                int(away_score),
                home_team.strip(),
                int(home_score)
            )
        return None  # 매칭 실패 시 None 반환
    
    def parse_game_datetime(self, date_str: str):
        # 1. 정규식으로 한글 요일 제거 (예: (토) → "")
        date_str = re.sub(r"\([가-힣]\)", "", date_str)

        # 2. 문자열을 datetime 객체로 변환
        date_obj = datetime.strptime(date_str, "%m.%d%H:%M")

        # 3. 연도 추가 (예: 2024년 기준)
        formatted_date = date_obj.replace(year=2025)

        return formatted_date.strftime("%Y-%m-%d %H:%M:%S")

    def _get_upsert_query(self, table_name: str) -> str:
        """각 테이블별 upsert 쿼리를 반환하는 메서드"""
        queries = {
            "game_schedule": """
            INSERT INTO game_schedule (
                game_date, away_team, away_score, home_team, home_score, stadium
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                away_score = VALUES(away_score),
                home_team = VALUES(home_team),
                home_score = VALUES(home_score),
                stadium = VALUES(stadium)
            """
        }
        return queries.get(table_name, "")

    async def upsert_data(self, table_name: str, data: Tuple):
        """데이터 삽입/업데이트 메서드"""
        query = self._get_upsert_query(table_name)
        await self.db_manager.execute_upsert(query, data)

    async def goto_with_retry(self, page: Page, url: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                await page.goto(url, wait_until="load", timeout=30000)  # 30초 타임아웃 설정
                return True
            except Exception as e:
                if attempt == max_retries - 1:  # 마지막 시도였다면
                    logger.error(f"페이지 로드 실패 (최종 실패): {url}, 오류: {e}")
                    raise  # 마지막 시도에서도 실패하면 예외를 발생시킴
                logger.warning(f"페이지 로드 실패 (재시도 {attempt + 1}/{max_retries}): {url}, 오류: {e}")
                await asyncio.sleep(2)  # 재시도 전 2초 대기

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            url = "https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx"
            await self.goto_with_retry(page, url)

            # 각 li에 대해 개별적으로 XPath를 사용하여 찾고 클릭
            ul_xpath = '//*[@id="contents"]/div[3]/div/div[1]/ul'

            # 먼저 li 요소 개수를 확인
            ul = await page.query_selector(f'xpath={ul_xpath}')
            li_elements = await ul.query_selector_all('li[class*="game-cont"]')
            li_count = len(li_elements)
            print(li_count)
            
            for i in range(1, li_count + 1):  # XPath에서는 인덱스가 1부터 시작
                # 매번 새롭게 특정 인덱스의 li 요소를 찾음
                li_xpath = f'{ul_xpath}/li[{i}]'
                try:
                    # 명시적으로 대기한 후 요소 찾기
                    li = await page.wait_for_selector(f'xpath={li_xpath}', timeout=5000)
                    if li:
                        await li.click()
                except Exception as e:
                    print(f"{i}번째 요소를 찾거나 클릭하는 중 오류 발생: {e}")
                
                stadium_element = await page.wait_for_selector(f'//*[@id="contents"]/div[3]/div/div[1]/ul/li[{i}]/div[1]/ul/li[1]')
                game_time_element = await page.wait_for_selector(f'//*[@id="contents"]/div[3]/div/div[1]/ul/li[{i}]/div[1]/ul/li[3]')
                
                stadium = await stadium_element.text_content()
                game_time = await game_time_element.text_content()
                print(stadium, game_time)
            await browser.close()

async def main():
    db_config = {
        "host": "116.37.91.221",
        "user": "niscom",
        "password": "niscom",
        "database": "baseball",
    }

    db_manager = DatabaseManager(**db_config)
    scraper = BaseballDataScraper(db_manager)
    
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
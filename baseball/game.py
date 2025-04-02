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

    async def process_player_data(self, page: Page):
        # 상대별 기록 처리
        url = f"https://www.koreabaseball.com/Schedule/Schedule.aspx"
        await self.goto_with_retry(page, url)
        await page.select_option('//*[@id="ddlMonth"]', "03")
        await asyncio.sleep(5)
        game_schedule = page.locator('//*[@id="tblScheduleList"]/tbody')
        game_schedule_elements = game_schedule.locator('tr')

        for i in range(await game_schedule_elements.count()):
            tr_row = game_schedule_elements.nth(i)
            td_elements = tr_row.locator('td')
            td_count = await td_elements.count()

            if td_count == 9:
                date = await td_elements.nth(0).inner_text()
                time = await td_elements.nth(1).inner_text()
                bundle = await td_elements.nth(2).inner_text()
                parsed_bundle = self.parse_bundle(bundle)
                if parsed_bundle is None:
                    continue
                else:
                    away_team, away_score, home_team, home_score = parsed_bundle
                stadium = await td_elements.nth(7).inner_text()
                timestamp = self.parse_game_datetime(date + time)
                await self.upsert_data("game_schedule", (timestamp, away_team, away_score, home_team, home_score, stadium))
            elif td_count == 8:
                time = await td_elements.nth(0).inner_text()
                bundle = await td_elements.nth(1).inner_text()
                parsed_bundle = self.parse_bundle(bundle)
                if parsed_bundle is None:
                    continue
                else:
                    away_team, away_score, home_team, home_score = parsed_bundle
                stadium = await td_elements.nth(6).inner_text()
                timestamp = self.parse_game_datetime(date + time)
                await self.upsert_data("game_schedule", (timestamp, away_team, away_score, home_team, home_score, stadium))

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await self.process_player_data(page)
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
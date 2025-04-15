import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple, Optional
from datetime import datetime

import mysql.connector
from mysql.connector import pooling
from playwright.async_api import async_playwright, Page

from utils.get_query import get_query

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

    def str_to_float(self, str):
        if str == "-":
            return None
        return float(str)

    async def upsert_data(self, table_name: str, data: Tuple):
        """데이터 삽입/업데이트 메서드"""
        query = get_query(table_name)
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

    async def check_player(self, page: Page, player_id: int) -> bool:
        url = f"https://www.koreabaseball.com/Record/Player/PitcherDetail/Basic.aspx?playerId={player_id}"
        await self.goto_with_retry(page, url)
        
        try:
            image_element = await page.locator('//*[@id="cphContents_cphContents_cphContents_playerProfile_imgProgile"]').get_attribute('src')
            if "no-Image" in image_element:
                return False
            else:
                return True
        except Exception as e:
            logger.warning(f"플레이어 {player_id} 확인 중 오류: {e}")
            return False

    async def process_player_data(self, page: Page, player_id: int):
        is_record = await page.locator('//*[@id="contents"]/div[2]/div[2]/div[2]/table/tbody/tr/td').count()
        if is_record == 1:
            return

        self.count += 1
        player_name = await page.locator('//*[@id="cphContents_cphContents_cphContents_playerProfile_lblName"]').text_content()
        player_name = player_name.strip()

        # 기본 정보 추출
        first_row = page.locator('//*[@id="contents"]/div[2]/div[2]/div[2]/table/tbody/tr').first
        first_td_elements = first_row.locator('td')
        first_td_values = []
        for i in range(await first_td_elements.count()):
            text = await first_td_elements.nth(i).text_content()
            first_td_values.append((text or "").strip())
        
        team_name, era, games, cg, sho, wins, loses, sv, hld, wpct, tbf, np, ip, hits, doubles, triples, hr = first_td_values
        team_name, era, games, cg, sho, wins, loses, sv, hld, wpct, tbf, np, hits, doubles, triples, hr = (
            team_name.strip(), self.str_to_float(era), int(games), int(cg), int(sho), int(wins), int(loses), 
            int(sv), int(hld), self.str_to_float(wpct), int(tbf), int(np), int(hits), int(doubles), int(triples), int(hr)
        )

        # 추가 정보 추출
        second_row = page.locator('//*[@id="contents"]/div[2]/div[2]/div[3]/table/tbody/tr').first
        second_td_elements = second_row.locator('td')
        second_td_values = []
        for i in range(await second_td_elements.count()):
            text = await second_td_elements.nth(i).text_content()
            second_td_values.append((text or "").strip())
        
        sac, sf, bb, ibb, so, wp, bk, runs, er, bsv, whip, avg, qs = second_td_values
        sac, sf, bb, ibb, so, wp, bk, runs, er, bsv, whip, avg, qs = (
            int(sac), int(sf), int(bb), int(ibb), int(so), int(wp), int(bk), 
            int(runs), int(er), int(bsv),
            self.str_to_float(whip), self.str_to_float(avg), int(qs)
        )

        # pitchers 테이블에 데이터 삽입
        data = (player_id, player_name, team_name, era, games, cg, sho, wins, loses, sv, hld, wpct, tbf, np, ip, hits, doubles, triples, hr, 
                sac, sf, bb, ibb, so, wp, bk, runs, er, bsv, whip, avg, qs)
        await self.upsert_data("pitchers", data)

        # 최근 10경기 데이터 처리
        recent_10_games = page.locator('//*[@id="contents"]/div[2]/div[2]/div[4]/table/tbody').first
        recent_tr_elements = recent_10_games.locator('tr')
        for i in range(await recent_tr_elements.count()):
            recent_row = recent_tr_elements.nth(i)
            recent_td_elements = recent_row.locator('td')
            recent_td_count = await recent_td_elements.count()

            recent_td_values = []
            for j in range(recent_td_count):
                recent_text = await recent_td_elements.nth(j).text_content()
                recent_td_values.append((recent_text or "").strip())
            
            r_date, r_opponent, r_result, r_era, r_tbf, r_ip, r_hits, r_hr, r_bb, r_hbp, r_so, r_runs, r_er, r_avg = recent_td_values
            
            # r_date 문자열 변환
            current_year = datetime.now().year
            r_date = f"{current_year}-{r_date.replace('.', '-')}"
            r_opponent = r_opponent.strip()
            r_result = r_result.strip()
            if not r_result:
                r_result = None
            r_era, r_tbf, r_hits, r_hr, r_bb, r_hbp, r_so, r_runs, r_er, r_avg = (
                self.str_to_float(r_era), int(r_tbf), int(r_hits), int(r_hr),
                int(r_bb), int(r_hbp), int(r_so), int(r_runs), int(r_er), self.str_to_float(r_avg)  
            )

            # 일자별 기록 테이블에 데이터 삽입
            data = (player_id, r_date, r_opponent, r_result, r_era, r_tbf, r_ip,
                    r_hits, r_hr, r_bb, r_hbp, r_so, r_runs, r_er, r_avg)
            await self.upsert_data("pitcher_games", data)

        # 상대별 기록 처리
        url = f"https://www.koreabaseball.com/Record/Player/PitcherDetail/Game.aspx?playerId={player_id}"
        await self.goto_with_retry(page, url)

        case_by_opponent = page.locator('//*[@id="contents"]/div[2]/div[2]/div[1]/table/tbody')
        cbo_tr_elements = case_by_opponent.locator('tr')
        for i in range(await cbo_tr_elements.count()):
            cbo_row = cbo_tr_elements.nth(i)
            cbo_td_elements = cbo_row.locator('td')
            cbo_td_count = await cbo_td_elements.count()

            cbo_td_values = []
            for j in range(cbo_td_count):
                cbo_text = await cbo_td_elements.nth(j).text_content()
                cbo_td_values.append((cbo_text or "").strip())
            
            o_opponent, o_games, o_era, o_wins, o_loses, o_sv, o_hld, o_wpct, o_tbf, o_ip, o_hits, o_hr, o_bb, o_hbp, o_so, o_runs, o_er, o_avg = cbo_td_values
            o_opponent, o_games, o_era, o_wins, o_loses, o_sv, o_hld, o_wpct, o_tbf, o_hits, o_hr, o_bb, o_hbp, o_so, o_runs, o_er, o_avg = (
                o_opponent.strip(), int(o_games), self.str_to_float(o_era), int(o_wins), int(o_loses), int(o_sv), int(o_hld),
                self.str_to_float(o_wpct), int(o_tbf), int(o_hits), int(o_hr), int(o_bb), int(o_hbp), int(o_so), int(o_runs), int(o_er),
                self.str_to_float(o_avg)
            )

            # 상대별 테이블
            data = (player_id, o_opponent, o_games, o_era, o_wins, o_loses, o_sv, o_hld, o_wpct,
                    o_tbf, o_ip, o_hits, o_hr, o_bb, o_hbp, o_so, o_runs, o_er, o_avg)
            await self.upsert_data("pitcher_opponents", data)

        # 구장별 기록 처리
        case_by_stadium = page.locator('//*[@id="contents"]/div[2]/div[2]/div[2]/table/tbody')
        cbs_tr_elements = case_by_stadium.locator('tr')
        for i in range(await cbs_tr_elements.count()):
            cbs_row = cbs_tr_elements.nth(i)
            cbs_td_elements = cbs_row.locator('td')
            cbs_td_count = await cbs_td_elements.count()

            cbs_td_values = []
            for j in range(cbs_td_count):
                cbs_text = await cbs_td_elements.nth(j).text_content()
                cbs_td_values.append((cbs_text or "").strip())
            
            s_stadium, s_games, s_era, s_wins, s_loses, s_sv, s_hld, s_wpct, s_tbf, s_ip, s_hits, s_hr, s_bb, s_hbp, s_so, s_runs, s_er, s_avg = cbs_td_values
            s_stadium, s_games, s_era, s_wins, s_loses, s_sv, s_hld, s_wpct, s_tbf, s_hits, s_hr, s_bb, s_hbp, s_so, s_runs, s_er, s_avg = (
                s_stadium.strip(), int(s_games), self.str_to_float(s_era), int(s_wins), int(s_loses), int(s_sv), int(s_hld),
                self.str_to_float(s_wpct), int(s_tbf), int(s_hits), int(s_hr), int(s_bb), int(s_hbp), int(s_so), int(s_runs), int(s_er),
                self.str_to_float(s_avg)
            )

            # 구장별 테이블
            data = (player_id, s_stadium, s_games, s_era, s_wins, s_loses, s_sv, s_hld, s_wpct, s_tbf,
                    s_ip, s_hits, s_hr, s_bb, s_hbp, s_so, s_runs, s_er, s_avg)
            await self.upsert_data("pitcher_stadiums", data)

    async def run(self, start_id: int, end_id: int):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for player_id in range(start_id, end_id + 1):
                if await self.check_player(page, player_id):
                    await self.process_player_data(page, player_id)

            await browser.close()
            logger.info(f"총 처리된 선수 수: {self.count}")

async def main():
    db_config = {
        "host": "116.37.91.221",
        "user": "niscom",
        "password": "niscom",
        "database": "baseball",
    }

    db_manager = DatabaseManager(**db_config)
    scraper = BaseballDataScraper(db_manager)
    
    await scraper.run(start_id=50007, end_id=99811)

if __name__ == "__main__":
    asyncio.run(main())
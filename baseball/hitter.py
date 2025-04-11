import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple, Optional
from datetime import datetime

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

    def str_to_float(self, str):
        if str == "-":
            return None
        return float(str)

    def _get_upsert_query(self, table_name: str) -> str:
        """각 테이블별 upsert 쿼리를 반환하는 메서드"""
        queries = {
            "hitters": """
            INSERT INTO hitters (
                hitter_id, player_name, team_name, avg, games, pa, ab, runs, hits, doubles, triples, hr, 
                rbi, sb, cs, sac, sf, bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                player_name = VALUES(player_name),
                team_name = VALUES(team_name),
                avg = VALUES(avg),
                games = VALUES(games),
                pa = VALUES(pa),
                ab = VALUES(ab),
                runs = VALUES(runs),
                hits = VALUES(hits),
                doubles = VALUES(doubles),
                triples = VALUES(triples),
                hr = VALUES(hr),
                rbi = VALUES(rbi),
                sb = VALUES(sb),
                cs = VALUES(cs),
                sac = VALUES(sac),
                sf = VALUES(sf),
                bb = VALUES(bb),
                ibb = VALUES(ibb),
                hbp = VALUES(hbp),
                so = VALUES(so),
                gdp = VALUES(gdp),
                slg = VALUES(slg),
                obp = VALUES(obp),
                errors = VALUES(errors),
                sb_percentage = VALUES(sb_percentage),
                mh = VALUES(mh),
                ops = VALUES(ops),
                risp = VALUES(risp),
                ph_ba = VALUES(ph_ba)
            """,
            "hitter_games": """
            INSERT INTO hitter_games (
                hitter_id, game_date, opponent_team, avg, pa, ab, runs, hits, doubles, triples, hr, 
                rbi, sb, cs, bb, hbp, so, gdp
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE 
                opponent_team = VALUES(opponent_team),
                avg = VALUES(avg),
                pa = VALUES(pa),
                ab = VALUES(ab),
                runs = VALUES(runs),
                hits = VALUES(hits),
                doubles = VALUES(doubles),
                triples = VALUES(triples),
                hr = VALUES(hr),
                rbi = VALUES(rbi),
                sb = VALUES(sb),
                cs = VALUES(cs),
                bb = VALUES(bb),
                hbp = VALUES(hbp),
                so = VALUES(so),
                gdp = VALUES(gdp)
            """,
            "hitter_opponents": """
            INSERT INTO hitter_opponents (
                hitter_id, opponent_team, games, avg, pa, ab, runs, hits, doubles, triples, hr, 
                rbi, sb, cs, bb, hbp, so, gdp
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE 
                games = VALUES(games),
                avg = VALUES(avg),
                pa = VALUES(pa),
                ab = VALUES(ab),
                runs = VALUES(runs),
                hits = VALUES(hits),
                doubles = VALUES(doubles),
                triples = VALUES(triples),
                hr = VALUES(hr),
                rbi = VALUES(rbi),
                sb = VALUES(sb),
                cs = VALUES(cs),
                bb = VALUES(bb),
                hbp = VALUES(hbp),
                so = VALUES(so),
                gdp = VALUES(gdp)
            """,
            "hitter_stadiums": """
            INSERT INTO hitter_stadiums (
                hitter_id, stadium, games, avg, pa, ab, runs, hits, doubles, triples, hr, 
                rbi, sb, cs, bb, hbp, so, gdp
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE 
                games = VALUES(games),
                avg = VALUES(avg),
                pa = VALUES(pa),
                ab = VALUES(ab),
                runs = VALUES(runs),
                hits = VALUES(hits),
                doubles = VALUES(doubles),
                triples = VALUES(triples),
                hr = VALUES(hr),
                rbi = VALUES(rbi),
                sb = VALUES(sb),
                cs = VALUES(cs),
                bb = VALUES(bb),
                hbp = VALUES(hbp),
                so = VALUES(so),
                gdp = VALUES(gdp)
            """,
            "hitter_situations": """
            INSERT INTO hitter_situations (
                hitter_id, situation, avg, ab, hits, doubles, triples, hr, rbi, bb, 
                hbp, so, gdp
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE 
                avg = VALUES(avg),
                ab = VALUES(ab),
                hits = VALUES(hits),
                doubles = VALUES(doubles),
                triples = VALUES(triples),
                hr = VALUES(hr),
                rbi = VALUES(rbi),
                bb = VALUES(bb),
                hbp = VALUES(hbp),
                so = VALUES(so),
                gdp = VALUES(gdp)
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

    async def check_player(self, page: Page, player_id: int) -> bool:
        url = f"https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx?playerId={player_id}"
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
        try:
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
            
            team_name, avg, games, pa, ab, runs, hits, doubles, triples, hr, _, rbi, sb, cs, sac, sf = first_td_values
            team_name, avg, games, pa, ab, runs, hits, doubles, triples, hr, rbi, sb, cs, sac, sf = (
                team_name.strip(), self.str_to_float(avg), int(games), int(pa), int(ab), int(runs), int(hits), 
                int(doubles), int(triples), int(hr), int(rbi), int(sb), int(cs), int(sac), int(sf)
            )

            # 추가 정보 추출
            second_row = page.locator('//*[@id="contents"]/div[2]/div[2]/div[3]/table/tbody/tr').first
            second_td_elements = second_row.locator('td')
            second_td_values = []
            for i in range(await second_td_elements.count()):
                text = await second_td_elements.nth(i).text_content()
                second_td_values.append((text or "").strip())
            
            bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba = second_td_values
            bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba = (
                int(bb), int(ibb), int(hbp), int(so), int(gdp), self.str_to_float(slg), self.str_to_float(obp), 
                int(errors), float(sb_percentage) / 100 if sb_percentage != "-" else None, 
                int(mh), self.str_to_float(ops), self.str_to_float(risp), self.str_to_float(ph_ba)
            )

            # hitters 테이블에 데이터 삽입
            data = (player_id, player_name, team_name, avg, games, pa, ab, runs, hits, doubles, triples, hr, 
                    rbi, sb, cs, sac, sf, bb, ibb, hbp, so, gdp, slg, obp, errors, sb_percentage, mh, ops, risp, ph_ba)
            await self.upsert_data("hitters", data)

            # 최근 10경기 데이터 처리
            recent_10_games = page.locator('//*[@id="contents"]/div[2]/div[2]/div[4]/table/tbody').first
            recent_tr_elements = recent_10_games.locator('tr')
            for i in range(await recent_tr_elements.count()):
                row = recent_tr_elements.nth(i)
                td_elements = row.locator('td')
                td_count = await td_elements.count()

                td_values = []
                for j in range(td_count):
                    text = await td_elements.nth(j).text_content()
                    td_values.append((text or "").strip())
                
                r_date, r_opponent, r_avg, r_pa, r_ab, r_runs, r_hits, r_doubles, r_triples, r_hr, r_rbi, r_sb, r_cs, r_bb, r_hbp, r_so, r_gdp = td_values
                
                # r_date 문자열 변환
                current_year = datetime.now().year
                r_date = f"{current_year}-{r_date.replace('.', '-')}"
                r_opponent = r_opponent.strip()
                r_avg, r_pa, r_ab, r_runs, r_hits, r_doubles, r_triples, r_hr, r_rbi, r_sb, r_cs, r_bb, r_hbp, r_so, r_gdp = (
                    self.str_to_float(r_avg), int(r_pa), int(r_ab), int(r_runs), int(r_hits), int(r_doubles), 
                    int(r_triples), int(r_hr), int(r_rbi), int(r_sb), int(r_cs), int(r_bb), 
                    int(r_hbp), int(r_so), int(r_gdp)
                )

                # 일자별 기록 테이블에 데이터 삽입
                data = (player_id, r_date, r_opponent, r_avg, r_pa, r_ab, r_runs, r_hits, r_doubles, 
                        r_triples, r_hr, r_rbi, r_sb, r_cs, r_bb, r_hbp, r_so, r_gdp)
                await self.upsert_data("hitter_games", data)

            # 상대별 기록 처리
            url = f"https://www.koreabaseball.com/Record/Player/HitterDetail/Game.aspx?playerId={player_id}"
            await self.goto_with_retry(page, url)

            case_by_opponent = page.locator('//*[@id="contents"]/div[2]/div[2]/div[1]/table/tbody')
            cbo_tr_elements = case_by_opponent.locator('tr')
            for i in range(await cbo_tr_elements.count()):
                row = cbo_tr_elements.nth(i)
                td_elements = row.locator('td')
                td_count = await td_elements.count()

                td_values = []
                for j in range(td_count):
                    text = await td_elements.nth(j).text_content()
                    td_values.append((text or "").strip())
                
                o_opponent, o_games, o_avg, o_pa, o_ab, o_runs, o_hits, o_doubles, o_triples, o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp = td_values
                o_opponent = o_opponent.strip()
                o_games = int(o_games)
                o_avg = self.str_to_float(o_avg)
                o_pa, o_ab, o_runs, o_hits, o_doubles, o_triples, o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp = (
                    int(o_pa), int(o_ab), int(o_runs), int(o_hits), int(o_doubles), int(o_triples), 
                    int(o_hr), int(o_rbi), int(o_sb), int(o_cs), int(o_bb), int(o_hbp), int(o_so), int(o_gdp)
                )

                # 상대별 테이블
                data = (player_id, o_opponent, o_games, o_avg, o_pa, o_ab, o_runs, o_hits, o_doubles, 
                        o_triples, o_hr, o_rbi, o_sb, o_cs, o_bb, o_hbp, o_so, o_gdp)
                await self.upsert_data("hitter_opponents", data)

            # 구장별 기록 처리
            case_by_stadium = page.locator('//*[@id="contents"]/div[2]/div[2]/div[2]/table/tbody')
            cbs_tr_elements = case_by_stadium.locator('tr')
            for i in range(await cbs_tr_elements.count()):
                row = cbs_tr_elements.nth(i)
                td_elements = row.locator('td')
                td_count = await td_elements.count()

                td_values = []
                for j in range(td_count):
                    text = await td_elements.nth(j).text_content()
                    td_values.append((text or "").strip())
                
                s_stadium, s_games, s_avg, s_pa, s_ab, s_runs, s_hits, s_doubles, s_triples, s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp = td_values
                s_stadium = s_stadium.strip()
                s_games = int(s_games)
                s_avg = self.str_to_float(s_avg)
                s_pa, s_ab, s_runs, s_hits, s_doubles, s_triples, s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp = (
                    int(s_pa), int(s_ab), int(s_runs), int(s_hits), int(s_doubles), int(s_triples), 
                    int(s_hr), int(s_rbi), int(s_sb), int(s_cs), int(s_bb), int(s_hbp), int(s_so), int(s_gdp)
                )

                # 구장별 테이블
                data = (player_id, s_stadium, s_games, s_avg, s_pa, s_ab, s_runs, s_hits, s_doubles, 
                        s_triples, s_hr, s_rbi, s_sb, s_cs, s_bb, s_hbp, s_so, s_gdp)
                await self.upsert_data("hitter_stadiums", data)

            # 상황별 기록 처리
            url = f"https://www.koreabaseball.com/Record/Player/HitterDetail/Situation.aspx?playerId={player_id}"
            await self.goto_with_retry(page, url)

            case_by_runners = page.locator('//*[@id="contents"]/div[2]/div[2]/div[1]/table/tbody')
            cbr_tr_elements = case_by_runners.locator('tr')
            for i in range(await cbr_tr_elements.count()):
                row = cbr_tr_elements.nth(i)
                td_elements = row.locator('td')
                td_count = await td_elements.count()

                td_values = []
                for j in range(td_count):
                    text = await td_elements.nth(j).text_content()
                    td_values.append((text or "").strip())
                
                if len(td_values) != 1:
                    r_situation, r_avg, r_ab, r_hits, r_doubles, r_triples, r_hr, r_rbi, r_bb, r_hbp, r_so, r_gdp = td_values
                    r_situation = r_situation.strip()
                    r_avg = s_avg = self.str_to_float(r_avg)
                    r_ab, r_hits, r_doubles, r_triples, r_hr, r_rbi, r_bb, r_hbp, r_so, r_gdp = (
                        int(r_ab), int(r_hits), int(r_doubles), int(r_triples), int(r_hr), 
                        int(r_rbi), int(r_bb), int(r_hbp), int(r_so), int(r_gdp)
                    )

                    data = (player_id, r_situation, r_avg, r_ab, r_hits, r_doubles, r_triples, 
                            r_hr, r_rbi, r_bb, r_hbp, r_so, r_gdp)
                    await self.upsert_data("hitter_situations", data)

        except Exception as e:
            logger.error(f"플레이어 {player_id} 데이터 처리 중 오류: {e}")

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
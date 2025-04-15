from utils.create_async_sqlalchemy_engine import create_async_sqlalchemy_engine
from get_query import get_query
from get_table_columns import get_table_columns

from datetime import datetime
from playwright.async_api import async_playwright, Page

class BaseballPlayerScraper:
    def __init__(self, db_config: Dict[str, Any], player_type: str, max_retries: int = 3):
        self.db_engine = create_async_sqlalchemy_engine(db_config)
        self.player_type = player_type
        self.max_retries = max_retries
        self.count = 0

    def run(self):
        if self.player_type == "hitter":
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                for player_id in range(start_id, end_id + 1):
                    if await self.check_player(page, player_id):
                        await self.crawling_hitter_stats(page=page, player_id=player_id)
                        await self.crawling_hitter_recent_games(page=pass, player_id=player_id=)
                        
                        

                await browser.close()
                logger.info(f"총 처리된 선수 수: {self.count}")

    def str_to_float(self, str):
        if str == "-":
            return None
        return float(str)

    def mapping_columns_with_data(self, table_name, data_tuple):
        columns = get_table_columns(table_name=table_name)
        # 컬럼과 값을 매핑하여 dict 생성
        data_dict = dict(zip(columns, data_tuple))

        return data_dict
    
    async def upsert_data(self, table_name, data_tuple):
        query = get_query(table_name=table_name)
        data = self.mapping_columns_with_data(table_name=table_name, data_tuple=data_tuple)

        async with self.db_engine.begin() as conn:
            await conn.execute(query, data)

    async def goto_with_retry(self, page: Page, url: str):
        """페이지 이동 (재시도 로직 포함)"""
        for attempt in range(self.max_retries):
            try:
                await page.goto(url, wait_until="load", timeout=30000)  # 30초 타임아웃
                return True
            except Exception as e:
                if attempt == self.max_retries - 1:  # 마지막 시도였다면
                    print(f"페이지 로드 실패 (최종 실패): {url}, 오류: {e}")
                    raise  # 마지막 시도에서도 실패하면 예외 발생
                print(f"페이지 로드 실패 (재시도 {attempt+1}/{self.max_retries}): {url}, 오류: {e}")
                await asyncio.sleep(2)  # 재시도 전 2초 대기

    async def check_player(self, page: Page, player_id: int) -> bool:
        """선수 ID가 유효한지 확인"""
        if self.player_type == "hitter":
            url = f"https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx?playerId={player_id}"
        else:
            url = f"https://www.koreabaseball.com/Record/Player/PitcherDetail/Basic.aspx?playerId={player_id}"
        
        await self.goto_with_retry(page, url)
        
        try:
            image_element = await page.locator('//*[@id="cphContents_cphContents_cphContents_playerProfile_imgProgile"]').get_attribute('src')
            return "no-Image" not in image_element
        except Exception as e:
            print(f"{self.player_type} 플레이어 {player_id} 확인 중 오류: {e}")
            return False

    async def crawling_hitter_stats(self, page: Page, player_id: int):
        # 기록이 있는지 확인
        is_record = await page.locator('//*[@id="contents"]/div[2]/div[2]/div[2]/table/tbody/tr/td').count()
        if is_record == 1:
            return

        # 기록이 있다면 count 1 증가
        self.count += 1

        # 선수 이름 추출
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

        await self.upsert_data(table_name="hitters", data_tuple=data)
    
    async def crawling_hitter_recent_games(self, page: Page, player_id: int):
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
            await self.upsert_data(table_name="hitter_games", data_tuple=data)

    async def crawling_hitter_opponents(self, page: Page, player_id: int):
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
            await self.upsert_data(table_name="hitter_opponents", data_tuple=data)

    async def crawling_hitter_stadiums(self, page: Page, player_id: int):
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
            await self.upsert_data(table_name="hitter_stadiums", data_tuple=data)
    
    async def crawling_pitcher_stats(self, page: Page, player_id: int):
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
        await self.upsert_data(table_name="pitchers", data_tuple=data)

    async def crawling_pitcher_recent_games(self, page: Page, player_id: int):
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
            await self.upsert_data(table_name="pitcher_games", data_tuple=data)
    
    async def crawling_pitcher_opponents(self, page: Page, player_id: int):
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
            await self.upsert_data(table_name="pitcher_opponents", data_tuple=data)
    
    async def crawling_pitcher_stadiums(self, page: Page, player_id: int):
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
            await self.upsert_data(table_name="pitcher_stadiums", data_tuple=data)

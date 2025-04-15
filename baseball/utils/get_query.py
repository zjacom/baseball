def get_query(table_name: str) -> str:
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

        "pitchers": """
        INSERT INTO pitchers (
            pitcher_id, player_name, team_name, era, games, cg, sho, wins, losses, sv, hld,
            wpct, tbf, np, ip, hits, doubles, triples, hr, sac, sf, bb, ibb, so, wp, bk,
            runs, er, bsv, whip, avg, qs
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            player_name = VALUES(player_name),
            team_name = VALUES(team_name),
            era = VALUES(era),
            games = VALUES(games),
            cg = VALUES(cg),
            sho = VALUES(sho),
            wins = VALUES(wins),
            losses = VALUES(losses),
            sv = VALUES(sv),
            hld = VALUES(hld),
            wpct = VALUES(wpct),
            tbf = VALUES(tbf),
            np = VALUES(np),
            ip = VALUES(ip),
            hits = VALUES(hits),
            doubles = VALUES(doubles),
            triples = VALUES(triples),
            hr = VALUES(hr),
            sac = VALUES(sac),
            sf = VALUES(sf),
            bb = VALUES(bb),
            ibb = VALUES(ibb),
            so = VALUES(so),
            wp = VALUES(wp),
            bk = VALUES(bk),
            runs = VALUES(runs),
            er = VALUES(er),
            bsv = VALUES(bsv),
            whip = VALUES(whip),
            avg = VALUES(avg),
            qs = VALUES(qs)
        """,

        "pitcher_games": """
        INSERT INTO pitcher_games (
            pitcher_id, game_date, opponent_team, result, era, tbf, ip, hits, hr,
            bb, hbp, so, runs, er, avg
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE 
            opponent_team = VALUES(opponent_team),
            result = VALUES(result),
            era = VALUES(era),
            tbf = VALUES(tbf),
            ip = VALUES(ip),
            hits = VALUES(hits),
            hr = VALUES(hr),
            bb = VALUES(bb),
            hbp = VALUES(hbp),
            so = VALUES(so),
            runs = VALUES(runs),
            er = VALUES(er),
            avg = VALUES(avg)
        """,

        "pitcher_opponents": """
        INSERT INTO pitcher_opponents (
            pitcher_id, opponent_team, games, era, wins, losses, sv, hld, wpct, tbf,
            ip, hits, hr, bb, hbp, so, runs, er, avg
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE 
            games = VALUES(games),
            era = VALUES(era),
            wins = VALUES(wins),
            losses = VALUES(losses),
            sv = VALUES(sv),
            hld = VALUES(hld),
            wpct = VALUES(wpct),
            tbf = VALUES(tbf),
            ip = VALUES(ip),
            hits = VALUES(hits),
            hr = VALUES(hr),
            bb = VALUES(bb),
            hbp = VALUES(hbp),
            so = VALUES(so),
            runs = VALUES(runs),
            er = VALUES(er),
            avg = VALUES(avg)
        """,

        "pitcher_stadiums": """
        INSERT INTO pitcher_stadiums (
            pitcher_id, stadium, games, era, wins, losses, sv, hld, wpct, tbf, ip, 
            hits, hr, bb, hbp, so, runs, er, avg, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON DUPLICATE KEY UPDATE 
            games = VALUES(games),
            era = VALUES(era),
            wins = VALUES(wins),
            losses = VALUES(losses),
            sv = VALUES(sv),
            hld = VALUES(hld),
            wpct = VALUES(wpct),
            tbf = VALUES(tbf),
            ip = VALUES(ip),
            hits = VALUES(hits),
            hr = VALUES(hr),
            bb = VALUES(bb),
            hbp = VALUES(hbp),
            so = VALUES(so),
            runs = VALUES(runs),
            er = VALUES(er),
            avg = VALUES(avg),
            created_at = NOW();
        """
    }

    return queries.get(table_name, "")
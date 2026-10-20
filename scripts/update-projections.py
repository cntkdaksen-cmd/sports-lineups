#!/usr/bin/env python3
"""Save dated, attributed lineup predictions from public lineup pages."""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'ucl': ('UCL', 'soccer'), 'epl': ('EPL', 'soccer'),
    'laliga': ('LIGA', 'soccer'), 'bundesliga': ('BUND', 'soccer'),
    'seriea': ('SERI', 'soccer'), 'ligue1': ('FRAN', 'soccer'),
    'mls': ('MLS', 'soccer'), 'wnba': ('', 'wnba'),
    'nba': ('', 'nba'), 'mlb': ('', 'mlb'),
}


def source_url(league, code, kind):
    if kind == 'soccer':
        return f'https://www.rotowire.com/soccer/lineups.php?league={code}'
    if kind == 'nba':
        return 'https://www.rotowire.com/basketball/nba-lineups.php'
    if kind == 'wnba':
        return 'https://www.rotowire.com/wnba/lineups.php'
    return 'https://www.rotowire.com/baseball/daily-lineups.php'


def scrape_page(league, code, kind):
    import urllib.request
    request = urllib.request.Request(source_url(league, code, kind), headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        page = response.read().decode('utf-8', errors='replace')
    blocks = re.split(r'(?=<div class="lineup is-(?:nba|wnba|soccer|mlb))', page)[1:]
    results = []
    for block in blocks:
        teams = {}
        names = {}
        for role, abbr in re.findall(r'<(?:a|div)[^>]*class="lineup__team is-(home|visit)"[^>]*>.*?<div class="lineup__abbr">([^<]+)</div>', block, re.S):
            teams['away' if role == 'visit' else 'home'] = html.unescape(abbr.strip())
        for role, name in re.findall(r'<div class="lineup__mteam is-(home|visit)"[^>]*>\s*([^<]+)', block):
            names['away' if role == 'visit' else 'home'] = html.unescape(name.strip())
        if len(teams) != 2:
            continue
        time_match = re.search(r'<div class="lineup__time">(.*?)</div>', block, re.S)
        if not time_match:
            continue
        time_text = re.sub(r'<[^>]+>|&nbsp;', ' ', time_match.group(1)).strip()
        if kind != 'soccer':
            # Daily NBA/MLB pages identify the date in the page heading.
            date_match = re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', page[300000:])
            if not date_match:
                continue
            time_text = date_match.group(0).replace(',', '') + ' ' + time_text
        else:
            time_text = time_text + f' {datetime.now(timezone.utc).year}'
            time_text = re.sub(r' ET (\d{4})$', r' \1 ET', time_text)
        try:
            moment = datetime.strptime(time_text.replace(' ET', ''), '%B %d %I:%M %p %Y' if kind == 'soccer' else '%B %d %Y %I:%M %p')
            kickoff = moment.replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        except ValueError:
            continue
        rosters = {}
        injuries = {}
        statuses = {}
        for role in ('home', 'visit'):
            side = 'away' if role == 'visit' else 'home'
            roster_match = re.search(r'<ul class="lineup__list is-' + role + r'".*?</ul>', block, re.S)
            if not roster_match:
                continue
            roster_html = roster_match.group(0)
            lineup_html = roster_html.split('<li class="lineup__title')[0]
            statuses[side] = 'confirmed' if 'is-confirmed' in lineup_html else 'predicted'
            players = []
            for item in re.findall(r'<li class="lineup__player[^>]*>.*?</li>', lineup_html, re.S):
                name = re.search(r'<a title="([^"]+)"', item)
                if not name:
                    continue
                position = re.search(r'<div class="lineup__pos[^>]*>([^<]+)', item)
                flag = re.search(r'<span class="lineup__inj">([^<]+)', item)
                players.append({'name': html.unescape(name.group(1)), 'position': position.group(1).strip() if position else '', 'flag': flag.group(1).strip() if flag else ''})
            rosters[side] = players
            injury_html = roster_html[len(lineup_html):]
            injuries[side] = [html.unescape(name) for name in re.findall(r'<li class="lineup__player[^>]*>.*?<a title="([^"]+)"', injury_html, re.S)][:8]
        expected = 11 if kind == 'soccer' else 9 if kind == 'mlb' else 5
        if any(len(rosters.get(side, [])) != expected for side in ('home', 'away')):
            continue
        results.append({'league': league, 'kickoff': kickoff, 'teams': teams, 'names': names, 'lineups': rosters, 'injuries': injuries, 'statuses': statuses, 'source': source_url(league, code, kind)})
    return results


def scrape_europa():
    import urllib.request
    url = 'https://starting11.com/europa-league'
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        page = response.read().decode('utf-8', errors='replace')
    results = []
    for article in re.findall(r'<article class="rounded-xl border border-white/\[0\.07\].*?</article>', page, re.S):
        title = re.search(r'<h3[^>]*>([^<]+) predicted lineups</h3>', article)
        time_match = re.search(r'Kick-off is (\d{1,2}:\d{2}) BST on (\w{3} \d{1,2} \w{3})', article)
        if not title or not time_match or ' vs ' not in title.group(1):
            continue
        home_name, away_name = title.group(1).split(' vs ', 1)
        try:
            moment = datetime.strptime(time_match.group(2) + f' {datetime.now(timezone.utc).year} ' + time_match.group(1), '%a %d %b %Y %H:%M')
            kickoff = moment.replace(tzinfo=ZoneInfo('Europe/London')).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        except ValueError:
            continue
        lineups = {}
        for side, name in [('home', home_name), ('away', away_name)]:
            match = re.search(r'<strong[^>]*>' + re.escape(name) + r' predicted lineup[^<]*</strong>\s*<!-- -->\s*(.*?)</p>', article, re.S)
            if not match:
                break
            names = [html.unescape(value.strip(' .')) for value in re.split(r'[;,]', match.group(1)) if value.strip(' .')]
            lineups[side] = [{'name': name, 'position': '', 'flag': ''} for name in names]
        if len(lineups.get('home', [])) != 11 or len(lineups.get('away', [])) != 11:
            continue
        results.append({'league': 'uel', 'kickoff': kickoff, 'names': {'home': home_name, 'away': away_name}, 'teams': {}, 'lineups': lineups, 'injuries': {}, 'statuses': {'home': 'predicted', 'away': 'predicted'}, 'source': url})
    return results


def fetch_text(url):
    import urllib.request
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode('utf-8', errors='replace')


def fetch_json(url):
    return json.loads(fetch_text(url))


def scrape_fotmob_kleague(league_id, key):
    """Use FotMob schedule and its lastStarting11 roster for K League projections."""
    from urllib.parse import urlencode
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    end = today.fromordinal(today.toordinal() + 2)
    query = urlencode({'id': league_id, 'ccode3': 'KOR', 'season': today.year})
    data = fetch_json('https://www.fotmob.com/api/data/leagues?' + query)
    events = []
    for match in data.get('fixtures', {}).get('allMatches', []):
        status = match.get('status', {})
        kickoff_text = status.get('utcTime')
        if not kickoff_text:
            continue
        kickoff = datetime.fromisoformat(kickoff_text.replace('Z', '+00:00'))
        local = kickoff.astimezone(ZoneInfo('Asia/Seoul'))
        if not today <= local.date() < end or status.get('finished'):
            continue
        home, away = match.get('home', {}), match.get('away', {})
        if not home.get('id') or not away.get('id'):
            continue
        detail = fetch_json('https://www.fotmob.com/api/data/matchDetails?' + urlencode({'matchId': match['id']}))
        lineup = detail.get('lineup', {})
        def players(team):
            result = []
            for row in team.get('starters', []):
                player = row.get('player', row)
                if player.get('name'):
                    result.append({'name': player['name'], 'position': row.get('position', ''), 'flag': ''})
            return result[:11]
        rosters = {'home': players(lineup.get('homeTeam', {})), 'away': players(lineup.get('awayTeam', {}))}
        names = {'home': home.get('name', ''), 'away': away.get('name', '')}
        utc = kickoff.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        competitors = [
            {'homeAway': 'home', 'team': {'id': home['id'], 'displayName': names['home'], 'shortDisplayName': names['home'], 'abbreviation': str(home['id'])}},
            {'homeAway': 'away', 'team': {'id': away['id'], 'displayName': names['away'], 'shortDisplayName': names['away'], 'abbreviation': str(away['id'])}}
        ]
        prediction = {'league': key, 'kickoff': utc, 'names': names, 'teams': {'home': str(home['id']), 'away': str(away['id'])},
            'lineups': rosters, 'injuries': {}, 'statuses': {'home': 'predicted', 'away': 'predicted'},
            'note': 'FotMob 최근 선발 11명 기준 예상', 'source': 'https://www.fotmob.com'}
        events.append({'event': {'id': str(match['id']), 'date': utc, 'competitions': [{'competitors': competitors}]}, 'prediction': prediction, 'confirmed': False})
    return events


def scrape_khl():
    """Import two-day KHL fixtures from the public KHL mobile API."""
    from urllib.parse import urlencode
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    start = datetime.combine(today, datetime.min.time(), ZoneInfo('Asia/Seoul')).astimezone(timezone.utc).timestamp()
    end = start + 2 * 86400
    query = urlencode({'q[start_at_gt_time_from_unixtime]': int(start), 'q[start_at_lt_time_from_unixtime]': int(end), 'order_direction': 'asc', 'locale': 'en'}, safe='[]')
    raw = fetch_json('https://khl.api.webcaster.pro/api/khl_mobile/events_v2.json?' + query)
    events = []
    for row in raw if isinstance(raw, list) else raw.get('events', []):
        game = row.get('event', row)
        if game.get('type_id') != 24 or not game.get('start_at'):
            continue
        home, away = game.get('team_a', {}), game.get('team_b', {})
        names = {'home': home.get('name', ''), 'away': away.get('name', '')}
        if not names['home'] or not names['away']:
            continue
        kickoff = datetime.fromtimestamp(game['start_at'] / 1000, timezone.utc).isoformat().replace('+00:00', 'Z')
        competitors = [
            {'homeAway': 'home', 'team': {'id': str(home['id']), 'displayName': names['home'], 'shortDisplayName': names['home'], 'abbreviation': str(home['id'])}},
            {'homeAway': 'away', 'team': {'id': str(away['id']), 'displayName': names['away'], 'shortDisplayName': names['away'], 'abbreviation': str(away['id'])}}
        ]
        prediction = {'league': 'khl', 'kickoff': kickoff, 'names': names, 'teams': {'home': str(home['id']), 'away': str(away['id'])},
            'lineups': {}, 'injuries': {}, 'statuses': {'home': 'predicted', 'away': 'predicted'},
            'note': 'KHL 경기 일정 확인됨. 경기 전 선발 명단 공개 대기.', 'source': 'https://khl.api.webcaster.pro'}
        events.append({'event': {'id': str(game['id']), 'date': kickoff, 'competitions': [{'competitors': competitors}]}, 'prediction': prediction, 'confirmed': False})
    return events


def scrape_cpbl():
    """Use CPBL public schedule and game detail API for two-day starter projections."""
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    events = []
    for offset in range(2):
        day = today.fromordinal(today.toordinal() + offset)
        games = fetch_json(f'https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/{day.isoformat()}')
        rows = games.get('Data', {}).get('Games', [])
        for game in rows:
            game_id = game.get('GameId') or game.get('Id')
            if not game_id:
                continue
            detail = fetch_json(f'https://stats.cpbl.com.tw/api/proxy/v1/games/{game_id}')
            data = detail.get('Data', {}).get('Game', {})
            visiting, home = data.get('Visiting', {}), data.get('Home', {})
            def hitters(team):
                return [{'name': row.get('HitterName', ''), 'position': row.get('PositionName', ''), 'flag': ''}
                        for row in team.get('Hitters', []) if row.get('HitterName') and row.get('Lineup')]
            away_players, home_players = hitters(visiting), hitters(home)
            names = {'home': home.get('TeamName', game.get('HomeTeamName', '')), 'away': visiting.get('TeamName', game.get('VisitingTeamName', ''))}
            if not names['home'] or not names['away']:
                continue
            time_text = game.get('GameTime') or game.get('StartTime') or '18:35'
            try:
                local = datetime.strptime(f'{day.isoformat()} {time_text[:5]}', '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('Asia/Taipei'))
            except ValueError:
                continue
            kickoff = local.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            competitors = [{'homeAway': side, 'team': {'id': names[side], 'displayName': names[side], 'shortDisplayName': names[side], 'abbreviation': names[side]}} for side in ('home', 'away')]
            confirmed = len(home_players) >= 9 and len(away_players) >= 9
            prediction = {'league': 'cpbl', 'kickoff': kickoff, 'names': names, 'teams': names,
                'lineups': {'home': home_players, 'away': away_players}, 'injuries': {},
                'statuses': {'home': 'confirmed' if confirmed else 'predicted', 'away': 'confirmed' if confirmed else 'predicted'},
                'note': 'CPBL 공식 선발 타순' if confirmed else 'CPBL 경기 일정. 선발 발표 전.', 'source': 'https://stats.cpbl.com.tw'}
            events.append({'event': {'id': str(game_id), 'date': kickoff, 'competitions': [{'competitors': competitors}]}, 'prediction': prediction, 'confirmed': confirmed})
    return events


def scrape_npb():
    """Use SPAIA public schedule feed; show last available starter data when published."""
    today = datetime.now(ZoneInfo('Asia/Tokyo')).date()
    events = []
    for offset in range(2):
        day = today.fromordinal(today.toordinal() + offset)
        raw = fetch_json(f'https://spaia.jp/baseball/npb/api/games_info_by_date?gameDate={day:%Y%m%d}')
        games = raw if isinstance(raw, list) else raw.get('data', raw.get('games', []))
        for game in games:
            game_id = game.get('gameId') or game.get('GameID') or game.get('id')
            home = game.get('homeTeamName') or game.get('HomeTeamName') or game.get('home')
            away = game.get('visitorTeamName') or game.get('VisitorTeamName') or game.get('away')
            if not game_id or not home or not away:
                continue
            lineup = fetch_json(f'https://spaia.jp/baseball/npb/api/starting_members_for_flash?gameId={game_id}')
            sides = lineup if isinstance(lineup, dict) else {}
            def players(side):
                values = sides.get(side, sides.get('Home' if side == 'home' else 'Visitor', []))
                if isinstance(values, dict): values = values.get('players', values.get('members', []))
                return [{'name': row.get('name') or row.get('playerName') or row.get('PlayerName', ''), 'position': row.get('position', ''), 'flag': ''} for row in values if isinstance(row, dict) and (row.get('name') or row.get('playerName') or row.get('PlayerName'))]
            rosters = {'home': players('home'), 'away': players('visitor')}
            names = {'home': home, 'away': away}
            kickoff = datetime.combine(day, datetime.min.time(), ZoneInfo('Asia/Tokyo')).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            competitors = [{'homeAway': side, 'team': {'id': names[side], 'displayName': names[side], 'shortDisplayName': names[side], 'abbreviation': names[side]}} for side in ('home', 'away')]
            confirmed = len(rosters['home']) >= 9 and len(rosters['away']) >= 9
            prediction = {'league': 'npb', 'kickoff': kickoff, 'names': names, 'teams': names, 'lineups': rosters, 'injuries': {},
                'statuses': {'home': 'confirmed' if confirmed else 'predicted', 'away': 'confirmed' if confirmed else 'predicted'},
                'note': 'NPB 선발 타순' if confirmed else 'NPB 경기 일정. 선발 발표 전.', 'source': 'https://spaia.jp'}
            events.append({'event': {'id': str(game_id), 'date': kickoff, 'competitions': [{'competitors': competitors}]}, 'prediction': prediction, 'confirmed': confirmed})
    return events


def post_json(url, values, referer):
    import urllib.parse
    import urllib.request
    data = urllib.parse.urlencode(values).encode()
    request = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Referer': referer
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8', errors='replace'))


def scrape_kbo_official():
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    events = []
    for offset in range(2):
        day = today.fromordinal(today.toordinal() + offset).strftime('%Y%m%d')
        referer = f'https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx?gameDate={day}'
        games = post_json('https://www.koreabaseball.com/ws/Main.asmx/GetKboGameList', {
            'leId': 1, 'srId': '0,1,3,4,5,6,7,8,9', 'date': day
        }, referer).get('game', [])
        for game in games:
            if game.get('GAME_STATE_SC') in ('3', '4') or game.get('CANCEL_SC_ID') not in ('0', 0, None):
                continue
            rows = post_json('https://www.koreabaseball.com/ws/Schedule.asmx/GetLineUpAnalysis', {
                'leId': game['LE_ID'], 'srId': game['SR_ID'], 'seasonId': game['SEASON_ID'], 'gameId': game['G_ID']
            }, referer)
            if len(rows) < 5:
                continue
            def lineup(table):
                result = []
                for row in table.get('rows', []):
                    cells = row.get('row', [])
                    if len(cells) >= 3 and cells[2].get('Text'):
                        result.append({'name': cells[2]['Text'], 'position': cells[1].get('Text', ''), 'flag': ''})
                return result
            home, away = lineup(json.loads(rows[3][0])), lineup(json.loads(rows[4][0]))
            if not home and not away:
                continue
            confirmed = bool(rows[0] and rows[0][0].get('LINEUP_CK'))
            kickoff = datetime.strptime(day + game['G_TM'], '%Y%m%d%H:%M').replace(tzinfo=ZoneInfo('Asia/Seoul'))
            names = {'home': game['HOME_NM'], 'away': game['AWAY_NM']}
            competitors = [
                {'homeAway': 'home', 'team': {'id': game['HOME_ID'], 'displayName': names['home'], 'shortDisplayName': names['home'], 'abbreviation': game['HOME_ID']}},
                {'homeAway': 'away', 'team': {'id': game['AWAY_ID'], 'displayName': names['away'], 'shortDisplayName': names['away'], 'abbreviation': game['AWAY_ID']}}
            ]
            prediction = {'league': 'kbo', 'kickoff': kickoff.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'), 'names': names,
                'teams': {'home': game['HOME_ID'], 'away': game['AWAY_ID']}, 'lineups': {'home': home, 'away': away}, 'injuries': {},
                'statuses': {'home': 'confirmed' if confirmed else 'predicted', 'away': 'confirmed' if confirmed else 'predicted'},
                'note': 'KBO 공식 당일 타순' if confirmed else 'KBO 공식 최근 선발 타순 기준 예상',
                'source': f"https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx?gameDate={day}&gameId={game['G_ID']}&section=START_PIT"}
            events.append({'event': {'id': game['G_ID'], 'date': prediction['kickoff'], 'competitions': [{'competitors': competitors}]},
                'prediction': prediction, 'confirmed': confirmed})
    return events


def scrape_kbl_statgg():
    """Use KBL schedule and season player minutes as a transparent starter projection."""
    from html.parser import HTMLParser
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    end = today.fromordinal(today.toordinal() + 2)
    schedule = fetch_text(f'https://statgg.com/ko/kbl/schedule?date={today.isoformat()}')
    links = re.findall(r'<a[^>]+href="(/ko/kbl/matches/[^\"]+)"[^>]*>(.*?)</a>', schedule, re.S)
    events = []
    seen = set()
    for path, card in links:
        if path in seen:
            continue
        seen.add(path)
        names = re.findall(r'<span class="break-keep[^\"]*">([^<]+)</span>', card)
        time_match = re.search(r'<span class="stat-num text-fg-muted">(\d{1,2}:\d{2})</span>', card)
        if len(names) != 2 or not time_match or '예정' not in card:
            continue
        card_index = schedule.find(f'href="{path}"')
        day_match = list(re.finditer(r'<span class="stat-num tabular-nums">(\d{4}\.\d{2}\.\d{2})', schedule[:card_index]))
        if not day_match:
            continue
        kickoff_local = datetime.strptime(day_match[-1].group(1) + ' ' + time_match.group(1), '%Y.%m.%d %H:%M').replace(tzinfo=ZoneInfo('Asia/Seoul'))
        if not today <= kickoff_local.date() < end:
            continue
        detail = fetch_text('https://statgg.com' + path)
        tables = re.findall(r'<h3 class="font-semibold">([^<]+)</h3>.*?<tbody>(.*?)</tbody>', detail, re.S)
        lineups = {}
        for team_name, table in tables[:2]:
            players = []
            for row in re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.S):
                name_match = re.search(r'<a[^>]*>([^<]+)', row)
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
                if not name_match or len(cells) < 2:
                    continue
                minute_text = re.sub(r'<[^>]+>', '', cells[-1]).strip()
                try:
                    minutes = float(minute_text)
                except ValueError:
                    continue
                if minutes > 0:
                    players.append((minutes, html.unescape(name_match.group(1).strip())))
            projected = sorted(players, reverse=True)[:5]
            if projected:
                side = 'home' if team_name.strip() == names[0].strip() else 'away'
                lineups[side] = [{'name': player, 'position': '', 'flag': ''} for _, player in projected]
        if not lineups:
            continue
        event_id = path.rsplit('/', 1)[-1]
        competitors = [
            {'homeAway': 'home', 'team': {'id': names[0], 'displayName': names[0], 'shortDisplayName': names[0], 'abbreviation': names[0]}},
            {'homeAway': 'away', 'team': {'id': names[1], 'displayName': names[1], 'shortDisplayName': names[1], 'abbreviation': names[1]}}
        ]
        events.append({'event': {'id': event_id, 'date': kickoff_local.astimezone(timezone.utc).isoformat().replace('+00:00','Z'), 'competitions': [{'competitors': competitors}]}, 'prediction': {'league': 'kbl', 'kickoff': kickoff_local.astimezone(timezone.utc).isoformat().replace('+00:00','Z'), 'names': {'home': names[0], 'away': names[1]}, 'teams': {'home': names[0], 'away': names[1]}, 'lineups': lineups, 'injuries': {}, 'statuses': {'home': 'predicted', 'away': 'predicted'}, 'note': 'StatGG 시즌 경기당 출장시간 상위 5명 기준 예상 선발', 'source': 'https://statgg.com' + path}})
    return events


def scrape_kovo_bkvolley():
    """Import KOVO fixtures; match pages link registered rosters, not starters."""
    from html.parser import HTMLParser
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(); self.value = []
        def handle_data(self, data):
            self.value.append(data)
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    page = fetch_text('https://bkvolley.kr/matches')
    events, seen = [], set()
    for match in re.finditer(r'<a\b[^>]*href=["\'](/matches/\d+)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        path, anchor = match.groups()
        if path in seen:
            continue
        seen.add(path)
        parser = Text(); parser.feed(anchor)
        title = ' '.join(' '.join(parser.value).split())
        pair = re.search(r'(.+?)\s+vs\s+(.+)', title, re.I)
        if not pair:
            continue
        context_start = max(0, match.start()-500)
        context = page[context_start:match.end()+500]
        text_parser = Text(); text_parser.feed(context)
        context_text = ' '.join(' '.join(text_parser.value).split())
        date_pattern = r'(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2}):(\d{2})'
        date_candidates = list(re.finditer(date_pattern, context_text))
        date_match = min(date_candidates, key=lambda item: abs(item.start()-len(context_text)//2)) if date_candidates else None
        if date_match:
            year, month, day, hour, minute = map(int, date_match.groups())
        else:
            short_candidates = list(re.finditer(r'(?<!\d)(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{1,2}):(\d{2})', context_text))
            short_date = min(short_candidates, key=lambda item: abs(item.start()-len(context_text)//2)) if short_candidates else None
            if not short_date:
                continue
            month, day, hour, minute = map(int, short_date.groups())
            year = today.year
        try:
            kickoff_local = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo('Asia/Seoul'))
        except ValueError:
            continue
        if not today <= kickoff_local.date() <= today.fromordinal(today.toordinal()+1):
            continue
        home, away = [name.strip() for name in pair.groups()]
        kickoff = kickoff_local.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        competitors = [
            {'homeAway': 'home', 'team': {'id': home, 'displayName': home, 'shortDisplayName': home, 'abbreviation': home}},
            {'homeAway': 'away', 'team': {'id': away, 'displayName': away, 'shortDisplayName': away, 'abbreviation': away}}
        ]
        url = 'https://bkvolley.kr' + path
        prediction = {'league': 'kovo', 'kickoff': kickoff, 'names': {'home': home, 'away': away}, 'teams': {'home': home, 'away': away},
            'lineups': {}, 'injuries': {}, 'statuses': {'home': 'predicted', 'away': 'predicted'},
            'note': '배구인사이트 경기 일정·등록 선수 정보. 예상 선발 명단은 공개되지 않아 경기 페이지에서 등록 선수 명단을 확인하세요.', 'source': url}
        events.append({'event': {'id': path.rsplit('/', 1)[-1], 'date': kickoff, 'competitions': [{'competitors': competitors}]}, 'prediction': prediction, 'confirmed': False})
    return events


def main():
    all_results = []
    for league, (code, kind) in SOURCES.items():
        found = scrape_page(league, code, kind)
        all_results.extend(found)
        print(league, len(found))
    europa = scrape_europa()
    all_results.extend(europa)
    print('uel', len(europa))
    if not all_results:
        raise SystemExit('No lineups fetched; keeping the current snapshot')
    path = ROOT / 'dist' / 'projections.json'
    previous = json.loads(path.read_text()) if path.exists() else {}
    payload = {'asOf': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'items': all_results}
    payload['domestic'] = {}
    for key, scraper in (('kbo', scrape_kbo_official), ('kbl', scrape_kbl_statgg), ('kovo', scrape_kovo_bkvolley), ('npb', scrape_npb), ('cpbl', scrape_cpbl),
                         ('kleague1', lambda: scrape_fotmob_kleague(9080, 'kleague1')),
                         ('kleague2', lambda: scrape_fotmob_kleague(9116, 'kleague2')), ('khl', scrape_khl)):
        try:
            payload['domestic'][key] = scraper()
            print(key + ('-statgg' if key == 'kbl' else '-official'), len(payload['domestic'][key]))
        except Exception as error:
            print(key + ' source unavailable:', error)
            payload['domestic'][key] = previous.get('domestic', {}).get(key, [])
    if previous.get('items') == all_results and previous.get('domestic') == payload.get('domestic'):
        print('No lineup changes')
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()

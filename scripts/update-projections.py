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
    'nba': ('', 'nba'), 'mlb': ('', 'mlb'),
}


def source_url(league, code, kind):
    if kind == 'soccer':
        return f'https://www.rotowire.com/soccer/lineups.php?league={code}'
    if kind == 'nba':
        return 'https://www.rotowire.com/basketball/nba-lineups.php'
    return 'https://www.rotowire.com/baseball/daily-lineups.php'


def scrape_page(league, code, kind):
    import urllib.request
    request = urllib.request.Request(source_url(league, code, kind), headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        page = response.read().decode('utf-8', errors='replace')
    blocks = re.split(r'(?=<div class="lineup is-(?:nba|soccer|mlb))', page)[1:]
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
    if previous.get('items') == all_results:
        print('No lineup changes')
        return
    payload = {'asOf': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'items': all_results}
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()

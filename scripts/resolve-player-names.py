"""Resolve names from public search pages; never transliterate or bypass search challenges."""
import datetime as dt
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ('wikipedia.org', 'transfermarkt.co.kr', 'flashscore.co.kr', 'sofascore.com',
           'premierleague.com', 'bundesliga.com', 'uefa.com', 'fifa.com', 'nba.com', 'mlb.com', 'nhl.com',
           'liverpoolfc.com', 'mancity.com', 'manutd.com', 'tottenhamhotspur.com', 'arsenal.com',
           'fcbayern.com', 'bvb.de', 'borussia.de', 'vfb.de', 'realmadrid.com', 'fcbarcelona.com',
           'yna.co.kr', 'yonhapnews.co.kr', 'newsis.com', 'news1.kr', 'sportsseoul.com',
           'sportschosun.com', 'sportalkorea.com', 'osen.co.kr', 'xportsnews.com', 'spotvnews.co.kr',
           'mk.co.kr', 'hankyung.com', 'chosun.com', 'donga.com', 'khan.co.kr', 'kbs.co.kr', 'sbs.co.kr')
SEARCH_HOSTS = ('www.google.com', 'search.naver.com')
POLICY = 'google-search-result-v1'


def normalize(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', str(value)) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9가-힣]+', ' ', unicodedata.normalize('NFC', value).lower()).strip()


def source_domain(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443):
        return None
    host = (parsed.hostname or '').lower()
    return next((d for d in DOMAINS if host == d or host.endswith('.' + d)), None)


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts, self.links, self.headings = [], [], []
        self.skip, self.anchor, self.heading = None, None, None
        self.panel_titles = []
        self.panel = None
        self.depth = 0
        self.feed(html)
        self.text = ' '.join(self.parts)

    def handle_starttag(self, tag, attrs):
        if tag not in ('br', 'img', 'input', 'meta', 'link', 'hr', 'wbr', 'source', 'area', 'base', 'embed', 'param', 'track', 'col'):
            self.depth += 1
        if tag in ('script', 'style', 'noscript'):
            self.skip = tag
        if self.skip:
            return
        attrs = dict(attrs)
        if attrs.get('data-attrid') in ('title', 'title:'):
            self.panel = [self.depth, []]
        if tag == 'a':
            self.anchor = [attrs.get('href', ''), []]
        if tag in ('title', 'h1'):
            self.heading = [tag, []]

    def handle_endtag(self, tag):
        if self.panel and self.depth == self.panel[0]:
            self.panel_titles.append(' '.join(self.panel[1]))
            self.panel = None
        self.depth = max(0, self.depth - 1)
        if tag == self.skip:
            self.skip = None
        if self.skip:
            return
        if tag == 'a' and self.anchor:
            self.links.append((self.anchor[0], ' '.join(self.anchor[1])))
            self.anchor = None
        if self.heading and tag == self.heading[0]:
            self.headings.append(' '.join(self.heading[1]))
            self.heading = None

    def handle_data(self, data):
        if self.skip or not data.strip():
            return
        self.parts.append(data.strip())
        if self.panel:
            self.panel[1].append(data.strip())
        if self.anchor:
            self.anchor[1].append(data.strip())
        if self.heading:
            self.heading[1].append(data.strip())


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not source_domain(newurl) and urllib.parse.urlsplit(newurl).hostname not in SEARCH_HOSTS:
            raise ValueError('redirect-outside-reviewed-domains')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'SportsLineupsNameReview/1.0', 'Accept-Language': 'ko-KR,ko;q=0.9'})
    with urllib.request.build_opener(SafeRedirect()).open(request, timeout=20) as response:
        if 'html' not in response.headers.get('Content-Type', ''):
            raise ValueError('not-html')
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('page-too-large')
        page = Page(raw.decode(response.headers.get_content_charset() or 'utf-8', 'replace'))
    if re.search(r'unusual traffic|verify you are human|자동입력 방지문자|비정상적인 접근|보안 확인을 완료', page.text, re.I):
        raise ValueError('search-challenge')
    return page


def search_links(page, engine):
    links = {}
    for url, title in page.links:
        if engine == 'google' and url.startswith('/url?'):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            url = (query.get('q') or query.get('url') or [''])[0]
        if source_domain(url):
            url = urllib.parse.urldefrag(url)[0]
            if len(title) > len(links.get(url, '')):
                links[url] = title
    return list(links.items())[:8]


def candidates(headings):
    result = set()
    for heading in headings:
        title = re.split(r'\s+[|–—-]\s+|[|:(（]', unescape(heading))[0].strip()
        title = re.sub(r'\s+(선수 프로필|프로필|선수 정보|통계).*$', '', title).strip()
        if re.fullmatch(r'[가-힣]{1,12}(?:[ ·ㆍ-][가-힣]{1,12}){0,5}', title) and not re.search(r'선수|뉴스|축구|야구|농구|경기|하이라이트|프로필|통계', title):
            result.add(title)
    return result


def evidence(row, url, page, title, engines, team_dictionary):
    full = normalize(page.text)
    name = normalize(row['name'])
    # Adjacent bilingual full names establish identity; surname matches are never accepted.
    result = []
    for korean in candidates(page.headings + [title]):
        ko = normalize(korean)
        paired = re.search(r'(?<!\w)' + re.escape(ko + ' ' + name) + r'(?!\w)', full) or re.search(r'(?<!\w)' + re.escape(name + ' ' + ko) + r'(?!\w)', full)
        if not paired:
            continue
        team = row.get('team', '')
        aliases = [team, team_dictionary.get(team, '')]
        team_match = any(len(normalize(alias)) > 2 and normalize(alias) in full for alias in aliases)
        result.append({'korean': korean, 'url': url, 'domain': source_domain(url), 'engines': sorted(engines),
                       'teamMatched': team_match, 'bilingualNameMatched': True,
                       'contentHash': hashlib.sha256(page.text.encode()).hexdigest()})
    return result


def verify(row, proofs):
    variants = {normalize(p['korean']) for p in proofs}
    if len(variants) != 1:
        return None
    if len({p['domain'] for p in proofs}) < 2 or not any(p['teamMatched'] for p in proofs):
        return None
    if not any(p['domain'] != 'wikipedia.org' for p in proofs):
        return None
    return {'name': row['name'], 'korean': proofs[0]['korean'], 'team': row.get('team'),
            'league': row.get('league'), 'method': 'independent-bilingual-sources-v1', 'sources': proofs}


def google_result(row, url, page, team_dictionary):
    """Accept an identifiable Google result without requiring a second publisher."""
    proofs = evidence(row, url, page, '', {'google'}, team_dictionary)
    # Knowledge-panel titles need the exact queried player and sports identity on the page.
    full = normalize(page.text)
    name = normalize(row['name'])
    team = row.get('team', '')
    team_match = any(len(normalize(t)) > 2 and normalize(t) in full
                     for t in (team, team_dictionary.get(team, '')))
    panels = candidates(page.panel_titles)
    if len(panels) == 1 and re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', full) and team_match:
        proofs.append({'korean': next(iter(panels)), 'teamMatched': True,
                       'bilingualNameMatched': False, 'knowledgePanelMatched': True})
    eligible = [p for p in proofs if p['teamMatched']]
    if not eligible or len({normalize(p['korean']) for p in eligible}) != 1:
        return None
    proof = {**eligible[0], 'url': url, 'domain': 'google.com', 'engines': ['google'],
             'contentHash': hashlib.sha256(page.text.encode()).hexdigest()}
    return {'name': row['name'], 'korean': proof['korean'], 'team': team,
            'league': row.get('league'), 'method': POLICY, 'sources': [proof]}


def resolve(row, get=fetch_page, team_dictionary=None):
    query = row['name'] + ' ' + (row.get('team') or '')
    urls = {'google': 'https://www.google.com/search?' + urllib.parse.urlencode({'q': query, 'hl': 'ko'}),
            'naver': 'https://search.naver.com/search.naver?' + urllib.parse.urlencode({'query': query})}
    found, searches, errors = {}, {}, []
    for engine, url in urls.items():
        try:
            page = get(url)
            if engine == 'google':
                approved = google_result(row, url, page, team_dictionary or {})
                if approved:
                    return approved, {'searches': {'google': {'url': url, 'status': 'direct-name-result'}},
                                      'sourceErrors': [], 'status': 'verified'}
            links = search_links(page, engine)
            searches[engine] = {'url': url, 'status': 'results' if links else 'no-readable-trusted-results'}
            for link, title in links:
                item = found.setdefault(link, {'title': title, 'engines': set()})
                item['engines'].add(engine)
        except (ValueError, OSError, urllib.error.URLError) as exc:
            searches[engine] = {'url': url, 'status': 'unavailable', 'reason': type(exc).__name__}
    proofs = []
    for url, result in found.items():
        try:
            proofs.extend(evidence(row, url, get(url), result['title'], result['engines'], team_dictionary or {}))
        except (ValueError, OSError, urllib.error.URLError) as exc:
            errors.append({'url': url, 'reason': type(exc).__name__})
    approved = verify(row, proofs)
    return approved, {'searches': searches, 'sourceErrors': errors, 'status': 'verified' if approved else 'needs-verification'}


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    inventory = read(ROOT / 'scripts/player-name-live-inventory.json', {})
    if not inventory.get('records') or now - dt.datetime.fromisoformat(inventory['at'].replace('Z', '+00:00')) > dt.timedelta(hours=2):
        raise ValueError('Fresh non-empty player inventory required')
    approved_path = ROOT / 'scripts/player-name-auto-review.json'
    state_path = ROOT / 'scripts/player-name-search-state.json'
    approved = read(approved_path, {'schemaVersion': 1, 'entries': []})
    state = read(state_path, {'schemaVersion': 1, 'players': {}})
    known = {normalize(r['name']) for r in approved['entries']}
    pending = {}
    for row in inventory['records']:
        if re.search(r'[a-zA-Z]', row['name']) and normalize(row['name']) == normalize(row.get('korean', row['name'])) and normalize(row['name']) not in known:
            pending.setdefault(row['name'], row)
    contexts = {}
    for row in inventory['records']:
        if row.get('team'):
            contexts.setdefault(normalize(row['name']), set()).add(normalize(row['team']))
    eligible = [row for name, row in pending.items()
                if len(contexts.get(normalize(name), set())) == 1
                and (state['players'].get(name, {}).get('policy') != POLICY
                     or state['players'].get(name, {}).get('nextCheckAt', '') <= now.isoformat())]
    eligible.sort(key=lambda row: (state['players'].get(row['name'], {}).get('checkedAt', ''), row['name']))
    teams = read(ROOT / 'dist/team-ko.json', {})
    checked = added = 0
    for row in eligible[:5]:
        entry, report = resolve(row, team_dictionary=teams)
        if entry:
            entry['verifiedAt'] = now.isoformat()
            approved['entries'].append(entry)
            added += 1
        delay = dt.timedelta(days=7) if any(s['status'] == 'results' for s in report['searches'].values()) else dt.timedelta(hours=6)
        state['players'][row['name']] = {**report, 'policy': POLICY, 'checkedAt': now.isoformat(), 'nextCheckAt': (now + delay).isoformat()}
        checked += 1
        write(approved_path, approved)
        write(state_path, state)
        # Do not keep issuing queries when both providers deny usable results.
        if all(s['status'] != 'results' for s in report['searches'].values()):
            break
        time.sleep(2)
    print(json.dumps({'pending': len(pending), 'checked': checked, 'approved': added, 'policy': 'Unverified names remain English'}))
    if checked and not added:
        print('::warning::No names passed independent source verification. See player-name-search-state.json; search access may be blocked.')


if __name__ == '__main__':
    main()

import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('resolver', Path(__file__).with_name('resolve-player-names.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class NameVerification(unittest.TestCase):
    row = {'name': 'Moritz Nicolas', 'team': 'Borussia Monchengladbach', 'league': 'bundesliga'}
    def page(self, korean='모리츠 니콜라스', english='Moritz Nicolas', team='Borussia Monchengladbach'):
        return r.Page(f'<title>{korean} - 선수 프로필</title><h1>{korean}</h1><p>{korean} ({english}) {team}</p>')
    def proof(self, url, **kwargs):
        return r.evidence(self.row, url, self.page(**kwargs), '', {'naver'}, {})
    def test_two_sources_same_identity(self):
        proof = self.proof('https://ko.wikipedia.org/wiki/Test') + self.proof('https://www.transfermarkt.co.kr/test')
        self.assertEqual(r.verify(self.row, proof)['korean'], '모리츠 니콜라스')
    def test_same_domain_not_independent(self):
        proof = self.proof('https://ko.wikipedia.org/wiki/A') + self.proof('https://en.wikipedia.org/wiki/B')
        self.assertIsNone(r.verify(self.row, proof))
    def test_conflict_stays_english(self):
        proof = self.proof('https://ko.wikipedia.org/wiki/A') + self.proof('https://www.transfermarkt.co.kr/B', korean='모리츠 니콜라스스')
        self.assertIsNone(r.verify(self.row, proof))
    def test_wrong_full_name_rejected(self):
        self.assertEqual(self.proof('https://ko.wikipedia.org/wiki/A', english='Other Nicolas'), [])
    def test_wrong_team_rejected(self):
        proof = self.proof('https://ko.wikipedia.org/wiki/A', team='Other FC') + self.proof('https://www.transfermarkt.co.kr/B', team='Other FC')
        self.assertIsNone(r.verify(self.row, proof))
    def test_search_excerpt_not_evidence(self):
        self.assertEqual(r.evidence(self.row, 'https://ko.wikipedia.org/wiki/A', r.Page('<p>No player information</p>'), '모리츠 니콜라스', {'google'}, {}), [])
    def test_both_engines_attempted_with_failure(self):
        calls=[]
        def get(url):
            calls.append(url)
            raise ValueError('search-challenge')
        approved, report=r.resolve(self.row,get)
        self.assertIsNone(approved)
        self.assertEqual(len(calls),2)
        self.assertEqual(set(report['searches']),{'google','naver'})
        self.assertTrue(all(x['status']=='unavailable' for x in report['searches'].values()))
    def test_safe_links_and_html(self):
        page=r.Page('<script>fake player</script><a href="/url?q=https%3A%2F%2Fko.wikipedia.org%2Fwiki%2FA">모리츠 니콜라스</a><a href="http://127.0.0.1/private">bad</a>')
        self.assertNotIn('fake player',page.text)
        self.assertEqual(r.search_links(page,'google'),[('https://ko.wikipedia.org/wiki/A','모리츠 니콜라스')])
        self.assertIsNone(r.source_domain('https://wikipedia.org.evil.test/A'))
        self.assertIsNone(r.source_domain('https://user:password@wikipedia.org/A'))
    def test_pipeline_with_public_sources(self):
        def get(url):
            if 'google.com/search' in url or 'search.naver.com' in url:
                return r.Page('<a href="https://ko.wikipedia.org/wiki/A">모리츠 니콜라스</a><a href="https://www.transfermarkt.co.kr/B">모리츠 니콜라스</a>')
            return self.page()
        approved, report=r.resolve(self.row,get)
        self.assertEqual(approved['korean'],'모리츠 니콜라스')
        self.assertEqual(approved['sources'][0]['engines'],['google','naver'])
        self.assertEqual(report['status'],'verified')

if __name__=='__main__': unittest.main()

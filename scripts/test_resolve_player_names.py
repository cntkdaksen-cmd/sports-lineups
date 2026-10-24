import importlib.util
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
import json
spec = importlib.util.spec_from_file_location('resolver', Path(__file__).with_name('resolve-player-names.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class NameVerification(unittest.TestCase):
    row = {'name': 'Moritz Nicolas', 'team': 'Borussia Monchengladbach', 'league': 'bundesliga'}
    def page(self, korean='모리츠 니콜라스', english='Moritz Nicolas', team='Borussia Monchengladbach'):
        return r.Page(f'<title>{korean} - 선수 프로필</title><h1>{korean}</h1><p>{korean} ({english}) {team}</p>')
    def proof(self, url, **kwargs):
        return r.evidence(self.row, url, self.page(**kwargs), '', {'naver'}, {})
    def test_asian_names_remain_distinct_for_search(self):
        self.assertEqual(r.normalize('尾形　崇斗'), '尾形 崇斗')
        self.assertEqual(r.normalize('岳政華'), '岳政華')
        self.assertNotEqual(r.normalize('尾形　崇斗'), r.normalize('石田　裕太郎'))
        self.assertNotEqual(r.normalize('ベイスターズ'), r.normalize('ヘイスターズ'))
    def test_google_result_registers_without_second_source(self):
        calls=[]
        def get(url):
            calls.append(url)
            return self.page()
        approved, report=r.resolve(self.row,get)
        self.assertEqual(approved['method'],'google-search-result-v1')
        self.assertEqual(approved['korean'],'모리츠 니콜라스')
        self.assertEqual(len(calls),1)
        self.assertEqual(report['status'],'verified')
    def test_google_knowledge_panel(self):
        page=r.Page('<div data-attrid="title"><span>모리츠 니콜라스</span></div><p>Moritz Nicolas Borussia Monchengladbach</p>')
        self.assertEqual(r.google_result(self.row,'https://www.google.com/search?q=test',page,{})['korean'],'모리츠 니콜라스')
    def test_google_wrong_identity_rejected(self):
        for page in (self.page(english='Other Nicolas'), self.page(team='Other FC'), r.Page('<h1>모리츠 니콜라스</h1>')):
            self.assertIsNone(r.google_result(self.row,'https://www.google.com/search?q=test',page,{}))
    def test_google_conflicting_names_rejected(self):
        page=r.Page('<h1>모리츠 니콜라스</h1><h1>모리츠 니콜라스스</h1><p>모리츠 니콜라스 (Moritz Nicolas) 모리츠 니콜라스스 (Moritz Nicolas) Borussia Monchengladbach</p>')
        self.assertIsNone(r.google_result(self.row,'https://www.google.com/search?q=test',page,{}))
    def test_bulk_language_links_and_identity(self):
        row={'name':'Alex Iwobi','team':'Fulham','league':'epl'}
        def data(intro='Alexander Chuka Iwobi plays football for Fulham.', ko='앨릭스 이워비'):
            return {'query':{'pages':{'1':{'title':'Alex Iwobi','extract':intro,'langlinks':[{'lang':'ko','*':ko}]}}}}
        approved,errors=r.bulk_wikipedia([row],{},lambda url:data())
        self.assertEqual(approved['alex iwobi']['korean'],'앨릭스 이워비')
        self.assertEqual(errors,[])
        self.assertEqual(r.bulk_wikipedia([row],{},lambda url:data('Nigerian professional footballer.'))[0]['alex iwobi']['korean'],'앨릭스 이워비')
        self.assertEqual(r.bulk_wikipedia([row],{},lambda url:data('Actor with no club'))[0],{})
        self.assertEqual(r.bulk_wikipedia([row],{},lambda url:data(ko='Alex Iwobi'))[0],{})
    def test_bulk_failure_is_reported(self):
        def get(url): raise ValueError('blocked')
        approved,errors=r.bulk_wikipedia([self.row],{},get)
        self.assertEqual(approved,{})
        self.assertTrue(errors)
    def test_priority_is_upcoming_starters_before_future_and_injury(self):
        now=r.dt.datetime(2026,10,24,tzinfo=r.dt.timezone.utc)
        state={'players':{}}
        rows=[{'name':'A','kind':'lineup','eventDate':'2026-10-28T01:00:00Z'},
              {'name':'B','kind':'injury','eventDate':'2026-10-24T01:00:00Z'},
              {'name':'Z','kind':'lineup','eventDate':'2026-10-24T01:00:00Z'}]
        self.assertEqual([x['name'] for x in sorted(rows,key=lambda x:r.priority(x,state,now))],['Z','B','A'])
    def test_google_h3_result(self):
        page=r.Page('<h3>모리츠 니콜라스</h3><p>모리츠 니콜라스 (Moritz Nicolas) Borussia Monchengladbach</p>')
        self.assertIsNotNone(r.google_result(self.row,'https://www.google.com/search?q=test',page,{}))
    def test_main_persists_multiple_google_approvals_and_deduplicates_accents(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'scripts').mkdir();(root/'dist').mkdir()
            now=r.dt.datetime.now(r.dt.timezone.utc).isoformat()
            records=[{'name':name,'korean':name,'team':'Test FC','kind':'lineup','eventDate':now} for name in ['Adrià Test','Adria Test','Other Person']]
            (root/'scripts/player-name-live-inventory.json').write_text(json.dumps({'at':now,'records':records}))
            (root/'dist/team-ko.json').write_text('{}')
            def resolve(row,**kw):
                return {'name':row['name'],'korean':'테스트','method':'google-search-result-v1','sources':[]},{'searches':{'google':{'status':'direct-name-result'}},'status':'verified'}
            with patch.object(r,'ROOT',root),patch.object(r,'bulk_wikipedia',return_value=({},[])),patch.object(r,'resolve',side_effect=resolve),patch.object(r.time,'sleep'):
                r.main()
            saved=json.loads((root/'scripts/player-name-auto-review.json').read_text())
            self.assertEqual(len(saved['entries']),2)
            self.assertEqual(json.loads((root/'scripts/player-name-run-report.json').read_text())['approved'],2)
    def test_new_bulk_policy_rechecks_names_before_search_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'scripts').mkdir();(root/'dist').mkdir()
            now=r.dt.datetime.now(r.dt.timezone.utc)
            name='Current Starter'
            (root/'scripts/player-name-live-inventory.json').write_text(json.dumps({'at':now.isoformat(),'records':[{'name':name,'korean':name,'team':'Test FC','kind':'lineup','eventDate':now.isoformat()}]}))
            (root/'scripts/player-name-search-state.json').write_text(json.dumps({'schemaVersion':1,'players':{r.normalize(name):{'policy':r.POLICY,'nextCheckAt':(now+r.dt.timedelta(days=1)).isoformat(),'nextBulkCheckAt':(now+r.dt.timedelta(days=1)).isoformat()}}}))
            (root/'dist/team-ko.json').write_text('{}')
            checked=[]
            def bulk(rows,teams):
                checked.extend(rows)
                return {},[]
            with patch.object(r,'ROOT',root),patch.object(r,'bulk_wikipedia',side_effect=bulk),patch.object(r,'resolve') as search:
                r.main()
            self.assertEqual([row['name'] for row in checked],[name])
            search.assert_not_called()
            state=json.loads((root/'scripts/player-name-search-state.json').read_text())
            self.assertEqual(state['players'][r.normalize(name)]['bulkPolicy'],r.BULK_POLICY)
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

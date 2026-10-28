import importlib.util
from pathlib import Path
import unittest
import tempfile
from unittest.mock import MagicMock, patch
import json
spec = importlib.util.spec_from_file_location('resolver', Path(__file__).with_name('resolve-player-names.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class NameVerification(unittest.TestCase):
    row = {'name': 'Moritz Nicolas', 'team': 'Borussia Monchengladbach', 'league': 'bundesliga'}
    def page(self, korean='모리츠 니콜라스', english='Moritz Nicolas', team='Borussia Monchengladbach'):
        return r.Page(f'<title>{korean} - 선수 프로필</title><h1>{korean}</h1><p>{korean} ({english}) {team}</p>')
    def proof(self, url, **kwargs):
        return r.evidence(self.row, url, self.page(**kwargs), '', {'google'}, {})
    def test_asian_names_remain_distinct_for_search(self):
        self.assertEqual(r.normalize('Łukasz Skorupski'),r.normalize('Lukasz Skorupski'))
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
    def test_google_redirect_shell_is_not_a_search_result(self):
        response=MagicMock()
        response.__enter__.return_value=response
        response.headers.get.return_value='text/html'
        response.headers.get_content_charset.return_value='utf-8'
        response.read.return_value='<title>Google Search</title><a href="/retry">여기</a>몇 초 안에 이동하지 않는 경우'.encode()
        opener=MagicMock()
        opener.open.return_value=response
        with patch.object(r.urllib.request,'build_opener',return_value=opener):
            with self.assertRaisesRegex(ValueError,'search-results-unavailable'):
                r.fetch_page('https://www.google.com/search?q=Moritz+Nicolas')
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
    def test_disambiguated_article_resolves_only_matching_sports_team(self):
        row={'name':'Tom Wilson','team':'Washington Capitals','league':'nhl'}
        def get(url,team='Washington Capitals',sport='ice hockey player'):
            if 'list=search' in url:
                return {'query':{'search':[{'title':'Tom Wilson (ice hockey)'},{'title':'Tom Wilson (actor)'}]}}
            return {'query':{'pages':{'1':{'title':'Tom Wilson (ice hockey)',
                'extract':f'Thomas Wilson is an {sport} for the {team}.',
                'langlinks':[{'lang':'ko','*':'톰 윌슨 (아이스하키 선수)'}]}}}}
        self.assertEqual(r.english_wikipedia_search(row,{},get)['korean'],'톰 윌슨')
        self.assertIsNone(r.english_wikipedia_search(row,{},lambda url:get(url,team='Other Club')))
        self.assertIsNone(r.english_wikipedia_search(row,{},lambda url:get(url,sport='actor')))
    def test_bulk_failure_is_reported(self):
        def get(url): raise ValueError('blocked')
        approved,errors=r.bulk_wikipedia([self.row],{},get)
        self.assertEqual(approved,{})
        self.assertTrue(errors)
    def test_korean_wikipedia_search_requires_exact_identity_sport_and_club(self):
        row={'name':'Miguel Gutiérrez','team':'Bayer Leverkusen','league':'bundesliga'}
        page={'title':'미겔 구티에레스','extract':'미겔 구티에레스는 바이어 04 레버쿠젠 소속 축구 선수이다.',
              'langlinks':[{'lang':'en','*':'Miguel Gutiérrez (footballer, born 2001)'}]}
        def get(url):
            if 'list=search' in url:
                return {'query':{'search':[{'title':'미겔 구티에레스'}]}}
            return {'query':{'pages':{'1':page}}}
        self.assertEqual(r.korean_wikipedia(row,{'Bayer Leverkusen':'바이어 04 레버쿠젠'},get)['korean'],'미겔 구티에레스')
        for changed in ({'extract':'미겔 구티에레스는 다른 구단 소속 축구 선수이다.'},
                        {'extract':'미겔 구티에레스는 바이어 04 레버쿠젠 소속 배우이다.'},
                        {'langlinks':[{'lang':'en','*':'Other Gutiérrez'}]}):
            with self.subTest(changed=changed):
                wrong={**page,**changed}
                def bad_get(url):
                    if 'list=search' in url: return {'query':{'search':[{'title':'미겔 구티에레스'}]}}
                    return {'query':{'pages':{'1':wrong}}}
                self.assertIsNone(r.korean_wikipedia(row,{'Bayer Leverkusen':'바이어 04 레버쿠젠'},bad_get))
    def test_wikidata_korean_label_for_exact_sports_article(self):
        row={'name':'Example Footballer','team':'Example FC','league':'epl'}
        calls=[]
        def get(url):
            calls.append(url)
            if 'wikidata.org' in url:
                return {'entities':{'Q123':{'labels':{'ko':{'language':'ko','value':'에밀리오 풋볼러'},
                    'en':{'language':'en','value':'Example Footballer'}}}}}
            return {'query':{'pages':{'1':{'title':'Example Footballer',
                'extract':'Example Footballer is a footballer for Example FC.',
                'pageprops':{'wikibase_item':'Q123'}}}}}
        approved,errors=r.bulk_wikipedia([row],{},get)
        self.assertEqual(errors,[])
        self.assertEqual(approved[r.normalize(row['name'])]['korean'],'에밀리오 풋볼러')
        self.assertEqual(approved[r.normalize(row['name'])]['method'],'wikidata-label-v1')
        self.assertEqual(len(calls),2)
        def wrong(url):
            data=get(url)
            if 'wikidata.org' in url: data['entities']['Q123']['labels']['en']['value']='Different Person'
            return data
        self.assertEqual(r.bulk_wikipedia([row],{},wrong)[0],{})
    def test_npb_hanzi_name_uses_japanese_article(self):
        row={'name':'牧　秀悟','team':'横浜DeNAベイスターズ','league':'npb'}
        urls=[]
        def get(url):
            urls.append(url)
            return {'query':{'pages':{'1':{'title':'牧秀悟','extract':'牧秀悟は日本のプロ野球選手。',
                    'langlinks':[{'lang':'ko','*':'마키 슈고'}]}}}}
        approved,errors=r.bulk_wikipedia([row],{},get)
        self.assertEqual(errors,[])
        self.assertIn('ja.wikipedia.org',urls[0])
        self.assertEqual(approved[r.normalize(row['name'])]['korean'],'마키 슈고')
        self.assertEqual(approved[r.normalize(row['name'])]['method'],'wikipedia-language-link-v2')
        self.assertEqual(r.bulk_wikipedia([row],{},lambda url:{'query':{'pages':{'1':{'title':'牧秀悟',
            'extract':'牧秀悟は俳優。','langlinks':[{'lang':'ko','*':'마키 슈고'}]}}}})[0],{})
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
            with patch.object(r,'ROOT',root),patch.object(r,'bulk_wikipedia',return_value=({},[])),patch.object(r,'korean_wikipedia',return_value=None),patch.object(r,'resolve',side_effect=resolve),patch.object(r.time,'sleep'):
                r.main()
            saved=json.loads((root/'scripts/player-name-auto-review.json').read_text())
            self.assertEqual(len(saved['entries']),2)
            self.assertEqual(json.loads((root/'scripts/player-name-run-report.json').read_text())['approved'],2)
    def test_main_continues_after_unreadable_google_result(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'scripts').mkdir();(root/'dist').mkdir()
            now=r.dt.datetime.now(r.dt.timezone.utc).isoformat()
            records=[{'name':name,'korean':name,'team':'Test FC','kind':'lineup','eventDate':now}
                     for name in ['First Player','Second Player']]
            (root/'scripts/player-name-live-inventory.json').write_text(json.dumps({'at':now,'records':records}))
            (root/'dist/team-ko.json').write_text('{}')
            def resolve(row,**kw):
                if row['name']=='First Player':
                    return None,{'searches':{'google':{'status':'no-readable-trusted-results'}},'status':'needs-verification'}
                return {'name':row['name'],'korean':'두 번째 선수','method':'google-search-result-v1','sources':[]},{'searches':{'google':{'status':'direct-name-result'}},'status':'verified'}
            with patch.object(r,'ROOT',root),patch.object(r,'bulk_wikipedia',return_value=({},[])),patch.object(r,'korean_wikipedia',return_value=None),patch.object(r,'resolve',side_effect=resolve) as search,patch.object(r.time,'sleep'):
                r.main()
            self.assertEqual(search.call_count,2)
            report=json.loads((root/'scripts/player-name-run-report.json').read_text())
            self.assertEqual((report['searchChecked'],report['approved']),(2,1))
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
    def test_only_google_attempted_with_failure(self):
        calls=[]
        def get(url):
            calls.append(url)
            raise ValueError('search-challenge')
        approved, report=r.resolve(self.row,get)
        self.assertIsNone(approved)
        self.assertEqual(len(calls),1)
        self.assertEqual(set(report['searches']),{'google'})
        self.assertTrue(all(x['status']=='unavailable' for x in report['searches'].values()))
    def test_safe_links_and_html(self):
        page=r.Page('<script>fake player</script><a href="/url?q=https%3A%2F%2Fko.wikipedia.org%2Fwiki%2FA">모리츠 니콜라스</a><a href="http://127.0.0.1/private">bad</a>')
        self.assertNotIn('fake player',page.text)
        self.assertEqual(r.search_links(page,'google'),[('https://ko.wikipedia.org/wiki/A','모리츠 니콜라스')])
        self.assertIsNone(r.source_domain('https://wikipedia.org.evil.test/A'))
        self.assertIsNone(r.source_domain('https://user:password@wikipedia.org/A'))
    def test_pipeline_with_public_sources(self):
        def get(url):
            if 'google.com/search' in url:
                return r.Page('<a href="https://ko.wikipedia.org/wiki/A">모리츠 니콜라스</a><a href="https://www.transfermarkt.co.kr/B">모리츠 니콜라스</a>')
            return self.page()
        approved, report=r.resolve(self.row,get)
        self.assertEqual(approved['korean'],'모리츠 니콜라스')
        self.assertEqual(approved['sources'][0]['engines'],['google'])
        self.assertEqual(report['status'],'verified')

if __name__=='__main__': unittest.main()

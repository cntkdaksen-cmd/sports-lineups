import importlib.util
from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime
from zoneinfo import ZoneInfo
spec = importlib.util.spec_from_file_location('projections', Path(__file__).with_name('update-projections.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class NpbSchedule(unittest.TestCase):
    def test_japan_series_times(self):
        self.assertEqual(m.npb_kickoff({'startTime': '1830'}, date(2026, 10, 24)), '2026-10-24T09:30:00Z')
        self.assertEqual(m.npb_kickoff({'startTime': '18:00'}, date(2026, 10, 25)), '2026-10-25T09:00:00Z')
    def test_tomorrow_abbreviations_use_known_full_names(self):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None): return cls(2026,10,24,12,tzinfo=ZoneInfo('Asia/Tokyo'))
        def get(url):
            if 'starting_members' in url: return {}
            if '20261024' in url: return [{'gameId':1,'startTime':'1830','homeTeamName':'横浜DeNAベイスターズ','visitorTeamName':'福岡ソフトバンクホークス','homeTeamNameI':'デ','visitorTeamNameI':'ソ','gameStateName':'試合終了'}]
            if '20261025' in url: return [{'gameId':2,'startTime':'1800','homeTeamNameI':'デ','visitorTeamNameI':'ソ'}]
            return []
        with patch.object(m,'datetime',Clock),patch.object(m,'fetch_json',side_effect=get):
            games=m.scrape_npb()
        self.assertEqual(len(games),2)
        self.assertEqual(games[1]['event']['date'],'2026-10-25T09:00:00Z')
        self.assertEqual(games[1]['prediction']['names']['away'],'福岡ソフトバンクホークス')
        self.assertTrue(games[0]['event']['status']['type']['completed'])
    def test_missing_and_placeholder_times_are_not_midnight(self):
        for value in (None, '', '0000', '未定', '2460', '18'):
            with self.assertRaises(ValueError):
                m.npb_kickoff({'startTime': value}, date(2026, 10, 24))

if __name__ == '__main__': unittest.main()

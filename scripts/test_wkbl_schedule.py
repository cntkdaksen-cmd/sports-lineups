import importlib.util
from pathlib import Path
from unittest import TestCase, main

spec = importlib.util.spec_from_file_location('projections_wkbl', Path(__file__).with_name('update-projections.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WKBLOfficialSchedule(TestCase):
    def test_official_monthly_schedule_keeps_home_side_and_kst_time(self):
        page = '<ul class="list_schedule"><li><span class="date">11.01</span>' \
               '<strong class="team_name">KB스타즈</strong><strong class="team_name">BNK 썸</strong>' \
               '<div class="place_block"><span>청주<br />16:00</span></div></li></ul>'
        rows = module.parse_wkbl_schedule(page, 2026, 11)
        self.assertEqual(rows, [{'date': '2026-11-01T07:00:00Z', 'home': 'KB스타즈', 'away': 'BNK 썸'}])
        self.assertEqual(module.parse_wkbl_schedule(page, 2026, 10), [])

    def test_missing_list_fails_instead_of_reporting_no_games(self):
        with self.assertRaises(ValueError):
            module.parse_wkbl_schedule('<html></html>', 2026, 11)


if __name__ == '__main__':
    main()

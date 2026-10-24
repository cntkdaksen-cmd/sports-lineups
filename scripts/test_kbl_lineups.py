import importlib.util
from pathlib import Path
from unittest import TestCase, main

spec = importlib.util.spec_from_file_location('projections_kbl', Path(__file__).with_name('update-projections.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KBLProjectedLineups(TestCase):
    def test_current_preview_table_keeps_home_and_away(self):
        def team(name, player):
            row = '<tr><td><a><span class="flex items-center gap-1.5 whitespace-nowrap font-medium">' + player + '</span></a></td><td>35.3</td></tr>'
            return '<h3 data-no-section-index="true" class="font-semibold">' + name + '</h3><table><tbody>' + row + '</tbody></table>'
        detail = team('서울 SK', '자밀 워니') + team('수원 KT', '허훈')
        lineups = module.kbl_projected_lineups(detail, ['서울 SK', '수원 KT'])
        self.assertEqual(lineups['home'][0]['name'], '자밀 워니')
        self.assertEqual(lineups['away'][0]['name'], '허훈')
        self.assertEqual(module.kbl_projected_lineups(team('다른 팀', '오류 선수'), ['서울 SK', '수원 KT']), {})


if __name__ == '__main__':
    main()

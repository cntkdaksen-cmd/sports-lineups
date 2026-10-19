# 스포츠 라인업

축구 7개 대회와 MLB, NBA의 경기별 한국시간 일정과 선발 명단을 표시하는 독립 프로젝트입니다.

- 공개 사이트: https://sports-lineups.fuzzyloach5.chatgpt.site/ (`.openai/hosting.json`)
- 화면: `dist/index.html`, `dist/app.js`, `dist/style.css`
- 선수 이름 한국어 표기: `dist/football-ko.js`
- 예상 명단 자료: `dist/projections.json`
- 예상 명단 갱신: `python3 scripts/update-projections.py`

경기 일정과 발표된 선발 명단은 ESPN 경기 데이터로 표시합니다. 발표 전에는 RotoWire 및 Starting 11에 게시된 예상 명단을 사용합니다. 자료원은 내부 갱신 스크립트에만 남기고 공개 페이지에는 표시하지 않습니다. 예상 명단은 마지막 갱신 시점의 스냅샷이므로 새 경기와 변경 사항은 갱신 스크립트를 다시 실행해야 반영됩니다.

이전 쇼츠 작업현황판의 사용하지 않는 라인업 코드는 `legacy/workboard-lineups/`에 보관합니다.

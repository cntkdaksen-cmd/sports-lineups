import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Execute the production dictionaries and rendering functions without network requests.
const element = {addEventListener() {}};
const context = vm.createContext({
  localStorage: {getItem() { return null; }},
  document: {documentElement: {dataset: {}}, getElementById() { return element; }, addEventListener() {}},
  window: {setInterval() {}}
});
for (const file of ['football-ko.js', 'player-ko.js', 'app.js']) {
  let source = fs.readFileSync(new URL(`../dist/${file}`, import.meta.url), 'utf8');
  if (file === 'app.js') source = source.replace(/loadGames\(\);\s*$/, '');
  vm.runInContext(source, context, {filename: file});
}
const run = code => vm.runInContext(code, context);
for (const [name, expected] of [
  ['Alisson Becker', '알리송 베커'], ['Alisson', '알리송 베커'],
  ['Onyeka Okongwu', '오니에카 오콩우'],
  ['Nickeil Alexander-Walker', '니킬 알렉산더워커'],
  ['Jayson Tatum', '제이슨 테이텀'],
  ['Kentavious Caldwell‑Pope', '켄타비우스 콜드웰-폽'],
  ['Joshua Kimmich', '요주아 키미히'],
  ['Sidney Crosby', '시드니 크로스비'],
  ['Shohei Ohtani', '오타니 쇼헤이'],
  ['Unknown Player', 'Unknown Player'], ['Alisson Santos', 'Alisson Santos'],
  ['Becker', 'Becker']
]) assert.equal(run(`translated(${JSON.stringify(name)})`), expected, name);
assert.equal(run(`translated('João Neves')`), run(`translated('Joao Neves')`));
for (const [name, korean] of run('Object.entries(playerKo)')) {
  context.checkedPlayer = {name};
  assert.equal(run('translated(checkedPlayer.name)'), korean, name);
  assert.ok(run(`teamCard({team:{displayName:'Team'},homeAway:'home'},[checkedPlayer]).includes(safe(translated(checkedPlayer.name)))`), `Lineup: ${name}`);
  assert.ok(run(`injuryPanel({injuryDetails:{home:[checkedPlayer]}},{}).includes(safe(translated(checkedPlayer.name)))`), `Injury: ${name}`);
}
assert.match(run(`teamCard({team:{displayName:'Liverpool'},homeAway:'home'},[{name:'Alisson Becker'}])`), /알리송 베커/);
assert.match(run(`injuryPanel({injuryDetails:{home:[{name:'Alisson Becker',status:'out'}]}},{})`), /알리송 베커/);
run(`language='en'`);
assert.equal(run(`translated('Alisson Becker')`), 'Alisson Becker');
assert.match(run(`teamCard({team:{displayName:'Liverpool'},homeAway:'home'},[{name:'Alisson Becker'}])`), /Alisson Becker/);
run(`language='ko'`);
const collisions = run(`Object.entries(naverKo).filter(([name,korean])=>naverKoNormalized[normalizePlayerName(name)]!==korean)`);
assert.equal(collisions.length, 0, `Conflicting normalized names: ${JSON.stringify(collisions)}`);
const reviewed = JSON.parse(fs.readFileSync(new URL('./player-name-source-review.json', import.meta.url), 'utf8')).entries;
assert.equal(new Set(reviewed.map(row=>row.name)).size, reviewed.length, 'Duplicate source review names');
for (const row of reviewed) {
  assert.ok(row.source.startsWith('https://'), `Missing source: ${row.name}`);
  assert.equal(run(`translated(${JSON.stringify(row.name)})`), row.korean, `Source review: ${row.name}`);
}
console.log(`Player names and both rendering paths passed. Reviewed dictionary: ${run('Object.keys(playerKo).length')} names/aliases.`);

// Unlike snapshot-only audits, this inventory also covers ESPN live starters,
// recent-game fallback starters and injury names collected by the actual renderers.
if (process.argv.includes('--inventory')) {
  const input = process.argv[process.argv.indexOf('--inventory') + 1];
  assert.ok(input, '--inventory requires a collected inventory path');
  const inventory = JSON.parse(fs.readFileSync(input, 'utf8'));
  const exceptions = JSON.parse(fs.readFileSync(new URL('./player-name-exceptions.json', import.meta.url), 'utf8')).entries;
  const allowed = new Set(exceptions.map(row => row.name));
  const names = [...new Map(inventory.records.map(row => [row.name, row])).values()];
  const pending = [], english = [];
  for (const row of names) {
    context.checkedPlayer = row;
    run(`language='ko'`);
    const korean = run('translated(checkedPlayer.name,checkedPlayer.short)');
    if (/\p{Script=Latin}/u.test(row.name) && korean === row.name) {
      (allowed.has(row.name) ? english : pending).push(row);
    }
    run(`language='en'`);
    if (/\p{Script=Latin}/u.test(row.name)) {
      assert.equal(run('translated(checkedPlayer.name,checkedPlayer.short)'), row.name.normalize('NFD').replace(/\p{M}/gu,''), `English: ${row.name}`);
    }
  }
  run(`language='ko'`);
  const report = {collectedAt:inventory.at, totalNames:names.length, mapped:names.length-pending.length-english.length, reviewedEnglish:english, pending, fetchFailures:inventory.failures};
  fs.writeFileSync(new URL('./player-name-live-audit.json', import.meta.url), JSON.stringify(report,null,2)+'\n');
  console.log(`Live inventory: ${report.totalNames} names; ${report.mapped} mapped, ${english.length} reviewed English exceptions, ${pending.length} unchecked.`);
  if (process.argv.includes('--require-reviewed')) {
    assert.equal(inventory.failures.length, 0, 'Inventory collection has fetch failures');
    assert.equal(pending.length, 0, `Unchecked live player names: ${pending.map(row=>row.name).join(', ')}`);
  }
}

// Audit every supplied league and date, including both injury data formats.
// A missing dictionary entry means "needs review", never "no Korean name exists".
if (process.argv.includes('--audit')) {
  const inputIndex = process.argv.indexOf('--input');
  const input = inputIndex < 0 ? new URL('../dist/projections.json', import.meta.url) : process.argv[inputIndex + 1];
  assert.ok(input, '--input requires a snapshot path');
  const snapshot = JSON.parse(fs.readFileSync(input, 'utf8'));
  const names = new Map();
  const predictions = [...(snapshot.items || []), ...Object.entries(snapshot.domestic || {}).flatMap(([league, games]) => games.map(game => ({...game.prediction, league})))];
  for (const prediction of predictions) {
    for (const side of ['home', 'away']) {
      for (const group of ['lineups', 'injuries', 'injuryDetails']) {
        for (const player of prediction[group]?.[side] || []) {
          const name = typeof player === 'string' ? player : player.name || player.player;
          if (!name || !/\p{Script=Latin}/u.test(name)) continue;
          if (!names.has(name)) names.set(name, new Set());
          names.get(name).add(prediction.league);
        }
      }
    }
  }
  const missing = [...names].filter(([name]) => run(`translated(${JSON.stringify(name)})`) === name).sort(([a], [b]) => a.localeCompare(b)).map(([name, leagues]) => ({
    name, leagues: [...leagues].sort(),
    google: `https://www.google.com/search?q=${encodeURIComponent(name)}`,
    naver: `https://search.naver.com/search.naver?query=${encodeURIComponent(name)}`,
    status: 'needs-source-review'
  }));
  const report = {snapshotAsOf: snapshot.asOf, totalLatinNames: names.size, translated: names.size - missing.length, missing};
  const output = new URL('../scripts/player-name-audit.json', import.meta.url);
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  console.log(`All leagues: ${report.translated}/${names.size} names mapped; ${missing.length} queued for source review.`);
}

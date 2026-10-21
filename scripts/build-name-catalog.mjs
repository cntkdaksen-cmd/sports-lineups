import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const read = path => JSON.parse(fs.readFileSync(new URL(path, root), 'utf8'));
const write = (path,value) => fs.writeFileSync(new URL(path,root),JSON.stringify(value,null,2)+'\n');
if (process.argv.includes('--queue')) {
  const entries = [];
  for (const [kind,path] of [['player','scripts/player-name-live-audit.json'],['team','scripts/team-name-live-audit.json']]) {
    if (!fs.existsSync(new URL(path,root))) continue;
    for (const row of read(path).pending || []) {
      const query = [row.name,row.team,row.league].filter(Boolean).join(' ');
      entries.push({...row,kind,google:`https://www.google.com/search?q=${encodeURIComponent(query)}`,naver:`https://search.naver.com/search.naver?query=${encodeURIComponent(query)}`});
    }
  }
  write('scripts/name-review-queue.json',{policy:'Confirm club/player identity and established Korean full name before approving. Do not publish search snippets automatically.',entries});
  console.log(`Name review queue: ${entries.length} unreviewed names.`);
} else {
  const teams = read('dist/team-ko.json');
  const review = read('scripts/team-name-review.json');
  for (const row of review.entries) teams[row.name]=row.korean;
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(new URL('dist/player-ko.js',root),'utf8'),context);
  const players = {...vm.runInContext('playerKo',context),...read('scripts/player-name-review.json').userOverrides};
  for (const dictionary of [teams,players]) {
    for (const [name,korean] of Object.entries(dictionary)) {
      assert.ok(name && typeof korean==='string' && korean.length<=160 && /\p{Script=Hangul}/u.test(korean),`Invalid approved name: ${name}`);
    }
  }
  const catalog = {schemaVersion:1,teams,players};
  write('dist/team-ko.json',teams);
  write('dist/name-catalog.json',catalog);
  console.log(`Approved name catalog: ${Object.keys(teams).length} team aliases, ${Object.keys(players).length} player aliases.`);
}

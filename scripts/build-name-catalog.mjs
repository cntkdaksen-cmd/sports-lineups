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
  const autoPath = new URL('scripts/player-name-auto-review.json',root);
  const automatic = {};
  if(fs.existsSync(autoPath)) for(const row of read('scripts/player-name-auto-review.json').entries) {
    if(row.method==='google-search-result-v1') {
      assert.ok(row.sources.length>=1 && row.sources.every(s=>{
        const url=new URL(s.url);
        return url.protocol==='https:' && url.hostname==='www.google.com' && url.pathname==='/search' && s.domain==='google.com' && s.teamMatched && (s.bilingualNameMatched || s.knowledgePanelMatched) && s.contentHash;
      }),'Google result needs player identity evidence');
    } else {
      assert.equal(row.method,'independent-bilingual-sources-v1');
      assert.ok(row.sources.length>=2 && new Set(row.sources.map(s=>s.domain)).size>=2 && row.sources.some(s=>s.teamMatched),'Automatic name needs independent identity evidence');
      assert.ok(row.sources.every(s=>s.bilingualNameMatched && /^https:\/\//.test(s.url)),'Automatic name lacks source evidence');
    }
    automatic[row.name]=row.korean;
  }
  // Human-reviewed spellings always take precedence over automated additions.
  vm.runInContext(fs.readFileSync(new URL('dist/football-ko.js',root),'utf8'),context);
  const manual={...vm.runInContext('footballKo',context),...vm.runInContext('playerKo',context),...read('scripts/player-name-review.json').userOverrides};
  const normalized=name=>name.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().replace(/[^a-z0-9]/g,'');
  const manualKeys=new Set(Object.keys(manual).map(normalized));
  const players = {...Object.fromEntries(Object.entries(automatic).filter(([name])=>!manualKeys.has(normalized(name)))),...manual};
  for (const dictionary of [teams,players]) {
    for (const [name,korean] of Object.entries(dictionary)) {
      assert.ok(name && typeof korean==='string' && korean.length<=160 && /\p{Script=Hangul}/u.test(korean),`Invalid approved name: ${name}`);
    }
  }
  const teamEnglish=Object.fromEntries(review.entries.filter(row=>row.english).map(row=>[row.name,row.english]));
  const catalog = {schemaVersion:1,teams,teamEnglish,players};
  write('dist/team-ko.json',teams);
  write('dist/name-catalog.json',catalog);
  console.log(`Approved name catalog: ${Object.keys(teams).length} team aliases, ${Object.keys(players).length} player aliases.`);
}

import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const elements=new Map();
const element=()=>({addEventListener(){},setAttribute(){},innerHTML:'',textContent:''});
const context=vm.createContext({document:{documentElement:{dataset:{}},getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},querySelector:element,addEventListener(){}},localStorage:{getItem(){return null;}},window:{setInterval(){}},atob,TextDecoder,Uint8Array});
for(const file of ['football-ko.js','player-ko.js','win-probability.js','app.js'])vm.runInContext(fs.readFileSync(new URL('../dist/'+file,import.meta.url),'utf8').replace(/loadGames\(\);\s*$/,''),context);
const run=code=>vm.runInContext(code,context);
run("sport='mlb'");
context.event={id:'test',date:new Date(Date.now()+3600000).toISOString(),competitions:[{competitors:[{homeAway:'home',team:{id:'8',displayName:'Milwaukee Brewers'},probables:[{name:'probableStartingPitcher',athlete:{displayName:'Jacob Misiorowski'}}]},{homeAway:'away',team:{id:'30',displayName:'Tampa Bay Rays'},probables:[{name:'probableStartingPitcher',athlete:{displayName:'Nick Martinez'}}]}]}]};
let card=run('gameCard(event,{},null,[])');
assert.match(card,/닉 마르티네스/);assert.match(card,/제이콥 미저라우스키/);assert.equal((card.match(/class="starting-pitcher"/g)||[]).length,2);
context.summary={boxscore:{players:[{team:{id:'8'},statistics:[{type:'pitching',athletes:[{starter:false,athlete:{displayName:'Reliever'}},{starter:true,athlete:{displayName:'Logan Henderson'}}]}]}]}};
assert.equal(run('summaryPitchers(summary,event).home.name'),'Logan Henderson');
assert.equal(run('summaryPitchers(summary,event).away'),undefined);
assert.equal(run("baseballPitcher(event.competitions[0].competitors[0],{startingPitchers:summaryPitchers(summary,event)}).name"),'Logan Henderson');
assert.match(run("pitcherMarkup({name:'Logan Henderson',status:'confirmed'})"),/로건 헨더슨.*확정/);
for(const league of ['mlb','kbo','npb','cpbl']){run(`sport='${league}'`);assert.equal(run("baseballPitcher({homeAway:'home',probables:[]},null)"),null);assert.match(run("pitcherMarkup(baseballPitcher({homeAway:'home'},null))"),/예고 전/);}
run("sport='nba'");assert.equal(run('baseballPitcher(event.competitions[0].competitors[0],null)'),undefined);assert.equal(run('pitcherMarkup(undefined)'),'');
const review=JSON.parse(fs.readFileSync(new URL('./fixtures/baseball-name-review.json',import.meta.url),'utf8'));
for(const row of review.entries){context.player=row;run("language='ko'");assert.equal(run('playerDisplayName(player.name)'),row.korean);run("language='en'");assert.equal(run('playerDisplayName(player.name)'),row.name);}
run("language='ko'");
const batters=Array.from({length:9},(_,i)=>({name:'Batter '+i}));context.batters=batters;
const html=run("teamCard({homeAway:'home',team:{displayName:'Team'}},batters,{name:'Logan Henderson',status:'probable'})");assert.equal((html.match(/<li>/g)||[]).length,9,'Pitcher must not change nine batting-order slots');assert.ok(html.indexOf('starting-pitcher')<html.indexOf('<ol>'));
console.log('Baseball: correct side, announced vs actual starter, reliever exclusion, nine-player batting order and 25 bilingual names passed.');

assert.equal(run('majorView'),true,'First visit defaults to major games');
context.majorStart=Date.now();context.majorEnd=context.majorStart+172800000;
context.majorRows=[...Array.from({length:5},(_,i)=>({key:'nba',event:{id:'nba'+i,date:new Date(context.majorStart+3600000+i*1000).toISOString(),competitions:[{}]}})),{key:'mlb',event:{id:'mlb1',date:new Date(context.majorStart+7200000).toISOString(),competitions:[{}]}},{key:'mlb',event:{id:'finished',date:new Date(context.majorStart+1000).toISOString(),status:{type:{completed:true}},competitions:[{}]}},{key:'mlb',event:{id:'later',date:new Date(context.majorEnd+1).toISOString(),competitions:[{}]}}];
context.majorRows.push(context.majorRows[0]);
const selected=run('majorGameRows(majorRows,majorStart,majorEnd)');
assert.equal(selected.length,4,'Deduplicate, remove finished/out-of-window games, show at most three per league');
assert.equal(selected.filter(row=>row.key==='nba').length,3);assert.equal(selected.filter(row=>row.key==='mlb').length,1);
console.log('Major games: default view, date window, completed-game exclusion, deduplication and league balance passed.');

for(const league of ['kbo','kbl','wkbl','kovo']){run(`sport='${league}'`);assert.equal(run("isKoreanPlayer({name:'Lee Jung-hoo',country:'Korea'})"),false);}
for(const league of ['kleague1','kleague2']){run(`sport='football';league='${league}'`);assert.equal(run("isKoreanPlayer({name:'Son Heung-min',nationality:'Korea Republic'})"),false);}
run("sport='football';league='epl'");assert.equal(run("isKoreanPlayer({name:'Son Heung-min'})"),true);
run("sport='mlb'");assert.equal(run("isKoreanPlayer({name:'Lee Jung-hoo'})"),true);assert.equal(run("isKoreanPlayer({name:'Foreign Player',country:'USA'})"),false);
console.log('Korean badges: domestic leagues excluded, overseas Korean players retained.');

context.injuries={injuryDetails:{home:[{name:'Nick Martinez',status:'questionable',part:'shoulder'}]}};
const injuryHtml=run('injuryPanel(injuries,event)');assert.match(injuryHtml,/<details class="injury-box"><summary>/);assert.doesNotMatch(injuryHtml,/<details[^>]*\bopen\b/);assert.match(injuryHtml,/닉 마르티네스/);assert.match(injuryHtml,/어깨/);
assert.match(run('gameCard(event,{},null,[])'),/--lineup-rows:1;--team-rows:3/);
console.log('Injuries: native disclosure defaults closed, preserves player/reason, and lineup row counts stay explicit.');

context.majorFixture={key:'mlb',event:{...context.event,date:new Date(Date.now()+86400000).toISOString()}};
run("recentLineups=async()=>({away:Array.from({length:9},()=>({name:'Yandy Diaz'})),home:Array.from({length:9},()=>({name:'Jackson Chourio'}))})");
const filled=await run('majorGameData(majorFixture,{items:[]},[])');assert.equal(filled.prediction.lineups.away.length,9);assert.equal(filled.prediction.lineups.home.length,9);assert.equal(filled.prediction.statuses.home,'predicted');assert.match(filled.prediction.note,/최근 경기/);
console.log('Major lineup regression: missing published lineups use the existing recent-starter fallback and remain predicted.');

const requests=[];context.fetch=async(url)=>{requests.push(String(url));return {ok:true,json:async()=>({items:[],domestic:{}})};};
await run('getProjections()');assert.equal(requests.length,1);assert.match(requests[0],/raw\.githubusercontent\.com/);assert.ok(!requests.some(url=>url.includes('api.github.com')),'Do not require GitHub API quota for public lineup snapshots');
console.log('Lineup feed: direct public snapshot works without the GitHub contents API.');

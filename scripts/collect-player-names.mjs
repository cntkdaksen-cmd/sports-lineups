import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const root=new URL('../',import.meta.url).pathname;
const arg=(flag,fallback)=>{const i=process.argv.indexOf(flag);return i<0?fallback:process.argv[i+1]};
const output=arg('--output',root+'scripts/player-name-live-inventory.json');
const cacheDir=arg('--cache-dir',null);if(cacheDir)fs.mkdirSync(cacheDir,{recursive:true});
const elements=new Map();const element=()=>({innerHTML:'',textContent:'',dataset:{},addEventListener(){},setAttribute(){}});
const records=[];const teams=new Map();let currentLeague='';const failures=[];
const cachedFetch=async url=>{
 if(String(url).includes('name-catalog.json'))return {ok:true,json:async()=>JSON.parse(fs.readFileSync(root+'/dist/name-catalog.json','utf8'))};
 const key=String(url).replace(/&v=\d+/,'');const file=cacheDir&&cacheDir+'/'+crypto.createHash('sha256').update(key).digest('hex')+'.json';
 if(file&&fs.existsSync(file)){const body=fs.readFileSync(file,'utf8');return {ok:true,json:async()=>JSON.parse(body)};}
 try{const response=await fetch(url,{signal:AbortSignal.timeout(20000)});if(!response.ok)throw Error(`HTTP ${response.status}`);const body=await response.text();JSON.parse(body);if(file)fs.writeFileSync(file,body);return {ok:true,json:async()=>JSON.parse(body)};}
 catch(error){failures.push({league:currentLeague,url:key,error:String(error)});return {ok:false,status:0,json:async()=>({})};}
};
const document={documentElement:{dataset:{}},getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id)},querySelector(){return element()},addEventListener(){}};
const ctx=vm.createContext({document,localStorage:{getItem(){return null}},window:{setInterval(){}},fetch:cachedFetch,atob,TextDecoder,Uint8Array,console});
for(const file of ['football-ko.js','player-ko.js','app.js'])vm.runInContext(fs.readFileSync(root+'/dist/'+file,'utf8').replace(/loadGames\(\);\s*$/,''),ctx);
ctx.record=(player,kind,team)=>{const name=typeof player==='string'?player:player.name;if(name)records.push({name,team:team?.team?.displayName,short:player.short,league:currentLeague,kind,korean:vm.runInContext(`translated(${JSON.stringify(name)},${JSON.stringify(player.short)})`,ctx)});};
ctx.recordTeam=team=>{const name=team.team.displayName;teams.set(currentLeague+':'+name,{name,short:team.team.shortDisplayName,league:currentLeague,korean:vm.runInContext(`teamDisplayName(${JSON.stringify(team.team)})`,ctx)});};
vm.runInContext(`const originalTeamCard=teamCard;teamCard=function(team,players){recordTeam(team);for(const p of players||[])record(p,'lineup',team);return originalTeamCard(team,players)};const originalInjuryPanel=injuryPanel;injuryPanel=function(prediction,event){for(const name of injuryNames(prediction))record(name,'injury');return originalInjuryPanel(prediction,event)};`,ctx);
const leagues=vm.runInContext(`Object.entries(sources).filter(([id])=>leagueIds.includes(id)).map(([id])=>({sport:'football',league:id})).concat(sports.filter(x=>x.id!=='football').map(x=>({sport:x.id,league:x.id})))`,ctx);
for(const item of leagues){currentLeague=item.league;vm.runInContext(`sport=${JSON.stringify(item.sport)};league=${JSON.stringify(item.league)};`,ctx);await vm.runInContext('loadGames()',ctx);const rendered=elements.get('games').innerHTML;console.log(item.league,records.filter(r=>r.league===item.league).length,rendered.includes('class="empty"')?rendered.replace(/<[^>]+>/g,'').slice(0,100):'loaded');fs.writeFileSync(output,JSON.stringify({at:new Date().toISOString(),leagues,records,teams:[...teams.values()],failures},null,2));}
const unique=[...new Map(records.map(r=>[r.name,r])).values()];console.log(JSON.stringify({total:unique.length,missing:unique.filter(r=>/\p{Script=Latin}/u.test(r.name)&&r.name===r.korean).length,failures:failures.length}));

if(failures.length)process.exitCode=1;

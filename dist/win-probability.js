// Transparent statistical estimates, not calibrated or live in-game probabilities.
const winProbability = (() => {
  const validRecord = record => record && ['wins','losses','draws'].every(key => Number.isFinite(record[key]) && record[key]>=0) && record.wins+record.losses+record.draws>0;
  const formRecord = results => {
    const known=(results||[]).filter(value=>['W','L','D'].includes(value)).slice(-5);
    return {wins:known.filter(value=>value==='W').length,losses:known.filter(value=>value==='L').length,draws:known.filter(value=>value==='D').length};
  };
  function strength(team) {
    const inputs=[[team.overall,.5],[formRecord(team.recent),.35],[team.venue,.15]].filter(([record])=>validRecord(record));
    if(!inputs.length)return {value:.5,available:false};
    const totalWeight=inputs.reduce((sum,[,weight])=>sum+weight,0);
    const value=inputs.reduce((sum,[record,weight])=>{
      const total=record.wins+record.losses+record.draws;
      return sum+weight*(record.wins+.5*record.draws+4)/(total+8);
    },0)/totalWeight;
    return {value,available:true};
  }
  function estimate({away={},home={},drawPrior=0}) {
    const a=strength(away),h=strength(home);
    // Temper log5 odds so a short winning streak does not imply near-certainty.
    const logit=value=>Math.log(value/(1-value));
    const homeConditional=1/(1+Math.exp(-.65*(logit(h.value)-logit(a.value))));
    const recent=[formRecord(away.recent),formRecord(home.recent)];
    const n=recent.reduce((sum,r)=>sum+r.wins+r.losses+r.draws,0);
    const draws=recent.reduce((sum,r)=>sum+r.draws,0);
    const draw=drawPrior>0?(draws+10*drawPrior)/(n+10):0;
    const raw=[(1-homeConditional)*(1-draw),draw,homeConditional*(1-draw)];
    const units=raw.map(value=>Math.floor(value*1000));
    const order=raw.map((value,index)=>({index,remainder:value*1000-units[index]})).sort((x,y)=>y.remainder-x.remainder);
    for(let i=0,remaining=1000-units.reduce((sum,value)=>sum+value,0);i<remaining;i++)units[order[i%3].index]++;
    return {away:units[0]/10,draw:units[1]/10,home:units[2]/10,coverage:Number(a.available)+Number(h.available),recentGames:n};
  }
  return {estimate,validRecord};
})();

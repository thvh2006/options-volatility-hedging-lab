import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const golden=JSON.parse(await fs.readFile(path.join(root,'outputs/workbook_golden.json'),'utf8'));
const results=JSON.parse(await fs.readFile(path.join(root,'outputs/research_results.json'),'utf8'));
const sources=JSON.parse(await fs.readFile(path.join(root,'configs/sources.json'),'utf8'));
const wb=Workbook.create(),names=['Overview','Inputs','Pricing','Tree','Hedge Ledger','Experiments','Path Data','Checks','Sources'];
const sh=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const num='#,##0.0000;(#,##0.0000);"-"';
const val=(s,c,v)=>{s.getRange(c).values=[[v]];if(typeof v==='number')s.getRange(c).format.font.color='#1756C0';};
const f=(s,c,v)=>{s.getRange(c).formulas=[['='+v]];s.getRange(c).format.font.color=v.includes('!')?'#238249':'#172D46';};
const label=(s,c,v)=>s.getRange(c).values=[[v]];
for(const [name,s] of Object.entries(sh)){
 s.showGridLines=false;s.getRange('A1:U320').format.font={name:'Arial',size:10,color:'#172D46'};
 s.getRange('A:B').format.columnWidth=2;s.getRange('C:C').format.columnWidth=43;s.getRange('D:D').format.columnWidth=18;s.getRange('E:U').format.columnWidth=15;
 s.getRange('C1:U320').format.rowHeight=21;s.getRange('C2').values=[[name]];s.getRange('C2').format.font={name:'Arial',size:15,bold:true,color:'#172D46'};
 label(s,'C3','Synthetic European options. USD per unit unless labelled. No observed market data.');
 s.getRange('C3:U3').format.font={name:'Arial',size:10,italic:true,color:'#627486'};s.getRange('D6:U310').setNumberFormat(num);
 if(!['Overview','Inputs'].includes(name))s.freezePanes.freezeRows(6);
}
const inp=sh.Inputs;
for(const [r,t,v] of [[5,'Option type','call'],[6,'Spot USD',100],[7,'Strike USD',100],[8,'Pricing maturity years',1],[9,'Pricing rate',.05],[10,'Pricing volatility',.2],[11,'Pricing dividend yield',0],[15,'IV target premium USD',10.450583572185565],[16,'IV upper bracket volatility',8],[21,'Hedge quantity in underlying units',1],[22,'Rebalance every grid steps',4],[23,'Hedge financing rate',.04],[24,'Hedge model volatility',.25],[25,'Spot fee bps',5],[26,'Half spread bps',0],[27,'Borrowing spread',0]]){label(inp,'C'+r,t);val(inp,'D'+r,v);}
inp.getRange('D5').dataValidation={rule:{type:'list',values:['call','put']}};
inp.getRange('D22').dataValidation={rule:{type:'list',values:['1','4','16','64']}};
for(const r of [9,10,11,16,23,24,27])inp.getRange('D'+r).setNumberFormat('0.00%');
f(inp,'D4','IF(AND(COUNT(D6:D11)=6,D6>0,D7>0,D8>=0,D10>=0,OR(D5="call",D5="put")),"VALID","Check pricing inputs")');label(inp,'C4','Pricing input status');
label(inp,'C20','Saved hedge path horizon years');f(inp,'D20',"'Path Data'!D4");
label(inp,'C19','Hedge input status');f(inp,'D19','IF(AND(D4="VALID",COUNT(D21:D27)=7,D21>0,D22>=1,D22=INT(D22),D24>0,D25>=0,D26>=0,D27>=0),"VALID","Check hedge inputs")');
label(inp,'F6','Pricing maturity, rate and dividend yield affect the calculator and tree.');
label(inp,'F8','Hedge uses the saved quarter-year path, its own financing rate and zero dividends.');
label(inp,'F10','Changing spot scales the saved path. It does not regenerate a stochastic process.');
label(inp,'F12','IV target is a separate assumed premium. It is not an observed quote.');
label(inp,'F15','Blue numbers are editable. Green formulas link sheets.');
label(inp,'F20','Hedge controls affect every cash-ledger row. No exchange margin is modelled.');
const I=r=>'Inputs!$D$'+r,pr=sh.Pricing;
const labs={6:'Discounted spot',7:'Discounted strike',8:'d1',9:'d2',10:'N d1',11:'N d2',12:'European call price',13:'European put price',14:'Selected option price',16:'Spot delta per unit',17:'Gamma per unit',18:'Vega per one volatility point',19:'Theta per calendar day',20:'Rho per one rate point',22:'Hedge initial premium per unit'};
for(const [r,t] of Object.entries(labs))label(pr,'C'+r,t);
f(pr,'D6',`${I(6)}*EXP(-${I(11)}*${I(8)})`);f(pr,'D7',`${I(7)}*EXP(-${I(9)}*${I(8)})`);
f(pr,'D8',`IF(OR(${I(8)}=0,${I(10)}=0),"n.a.",(LN(${I(6)}/${I(7)})+(${I(9)}-${I(11)}+${I(10)}^2/2)*${I(8)})/(${I(10)}*SQRT(${I(8)})))`);
f(pr,'D9',`IF(ISNUMBER(D8),D8-${I(10)}*SQRT(${I(8)}),"n.a.")`);
for(const [r,d] of [[10,8],[11,9]])f(pr,'D'+r,`IF(ISNUMBER(D${d}),NORM.S.DIST(D${d},TRUE),"n.a.")`);
f(pr,'D12',`IF(Inputs!D4<>"VALID","Check inputs",IF(OR(${I(8)}=0,${I(10)}=0),MAX(D6-D7,0),D6*D10-D7*D11))`);
f(pr,'D13',`IF(Inputs!D4<>"VALID","Check inputs",IF(OR(${I(8)}=0,${I(10)}=0),MAX(D7-D6,0),D7*NORM.S.DIST(-D9,TRUE)-D6*NORM.S.DIST(-D8,TRUE)))`);
f(pr,'D14',`IF(${I(5)}="call",D12,D13)`);
const smooth=`AND(ISNUMBER(D8),Inputs!D4="VALID")`;
f(pr,'D16',`IF(${smooth},EXP(-${I(11)}*${I(8)})*(IF(${I(5)}="call",D10,D10-1)),"n.a.")`);
f(pr,'D17',`IF(${smooth},EXP(-${I(11)}*${I(8)})*NORM.S.DIST(D8,FALSE)/(${I(6)}*${I(10)}*SQRT(${I(8)})),"n.a.")`);
f(pr,'D18',`IF(${smooth},D6*NORM.S.DIST(D8,FALSE)*SQRT(${I(8)})*0.01,"n.a.")`);
f(pr,'D19',`IF(${smooth},(-D6*NORM.S.DIST(D8,FALSE)*${I(10)}/(2*SQRT(${I(8)}))+IF(${I(5)}="call",-${I(9)}*D7*D11+${I(11)}*D6*D10,${I(9)}*D7*NORM.S.DIST(-D9,TRUE)-${I(11)}*D6*NORM.S.DIST(-D8,TRUE)))/365,"n.a.")`);
f(pr,'D20',`IF(${smooth},IF(${I(5)}="call",D7*${I(8)}*D11,-D7*${I(8)}*NORM.S.DIST(-D9,TRUE))*0.01,"n.a.")`);
// Hedge premium owns a separate maturity/rate/volatility calculation, q=0.
label(pr,'F22','Hedge d1');f(pr,'G22',`(LN(${I(6)}/${I(7)})+(${I(23)}+${I(24)}^2/2)*${I(20)})/(${I(24)}*SQRT(${I(20)}))`);
label(pr,'F23','Hedge d2');f(pr,'G23',`G22-${I(24)}*SQRT(${I(20)})`);
f(pr,'D22',`IF(${I(5)}="call",${I(6)}*NORM.S.DIST(G22,TRUE)-${I(7)}*EXP(-${I(23)}*${I(20)})*NORM.S.DIST(G23,TRUE),${I(7)}*EXP(-${I(23)}*${I(20)})*NORM.S.DIST(-G23,TRUE)-${I(6)}*NORM.S.DIST(-G22,TRUE))`);
label(pr,'C25','IV solver status');
f(pr,'D25',`IF(${I(8)}=0,"EXPIRED_NO_IV",IF(OR(${I(15)}<IF(${I(5)}="call",MAX(D6-D7,0),MAX(D7-D6,0)),${I(15)}>=IF(${I(5)}="call",D6,D7)),"PRICE_BOUNDARY_OR_INVALID",IF(ABS(H88)<0.00000001,"CONVERGED","BRACKET_OR_ITERATION_LIMIT")))`);
label(pr,'C26','Solved IV decimal');f(pr,'D26','IF(D25="CONVERGED",F88,"n.a.")');pr.getRange('D26').setNumberFormat('0.0000%');
label(pr,'C27','Repricing residual USD');f(pr,'D27','H88');
pr.getRange('C28:L28').values=[['Iteration','Lower vol','Upper vol','Mid vol','Model price','Residual','Next lower','Next upper','d1','d2']];
for(let row=29;row<=88;row++){
 val(pr,'C'+row,row-28);f(pr,'D'+row,row===29?'0':'I'+(row-1));f(pr,'E'+row,row===29?I(16):'J'+(row-1));f(pr,'F'+row,`(D${row}+E${row})/2`);
 f(pr,'K'+row,`IF(${I(8)}=0,0,(LN(${I(6)}/${I(7)})+(${I(9)}-${I(11)}+F${row}^2/2)*${I(8)})/(F${row}*SQRT(${I(8)})))`);
 f(pr,'L'+row,`K${row}-F${row}*SQRT(${I(8)})`);
 f(pr,'G'+row,`IF(${I(8)}=0,IF(${I(5)}="call",MAX(${I(6)}-${I(7)},0),MAX(${I(7)}-${I(6)},0)),IF(${I(5)}="call",$D$6*NORM.S.DIST(K${row},TRUE)-$D$7*NORM.S.DIST(L${row},TRUE),$D$7*NORM.S.DIST(-L${row},TRUE)-$D$6*NORM.S.DIST(-K${row},TRUE)))`);
 f(pr,'H'+row,`G${row}-${I(15)}`);f(pr,'I'+row,`IF(H${row}<0,F${row},D${row})`);f(pr,'J'+row,`IF(H${row}>=0,F${row},E${row})`);
}
const tr=sh.Tree,columns=Array.from({length:17},(_,i)=>String.fromCharCode(68+i));
label(tr,'C4','Small tree European price');label(tr,'C5','Steps fixed for visible tree');val(tr,'D5',16);
label(tr,'F4','dt');f(tr,'G4',`${I(8)}/D5`);label(tr,'F5','Up factor');f(tr,'G5',`EXP(${I(10)}*SQRT(G4))`);label(tr,'I5','Down factor');f(tr,'J5','1/G5');
label(tr,'F6','Risk-neutral probability');f(tr,'G6',`IF(G5=J5,"n.a.",(EXP((${I(9)}-${I(11)})*G4)-J5)/(G5-J5))`);
label(tr,'F7','Tree validity');f(tr,'G7',`IF(OR(${I(8)}=0,${I(10)}=0),"DETERMINISTIC",IF(AND(G6>=0,G6<=1),"VALID","INCREASE_STEPS"))`);
for(let level=0;level<=16;level++){
 const col=columns[level];val(tr,col+'9',level);val(tr,col+'38',level);
 for(let j=0;j<=level;j++)f(tr,col+(10+j),`${I(6)}*$G$5^${j}*$J$5^${level-j}`);
}
for(let level=16;level>=0;level--)for(let j=0;j<=level;j++){
 const c=columns[level],next=columns[level+1];
 const calc=level===16?`IF(${I(5)}="call",MAX(${c}${10+j}-${I(7)},0),MAX(${I(7)}-${c}${10+j},0))`:`EXP(-${I(9)}*$G$4)*((1-$G$6)*${next}${40+j}+$G$6*${next}${41+j})`;
 f(tr,c+(40+j),`IF($G$7="VALID",${calc},"n.a.")`);
}
f(tr,'D4','IF(G7="DETERMINISTIC",Pricing!D14,IF(G7="VALID",D40,"n.a."))');label(tr,'C8','Underlying price lattice');label(tr,'C37','Backward option-value lattice');
const pd=sh['Path Data'];label(pd,'C4','Original path horizon years');val(pd,'D4',.25);pd.getRange('C6:E6').values=[['Step','Years elapsed','Saved spot ratio']];
for(const [i,s] of golden.path.entries()){const row=7+i;pd.getRange('C'+row+':E'+row).values=[[i,i/256*.25,s/100]];}
label(pd,'G7','Synthetic saved path, seed94000. Normalised to100 at inception.');label(pd,'G9','Not a market history. Changing horizon would require a new path source.');
const hl=sh['Hedge Ledger'];hl.getRange('C:C').format.columnWidth=8;hl.getRange('D:S').format.columnWidth=16;
hl.getRange('C6:S6').values=[['Step','Years','Spot USD','Remaining years','Target delta','Target units','Trade units','Opening cash','Interest','Option cash','Hedge cash','Costs','Closing cash','Holding units','Option liability','Net wealth USD','Cash roll residual']];hl.getRange('C6:S6').format.wrapText=true;hl.getRange('C6:S6').format.rowHeight=38;
const end=7+256;
for(let i=0;i<=256;i++){
 const row=7+i,prev=row-1;f(hl,'C'+row,`'Path Data'!C${row}`);f(hl,'D'+row,`'Path Data'!D${row}`);f(hl,'E'+row,`${I(6)}*'Path Data'!E${row}`);f(hl,'F'+row,`MAX(${I(20)}-D${row},0)`);
 const d1=`(LN(E${row}/${I(7)})+(${I(23)}+${I(24)}^2/2)*F${row})/(${I(24)}*SQRT(F${row}))`;
 f(hl,'G'+row,i===256?'0':`NORM.S.DIST(${d1},TRUE)-IF(${I(5)}="put",1,0)`);
 f(hl,'H'+row,i===256?'0':`IF(MOD(C${row},${I(22)})=0,G${row}*${I(21)},${i?'P'+prev:'0'})`);
 f(hl,'I'+row,`H${row}-${i?'P'+prev:'0'}`);f(hl,'J'+row,i?'O'+prev:'0');
 f(hl,'K'+row,i?`J${row}*(EXP((${I(23)}+IF(J${row}<0,${I(27)},0))*(D${row}-D${prev}))-1)`:'0');
 f(hl,'L'+row,i===0?`Pricing!D22*${I(21)}`:i===256?`-IF(${I(5)}="call",MAX(E${row}-${I(7)},0),MAX(${I(7)}-E${row},0))*${I(21)}`:'0');
 f(hl,'M'+row,`-I${row}*E${row}`);f(hl,'N'+row,`ABS(I${row})*E${row}*(${I(25)}+${I(26)})/10000`);f(hl,'O'+row,`SUM(J${row}:M${row})-N${row}`);f(hl,'P'+row,'H'+row);
 const d2=`(${d1}-${I(24)}*SQRT(F${row}))`;
 f(hl,'Q'+row,i===256?'0':`IF(${I(5)}="call",E${row}*NORM.S.DIST(${d1},TRUE)-${I(7)}*EXP(-${I(23)}*F${row})*NORM.S.DIST(${d2},TRUE),${I(7)}*EXP(-${I(23)}*F${row})*NORM.S.DIST(-${d2},TRUE)-E${row}*NORM.S.DIST(-${d1},TRUE))*${I(21)}`);
 f(hl,'R'+row,`O${row}+P${row}*E${row}-Q${row}`);f(hl,'S'+row,`O${row}-(J${row}+K${row}+L${row}+M${row}-N${row})`);
}
label(hl,'C4','Target delta is a close instruction of zero at expiry. Hedge dividends fixed to zero.');
const ex=sh.Experiments;label(ex,'C4','Saved Python experiments. Do not recalculate from the workbook inputs.');
const fields=['realised_vol','rebalance_every','fee_bps','mean_error','standard_deviation','rmse','mean_cost','mean_trade_count'];ex.getRange('C6:J6').values=[fields.map(k=>k.replaceAll('_',' '))];
ex.getRange('C7:J42').values=results.hedge_cases.map(r=>fields.map(k=>r[k]));ex.getRange('C7:C42').setNumberFormat('0.0%');
label(ex,'C45','Monte Carlo imported benchmark');label(ex,'C46','Antithetic pair observations');val(ex,'D46',results.benchmark.monte_carlo.independent_pairs);label(ex,'C47','Price USD');val(ex,'D47',results.benchmark.monte_carlo.price);label(ex,'C48','Standard error USD');val(ex,'D48',results.benchmark.monte_carlo.standard_error);
const checks=sh.Checks;checks.getRange('C6:E6').values=[['Independent diagnostic','Difference / value','Tolerance']];
for(const [r,t,calc,tol] of [[7,'Put call parity','Pricing!D12-Pricing!D13-(Pricing!D6-Pricing!D7)',1e-9],[8,'Hedge terminal holdings',`'Hedge Ledger'!P${end}`,1e-9],[9,'Hedge total cash reconciliation',`'Hedge Ledger'!O${end}-SUM('Hedge Ledger'!K7:M${end})+SUM('Hedge Ledger'!N7:N${end})`,1e-8],[10,'Maximum row cash-roll difference',`MAX(MAX('Hedge Ledger'!S7:S${end}),-MIN('Hedge Ledger'!S7:S${end}))`,1e-9],[11,'IV repricing residual','Pricing!D27',1e-8]]){label(checks,'C'+r,t);f(checks,'D'+r,calc);val(checks,'E'+r,tol);}
checks.getRange('D7:E11').setNumberFormat('0.00E+00');label(checks,'C14','Checks observe calculations and never feed a price, hedge decision or status.');
const ov=sh.Overview;label(ov,'C2','P5 option pricing and hedge accounting');
for(const [row,name,ref] of [[7,'Selected option premium USD','Pricing!D14'],[8,'Spot delta per unit','Pricing!D16'],[9,'Vega per volatility point','Pricing!D18'],[10,'Solved IV','Pricing!D26'],[12,'16 step European tree price','Tree!D4'],[15,'Saved-path hedge error USD',`'Hedge Ledger'!O${end}`],[16,'Total spot trading costs',`SUM('Hedge Ledger'!N7:N${end})`],[17,'Cash financing interest',`SUM('Hedge Ledger'!K7:K${end})`]]){label(ov,'C'+row,name);f(ov,'D'+row,ref);}
ov.getRange('D10').setNumberFormat('0.0000%');ov.getRange('D7:D17').format.font.color='#172D46';
label(ov,'C20','1. Edit Inputs for pricing, IV and hedge controls.');label(ov,'C22','2. Inspect Pricing, Tree and Hedge Ledger for calculations.');label(ov,'C24','3. Experiments contains saved Python scenarios, not live case outputs.');label(ov,'C26','No observed market quotes or investor returns. No venue margin emulation.');
ov.getRange('C34:D34').values=[['Path step','Active hedge net wealth USD']];for(let i=0;i<=256;i++){f(ov,'C'+(35+i),`'Hedge Ledger'!C${7+i}`);f(ov,'D'+(35+i),`'Hedge Ledger'!R${7+i}`);}
const chart=ov.charts.add('line',ov.getRange('C34:D291'));chart.title='Synthetic path hedge net wealth';chart.setPosition('F6','M25');chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;chart.hasLegend=false;chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:9}};chart.yAxis={numberFormatCode:'0.00',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:9}};
const so=sh.Sources;so.getRange('C6:F6').values=[['Source ID','Publisher','Use','URL']];so.getRange('C:C').format.columnWidth=28;so.getRange('D:D').format.columnWidth=20;so.getRange('E:E').format.columnWidth=70;so.getRange('F:F').format.columnWidth=75;
for(const [i,x] of sources.sources.entries()){so.getRange('C'+(7+i)+':F'+(7+i)).values=[[x.id,x.publisher,x.use,x.url]];so.getRange('C'+(7+i)+':F'+(7+i)).format.wrapText=true;so.getRange('C'+(7+i)+':F'+(7+i)).format.rowHeight=55;}
label(so,'C18','Price/path source: synthetic fixtures generated by this project.');label(so,'C20','Seed94000 and protocol are recorded in configs/research.json.');label(so,'C22','Observed venue market/derived data excluded. Independent human review not claimed.');
for(const [s,range] of [[ov,'C6:D6'],[hl,'C6:S6'],[ex,'C6:J6'],[pd,'C6:E6'],[checks,'C6:E6'],[so,'C6:F6']]){s.getRange(range).format.fill='#183B5B';s.getRange(range).format.font.color='#FFFFFF';}
ov.getRange('C6:D6').values=[['Calculation','Live result']];
tr.getRange('D9:T9').setNumberFormat('0');tr.getRange('D38:T38').setNumberFormat('0');
ex.getRange('D7:E42').setNumberFormat('0');
inp.getRange('D22').setNumberFormat('0');
so.getRange('F7:F14').format.font.size=9;so.getRange('C7:F14').format.rowHeight=75;
// Reject invalid editable inputs before a downstream numeric operation.
for(const row of [6,7,8,9,10,11,12,13,14,16,17,18,19,20]){
 const c=pr.getRange('D'+row),old=c.formulas[0][0];f(pr,'D'+row,`IF(Inputs!D4<>"VALID","Check pricing inputs",${old.slice(1)})`);
}
for(const col of ['G22','G23','D22']){const old=pr.getRange(col).formulas[0][0];f(pr,col,`IF(Inputs!D19<>"VALID","Check hedge inputs",${old.slice(1)})`);}
const ivValid='AND(Inputs!D4="VALID",COUNT(Inputs!D15:D16)=2,Inputs!D16>0)';
for(let row=29;row<=88;row++)for(const col of ['D','E','F','G','H','I','J','K','L']){const c=col+row,old=pr.getRange(c).formulas[0][0];f(pr,c,`IF(${ivValid},${old.slice(1)},"Check IV inputs")`);}
for(const row of [25,26,27]){const c='D'+row,old=pr.getRange(c).formulas[0][0];f(pr,c,`IF(${ivValid},${old.slice(1)},"Check IV inputs")`);}
for(let row=7;row<=end;row++)for(const col of ['E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']){const c=col+row,old=hl.getRange(c).formulas[0][0];f(hl,c,`IF(Inputs!D19="VALID",${old.slice(1)},"Check hedge inputs")`);}
for(const row of [15,16,17]){const c='D'+row,old=ov.getRange(c).formulas[0][0];f(ov,c,`IF(Inputs!D19="VALID",${old.slice(1)},"Check hedge inputs")`);}
const comparisons=[];
for(const g of golden.cases){
 for(const [r,v] of [[5,g.kind],[6,g.s],[7,g.k],[8,g.t],[9,g.r],[10,g.vol],[11,g.q],[15,g.price],[25,g.fee],[27,g.borrow]])val(inp,'D'+r,v);
 wb.recalculate();
 for(const [s,c,v,key] of [[pr,'D14',g.price,'price'],[tr,'D4',g.tree,'tree'],[pr,'D16',g.greeks.delta,'delta'],[pr,'D17',g.greeks.gamma,'gamma'],[pr,'D18',g.greeks.vega_per_vol_point,'vega'],[pr,'D19',g.greeks.theta_per_calendar_day,'theta'],[pr,'D20',g.greeks.rho_per_rate_point,'rho']]){
  const got=s.getRange(c).values[0][0];if(typeof got!=='number'||Math.abs(got-v)>1e-7)throw Error(`${g.kind} ${key}: ${got} != ${v}`);comparisons.push({case:g.kind+'-'+g.s,key,excel:got,python:v});
 }
 for(let i=0;i<=256;i++)for(const [col,key] of [['O','closing_cash'],['P','holding'],['N','costs'],['R','net_wealth']]){const got=hl.getRange(col+(7+i)).values[0][0],want=g.hedge.ledger[i][key];if(typeof got!=='number'||Math.abs(got-want)>1e-7)throw Error(`Ledger ${g.kind} ${i} ${key}: ${got} != ${want}`);}
}
const g=golden.cases[0];for(const [r,v] of [[5,g.kind],[6,g.s],[7,g.k],[8,g.t],[9,g.r],[10,g.vol],[11,g.q],[15,g.price],[25,g.fee],[27,g.borrow]])val(inp,'D'+r,v);wb.recalculate();
const initial=hl.getRange('O263').values[0][0];val(inp,'D25',20);wb.recalculate();if(!(hl.getRange('O263').values[0][0]<initial))throw Error('Costs do not reduce hedge cash');val(inp,'D25',5);wb.recalculate();
val(inp,'D24',0);wb.recalculate();if(hl.getRange('O263').values[0][0]!=='Check hedge inputs')throw Error('Zero hedge volatility not rejected');val(inp,'D24',.25);
val(inp,'D6',-1);wb.recalculate();if(pr.getRange('D14').values[0][0]!=='Check pricing inputs')throw Error('Invalid spot not rejected');val(inp,'D6',100);
val(inp,'D16',0);wb.recalculate();if(pr.getRange('D25').values[0][0]!=='Check IV inputs')throw Error('Invalid IV bracket not rejected');val(inp,'D16',8);wb.recalculate();
await fs.mkdir(path.join(root,'outputs/qa/spreadsheets'),{recursive:true});
for(const [name,range] of [['Overview','C2:M28'],['Inputs','C2:M28'],['Pricing','C2:L28'],['Tree','C2:T26'],['Tree','C37:T56'],['Hedge Ledger','C2:S18'],['Hedge Ledger','C248:S263'],['Experiments','C2:J22'],['Path Data','C2:J18'],['Checks','C2:J16'],['Sources','C2:F22']]){
 const blob=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(path.join(root,'outputs/qa/spreadsheets',name.replaceAll(' ','_')+'_'+range.split(':')[0]+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A',options:{useRegex:true,maxResults:20},maxChars:1500})).ndjson);
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(root,'outputs/P5_Options_Research_Model.xlsx'));
await fs.writeFile(path.join(root,'outputs/excel_checks.json'),JSON.stringify({pricing_comparisons:comparisons,ledger_comparisons:3*257*4,absolute_tolerance:1e-7,fee_perturbation_pass:true,exported_sheets:names.length},null,2)+'\n');console.log({pricing:comparisons.length,ledger:3*257*4,sheets:names.length});

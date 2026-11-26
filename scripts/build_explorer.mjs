import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {price} from '../dashboard/pricer.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const data={holdout:JSON.parse(await fs.readFile(path.join(root,'outputs/holdout_results.json'),'utf8')),results:JSON.parse(await fs.readFile(path.join(root,'outputs/research_results.json'),'utf8')),hedge:JSON.parse(await fs.readFile(path.join(root,'outputs/representative_hedge.json'),'utf8'))};
const golden=JSON.parse(await fs.readFile(path.join(root,'outputs/pricing_golden.json'),'utf8'));let worst=0;
for(const row of golden){const got=price(...row.inputs);worst=Math.max(worst,Math.abs(got-row.price));}
if(worst>1e-4)throw Error('Independent JavaScript pricing mismatch '+worst);
const model=(await fs.readFile(path.join(root,'dashboard/pricer.mjs'),'utf8')).replaceAll('export function','function');
const html=(await fs.readFile(path.join(root,'dashboard/template.html'),'utf8')).replace('/* PRICER */',()=>model).replace('/* DATA */',()=>`const DATA=${JSON.stringify(data).replaceAll('<','\\u003c')};`);
const elements={};for(const match of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)){
 const id=match[1];let v=match[0].match(/\bvalue="([^"]*)"/)?.[1]??({kind:'call',realised:'.25',fee:'5'}[id]??'');const handlers={};
 elements[id]={get value(){return v;},set value(x){v=String(x);},innerHTML:'',textContent:'',hidden:false,addEventListener:(k,f)=>handlers[k]=f,trigger:k=>handlers[k]?.()};
}
const document={getElementById:id=>{if(!elements[id])throw Error('Missing DOM id '+id);return elements[id];}};
const context=vm.createContext({document,Intl,console});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
let checks=0;function assert(x,msg){if(!x)throw Error(msg);checks++;}
const getPrice=()=>Number(elements.premium.textContent.replaceAll(',',''));
assert(Math.abs(getPrice()-10.450583572185565)<1e-4,'Initial benchmark');elements.kind.value='put';elements.kind.trigger('input');assert(Math.abs(getPrice()-5.573526022256971)<1e-4,'Put change');
elements.spot.value='';elements.spot.trigger('input');assert(!elements.error.hidden&&elements.premium.textContent==='Unavailable','Blank rejection');
elements.reset.trigger('click');assert(elements.error.hidden&&Math.abs(getPrice()-10.450583572185565)<1e-4,'Reset');
elements.days.value=0;elements.days.trigger('input');assert(getPrice()===0&&elements.delta.textContent==='Unavailable','Expiry boundary');elements.reset.trigger('click');
elements.step.value=256;elements.step.trigger('input');assert(elements.ledger.innerHTML.includes('0.0000'),'Final hedge position');
assert(elements.frontier.innerHTML.includes('<table>'),'Saved frontier');
assert((elements.holdout.innerHTML.match(/<tr>/g)||[]).length===9,'Eight paired evaluation comparisons');
assert(elements.holdout.innerHTML.includes('Conditional down-jump'),'Conditional jump labelling');
await fs.writeFile(path.join(root,'index.html'),html);
await fs.writeFile(path.join(root,'outputs/javascript_checks.json'),JSON.stringify({golden_price_comparisons:golden.length,absolute_price_tolerance:1e-4,maximum_difference:worst,application_checks:checks,method:'independent JS pricing and minimal-DOM application execution; browser visual layout not verified'},null,2)+'\n');
console.log({goldenPrices:golden.length,worstDifference:worst,applicationChecks:checks});

#!/usr/bin/env python3
"""Independent golden cases for Excel authoring; not workbook business logic."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from options_lab.pricing import bsm,greeks,crr
from options_lab.hedging import hedge_path

def main():
    h=json.loads((ROOT/'outputs/representative_hedge.json').read_text());path=[r['spot'] for r in h['ledger']]
    cases=[]
    for kind,s,k,t,r,vol,q,fee,borrow in [('call',100,100,1,.05,.2,0,5,0),('put',100,100,1,.05,.2,0,5,0),('call',110,105,.5,.03,.35,.02,20,.03)]:
        cases.append(dict(kind=kind,s=s,k=k,t=t,r=r,vol=vol,q=q,fee=fee,borrow=borrow,
                          price=bsm(s,k,t,r,vol,q,kind),greeks=greeks(s,k,t,r,vol,q,kind),tree=crr(s,k,t,r,vol,q,kind,steps=16),
                          hedge=hedge_path([x*s/100 for x in path],k,.25,.04,.25,kind=kind,rebalance_every=4,fee_bps=fee,borrow_spread=borrow)))
    (ROOT/'outputs/workbook_golden.json').write_text(json.dumps(dict(path=path,cases=cases),indent=2)+'\n')
    print('Prepared',len(cases),'pricing/tree/ledger golden cases')

if __name__=='__main__':main()

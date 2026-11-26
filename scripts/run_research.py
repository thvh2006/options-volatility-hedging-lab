#!/usr/bin/env python3
"""Seeded synthetic numerical and hedge-cost research. No observed market data."""
import sys,json,csv,hashlib,math
from pathlib import Path
from statistics import mean,stdev
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from options_lab.pricing import bsm,crr,monte_carlo,implied_vol,greeks
from options_lab.hedging import gbm_path,hedge_path

def quantile(values,p):
    s=sorted(values);index=(len(s)-1)*p;i=int(index);f=index-i
    return s[i]*(1-f)+s[min(i+1,len(s)-1)]*f

def main():
    cfg=json.loads((ROOT/'configs/research.json').read_text());e=cfg['hedge_experiment'];b=cfg['benchmark']
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    analytical=bsm(b['spot'],b['strike'],b['time'],b['rate'],b['vol'],b['dividend_yield'],b['kind'])
    convergence=[dict(steps=n,price=crr(b['spot'],b['strike'],b['time'],b['rate'],b['vol'],steps=n)) for n in [25,50,100,200,400,800]]
    for x in convergence:x['error']=x['price']-analytical
    mc=monte_carlo(b['spot'],b['strike'],b['time'],b['rate'],b['vol'],pairs=20000)
    coverage=[]
    for seed in range(40):
        r=monte_carlo(100,100,1,.05,.2,pairs=2000,seed=seed)
        coverage.append(r['ci95'][0]<=analytical<=r['ci95'][1])
    n=len(coverage);phat=sum(coverage)/n;z=1.96;den=1+z*z/n
    center=(phat+z*z/(2*n))/den;half=z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/den
    rows=[];representative=None;max_residual=0
    for realised in e['realised_vols']:
        # Each cost/frequency cell reuses these exact paths. Seeds are not re-drawn.
        paths=[gbm_path(e['spot'],e['time'],realised,e['physical_drift'],e['path_steps'],e['base_seed']+i) for i in range(e['paths'])]
        for every in e['rebalance_every']:
            for fee in e['fee_bps']:
                errors=[];costs=[];interests=[];turnovers=[];trades=[]
                for i,p in enumerate(paths):
                    h=hedge_path(p,e['strike'],e['time'],e['rate'],e['hedge_vol'],rebalance_every=every,fee_bps=fee)
                    errors.append(h['hedging_error']);costs.append(h['total_costs']);interests.append(h['total_interest']);turnovers.append(h['turnover_units']);trades.append(h['trade_count'])
                    max_residual=max(max_residual,abs(h['accounting_residual']))
                    if realised==.25 and every==4 and fee==5 and i==0:representative=h
                rows.append(dict(mode='SYNTHETIC',realised_vol=realised,hedge_vol=e['hedge_vol'],rebalance_every=every,fee_bps=fee,paths=len(paths),mean_error=mean(errors),standard_deviation=stdev(errors),standard_error_of_mean=stdev(errors)/math.sqrt(len(errors)),rmse=math.sqrt(mean(x*x for x in errors)),p05=quantile(errors,.05),p95=quantile(errors,.95),mean_cost=mean(costs),mean_interest=mean(interests),mean_turnover_units=mean(turnovers),mean_trade_count=mean(trades)))
    p=gbm_path(100,.25,.25,.04,256,1201);jump=[x*(.8 if i>=128 else 1) for i,x in enumerate(p)]
    jump_cases=[dict(case=name,hedge=hedge_path(path,100,.25,.04,.25,rebalance_every=4,fee_bps=5)) for name,path in [('continuous_path',p),('single_down_jump_20_percent',jump)]]
    payload=dict(status='SYNTHETIC_FOUNDATION',data_mode='SYNTHETIC',observed_market_data_admitted=False,
                 run_id=hashlib.sha256((ROOT/'configs/research.json').read_bytes()+b''.join(p.read_bytes() for p in sorted((ROOT/'src/options_lab').glob('*.py')))).hexdigest()[:16],
                 convention=cfg['contract'],benchmark=dict(analytical_call=analytical,greeks=greeks(100,100,1,.05,.2),iv_roundtrip=implied_vol(analytical,100,100,1,.05),tree=convergence,monte_carlo=mc),
                 monte_carlo_coverage=dict(replications=n,independent_pairs_per_replication=2000,coverage=phat,wilson95=[center-half,center+half],interpretation='Monte Carlo coverage diagnostic with binomial uncertainty, not a guarantee every interval contains the analytic price'),
                 hedge_experiment=e,hedge_cases=rows,max_cash_accounting_residual=max_residual,
                 jump_stress=[dict(case=x['case'],hedging_error=x['hedge']['hedging_error'],costs=x['hedge']['total_costs']) for x in jump_cases],
                 scope_limits=['No market calibration or observed strategy performance','Spot hedge assumes q=0 and unrestricted fractional trading with cash borrowing','No exchange margin, futures variation margin, funding or TWAP settlement hedge emulation','Fixed-vol paths and one illustrative jump are not an estimated return model','Costs are assumed bps on spot notional, not an actual exchange fee schedule'])
    (out/'research_results.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    for name,records in [('hedge_cost_frontier',rows),('representative_hedge_ledger',representative['ledger'])]:
        with (out/(name+'.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');writer.writeheader();writer.writerows(records)
    (out/'representative_hedge.json').write_text(json.dumps(representative,indent=2)+'\n')
    print(json.dumps(dict(run_id=payload['run_id'],hedge_experiments=len(rows),paths_per_cell=e['paths'],path_steps=e['path_steps'],max_cash_residual=max_residual,mc_coverage=phat,observed_data=False),indent=2))

if __name__=='__main__':main()

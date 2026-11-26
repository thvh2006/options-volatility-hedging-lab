#!/usr/bin/env python3
"""Locked synthetic extension with paired path-level uncertainty."""
import csv,hashlib,json,math,sys
from pathlib import Path
from random import Random
from statistics import mean,stdev
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from options_lab.hedging import hedge_path

def quantile(xs,p):
    v=sorted(xs);a=(len(v)-1)*p;i=int(a)
    return v[i]+(a-i)*(v[min(i+1,len(v)-1)]-v[i])

def path_for(cfg,scenario,seed):
    rng=Random(seed);dt=cfg['time']/cfg['steps'];p=[cfg['spot']]
    for i in range(1,cfg['steps']+1):
        vol=scenario['first_vol'] if i<=cfg['steps']//2 else scenario['second_vol']
        x=p[-1]*math.exp((cfg['drift']-vol*vol/2)*dt+vol*math.sqrt(dt)*rng.gauss(0,1))
        if i==cfg['steps']//2:x*=scenario['jump_multiplier']
        p.append(x)
    return p

def paired(a,b,seed,reps):
    # The same resampled path indices apply to both policies, preserving pairing.
    rng=Random(seed);n=len(a);squared_a=[x*x for x in a];squared_b=[x*x for x in b];samples=[]
    for _ in range(reps):
        ix=[rng.randrange(n) for _ in range(n)]
        samples.append(math.sqrt(sum(squared_a[i] for i in ix)/n)-math.sqrt(sum(squared_b[i] for i in ix)/n))
    diffs=[x-y for x,y in zip(a,b)];se=stdev(diffs)/math.sqrt(n)
    return dict(rmse_difference=math.sqrt(mean(squared_a))-math.sqrt(mean(squared_b)),rmse_difference_percentile95=[quantile(samples,.025),quantile(samples,.975)],mean_error_difference=mean(diffs),mean_difference_normal95=[mean(diffs)-1.96*se,mean(diffs)+1.96*se],bootstrap_replications=reps)

def main():
    cfg=json.loads((ROOT/'configs/holdout.json').read_text());start,stop=cfg['evaluation_seed_range'];bstart,bstop=cfg['baseline_seed_range']
    assert stop-start+1==cfg['paths'] and (stop<bstart or start>bstop)
    rows=[];comparisons=[];path_records=[];max_residual=0
    for scenario in cfg['scenarios']:
        errors={};costs={};hashes=[]
        for seed in range(start,stop+1):
            path=path_for(cfg,scenario,seed)
            digest=hashlib.sha256(json.dumps(path,separators=(',',':')).encode()).hexdigest();hashes.append(digest)
            for fee in cfg['fee_bps']:
                for every in cfg['rebalance_every']:
                    h=hedge_path(path,cfg['strike'],cfg['time'],cfg['rate'],cfg['hedge_vol'],rebalance_every=every,fee_bps=fee)
                    key=(fee,every);errors.setdefault(key,[]).append(h['hedging_error']);costs.setdefault(key,[]).append(h['total_costs'])
                    max_residual=max(max_residual,abs(h['accounting_residual']))
                    assert h['terminal_holdings']==0
                    path_records.append(dict(scenario=scenario['id'],seed=seed,fee_bps=fee,rebalance_every=every,path_sha256=digest,error=h['hedging_error'],cost=h['total_costs']))
        for (fee,every),xs in errors.items():
            p05=quantile(xs,.05)
            rows.append(dict(scenario=scenario['id'],fee_bps=fee,rebalance_every=every,paths=len(xs),mean_error=mean(xs),standard_deviation=stdev(xs),rmse=math.sqrt(mean(x*x for x in xs)),p05=p05,lower_tail_mean=mean(x for x in xs if x<=p05),mean_cost=mean(costs[fee,every])))
        comp=cfg['comparison']
        for fee in cfg['fee_bps']:
            comparisons.append(dict(scenario=scenario['id'],fee_bps=fee,policy_every=comp['policy_every'],reference_every=comp['reference_every'],**paired(errors[fee,comp['policy_every']],errors[fee,comp['reference_every']],comp['bootstrap_seed'],comp['bootstrap_replications'])))
    payload=dict(data_mode='SYNTHETIC',protocol=cfg,configuration_sha256=hashlib.sha256((ROOT/'configs/holdout.json').read_bytes()).hexdigest(),summary=rows,paired_comparisons=comparisons,max_accounting_residual=max_residual,paths_disjoint_from_baseline=True,market_out_of_sample=False,policy_selected=False)
    (ROOT/'outputs/holdout_results.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    for name,rs in [('holdout_summary',rows),('holdout_path_errors',path_records)]:
        with (ROOT/'outputs'/f'{name}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
    print(json.dumps(dict(cells=len(rows),paired_comparisons=len(comparisons),path_policy_rows=len(path_records),max_accounting_residual=max_residual)))
if __name__=='__main__':main()

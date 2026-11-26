#!/usr/bin/env python3
"""Prepare independent JS golden inputs and execute the foundation notebook."""
import io,json,sys
from pathlib import Path
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from options_lab.pricing import bsm

def main():
    golden=[]
    for s in [60,100,150]:
        for t in [.01,.25,1]:
            for vol in [.1,.3,.8]:
                for r in [-.01,.05]:
                    for kind in ['call','put']:
                        inputs=[s,100,t,r,vol,.02,kind];golden.append(dict(inputs=inputs,price=bsm(*inputs)))
    (ROOT/'outputs/pricing_golden.json').write_text(json.dumps(golden,indent=2)+'\n')
    sections=[('''# P5 numerical pricing and hedge-cost foundation

All saved experiments are synthetic. There is no observed quote chain or trading track record.
This notebook executes ordinary Python sequentially. A Jupyter-kernel run is not claimed.
''','''from pathlib import Path
import json,sys
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'src/options_lab').is_dir())
sys.path.insert(0,str(ROOT/'src'))
from options_lab.pricing import bsm,crr,implied_vol,greeks,monte_carlo
from options_lab.hedging import gbm_path,hedge_path
print('Benchmark call:',bsm(100,100,1,.05,.2))
'''),('## 1 Price to IV to price\nSolver status and price residual must accompany the implied volatility.','''p=bsm(100,100,1,.05,.2)
r=implied_vol(p,100,100,1,.05)
assert r['status']=='CONVERGED' and abs(r['residual'])<1e-9
print(r)
print(greeks(100,100,1,.05,.2))
'''),('## 2 Numerical approximation and uncertainty\nAn individual Monte Carlo interval can miss the correct price. Standard errors belong to independent antithetic pairs.','''results=json.loads((ROOT/'outputs/research_results.json').read_text())
for r in results['benchmark']['tree']:print('CRR',r)
print('Monte Carlo:',results['benchmark']['monte_carlo'])
print('Coverage diagnostic:',results['monte_carlo_coverage'])
'''),('## 3 Self-financing cash ledger\nPremium finances the hedge and a cash account that may borrow. Final stock liquidation and option settlement both enter cash.','''p=gbm_path(100,.25,.25,.04,256,94000)
h=hedge_path(p,100,.25,.04,.25,rebalance_every=4,fee_bps=5)
assert abs(h['accounting_residual'])<1e-10 and h['terminal_holdings']==0
print({k:h[k] for k in ['premium','terminal_payoff','total_costs','total_interest','hedging_error','accounting_residual']})
'''),('## 4 Cost and frequency use identical paths\nA lower discretisation error does not imply a better result after costs. These exploratory results do not select a universal optimum.','''matched=[r for r in results['hedge_cases'] if r['realised_vol']==.25]
for r in matched:print('Every',r['rebalance_every'],'steps; fees',r['fee_bps'],'bps; RMSE',round(r['rmse'],4),'mean error',round(r['mean_error'],4))
print('Largest accounting residual:',results['max_cash_accounting_residual'])
'''),('## 6 Claims and next research stage\nMarket snapshots require contract, timestamp and publication-rights review. Calibration accuracy alone cannot establish hedge performance.','''validation=json.loads((ROOT/'outputs/validation.json').read_text())
assert validation['status']=='PASS'
print('Mathematical and accounting tests:',validation)
print('Observed market data admitted:',results['observed_market_data_admitted'])
print('Excel model: outputs/P5_Options_Research_Model.xlsx; independent formula and cross-engine checks saved.')
print('Next: allowed observed market evidence, venue-specific hedge accounting and locked challenger evaluation.')
''')]
    sections.insert(5,('## 5 Separate seeds and paired uncertainty\nThese are conditional synthetic comparisons, not market OOS. A jump is imposed on every jump-stress path. Intervals are pointwise and select no policy.','''extension=json.loads((ROOT/'outputs/holdout_results.json').read_text())
assert extension['paths_disjoint_from_baseline'] and not extension['market_out_of_sample']
for row in extension['paired_comparisons']:
    print(row['scenario'],row['fee_bps'],'bps; RMSE difference',round(row['rmse_difference'],4),'95% interval',[round(v,4) for v in row['rmse_difference_percentile95']])
print('Policy selected:',extension['policy_selected'])
'''))
    cells=[];env={'__name__':'__main__'}
    for i,(md,code) in enumerate(sections,1):
        cells.append(dict(id=f'md-{i}',cell_type='markdown',metadata={},source=md.splitlines(True)))
        buf=io.StringIO()
        with redirect_stdout(buf):exec(compile(code,'<notebook-cell>','exec'),env)
        cells.append(dict(id=f'code-{i}',cell_type='code',metadata={},source=code.splitlines(True),execution_count=i,outputs=[dict(output_type='stream',name='stdout',text=buf.getvalue().splitlines(True))]))
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.12'),execution_method='ordinary Python sequential harness; Jupyter not verified'),cells=cells)
    (ROOT/'notebooks/01_foundation_walkthrough.ipynb').write_text(json.dumps(nb,indent=2)+'\n')
    print(json.dumps(dict(golden_prices=len(golden),executed_notebook_cells=len(sections))))

if __name__=='__main__':main()

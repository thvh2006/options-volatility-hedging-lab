"""Synthetic spot delta hedge. No exchange margin/futures/funding emulation.

Short one or more options, finance spot delta hedge with premium plus cash
borrowing. Initial and terminal trading costs both count. q must be zero.
"""
from math import exp,expm1,isfinite,sqrt
from random import Random
from .pricing import bsm,greeks,payoff,validate

def gbm_path(s,t,vol,mu,steps,seed):
    validate(s,s,t,mu,vol)
    if t<=0 or not isinstance(steps,int) or isinstance(steps,bool) or steps<1:raise ValueError('Positive horizon and integer path steps required')
    rng=Random(seed);dt=t/steps;path=[s]
    for _ in range(steps):path.append(path[-1]*exp((mu-vol*vol/2)*dt+vol*sqrt(dt)*rng.gauss(0,1)))
    return path

def hedge_path(path,k,t,r,hedge_vol,*,kind='call',contracts=1,multiplier=1,rebalance_every=1,fee_bps=0,half_spread_bps=0,borrow_spread=0,q=0):
    if not isinstance(path,(list,tuple)) or len(path)<2 or any(not isfinite(s) or s<=0 for s in path):raise ValueError('Positive finite prices required')
    validate(path[0],k,t,r,hedge_vol,q,kind)
    if t<=0 or hedge_vol<=0 or q!=0:raise ValueError('Spot hedge currently requires positive time/hedge volatility and q=0')
    if not isinstance(rebalance_every,int) or isinstance(rebalance_every,bool) or rebalance_every<1:raise ValueError('Positive integer rebalance interval required')
    if any(not isfinite(v) or v<0 for v in [fee_bps,half_spread_bps,borrow_spread]) or any(not isfinite(v) or v<=0 for v in [contracts,multiplier]):raise ValueError('Invalid trade/cost convention')
    quantity=contracts*multiplier;n=len(path)-1;dt=t/n
    premium=bsm(path[0],k,t,r,hedge_vol,kind=kind)*quantity
    cash=0.;holding=0.;ledger=[]
    for i,s in enumerate(path):
        opening_cash=cash;interest=cash*expm1((r+(borrow_spread if cash<0 else 0))*dt) if i else 0
        cash+=interest;option_cash=premium if i==0 else (-payoff(s,k,kind)*quantity if i==n else 0)
        cash+=option_cash
        if i==n:target=0.
        elif i%rebalance_every==0:target=greeks(s,k,t-i*dt,r,hedge_vol,kind=kind)['delta']*quantity
        else:target=holding
        trade=target-holding;trade_cash=-trade*s
        costs=abs(trade)*s*(fee_bps+half_spread_bps)/10000
        cash+=trade_cash-costs;holding=target
        residual=cash-(opening_cash+interest+option_cash+trade_cash-costs)
        model_liability=0 if i==n else bsm(s,k,t-i*dt,r,hedge_vol,kind=kind)*quantity
        ledger.append(dict(step=i,time=i*dt,spot=s,opening_cash=opening_cash,interest=interest,option_cash=option_cash,
                           trade_units=trade,trade_cash=trade_cash,costs=costs,closing_cash=cash,holding=holding,
                           option_liability=model_liability,net_wealth=cash+holding*s-model_liability,cash_roll_residual=residual))
    accounting=cash-sum(row['interest']+row['option_cash']+row['trade_cash']-row['costs'] for row in ledger)
    return dict(mode='SYNTHETIC_SPOT_HEDGE',measure='path scenario; not a trading performance record',premium=premium,
                terminal_payoff=payoff(path[-1],k,kind)*quantity,hedging_error=cash,
                total_costs=sum(x['costs'] for x in ledger),total_interest=sum(x['interest'] for x in ledger),
                turnover_units=sum(abs(x['trade_units']) for x in ledger),trade_count=sum(abs(x['trade_units'])>1e-14 for x in ledger),
                terminal_holdings=holding,accounting_residual=accounting,ledger=ledger)

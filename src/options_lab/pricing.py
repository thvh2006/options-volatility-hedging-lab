"""Prices per underlying unit; rates/volatility decimal; time in years.

BSM uses a cash-funded spot and continuous dividend yield. Black76 uses a
fixed-maturity forward and an explicit discount factor. They are different
contracts. Greeks below are BSM spot Greeks, not exchange collateral Greeks.
"""
from math import erf, erfc, exp, isfinite, log, pi, sqrt
from random import Random
from statistics import mean, stdev

def validate(s,k,t,r,vol,q=0,kind='call'):
    if kind not in ('call','put') or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not isfinite(x) for x in [s,k,t,r,vol,q]):
        raise ValueError('Finite numeric inputs and call/put required')
    if s<=0 or k<=0 or t<0 or vol<0:raise ValueError('Positive spot/strike; nonnegative time/volatility required')

def cdf(x):return .5*erfc(-x/sqrt(2))
def pdf(x):return exp(-x*x/2)/sqrt(2*pi)
def payoff(s,k,kind='call'):
    validate(s,k,0,0,0,kind=kind)
    return max((s-k) if kind=='call' else (k-s),0)

def bounds(s,k,t,r,q=0,kind='call'):
    validate(s,k,t,r,0,q,kind)
    a,b=s*exp(-q*t),k*exp(-r*t)
    return (max(a-b,0),a) if kind=='call' else (max(b-a,0),b)

def bsm(s,k,t,r,vol,q=0,kind='call'):
    validate(s,k,t,r,vol,q,kind)
    if t==0:return payoff(s,k,kind)
    if vol==0:return exp(-r*t)*payoff(s*exp((r-q)*t),k,kind)
    d1=(log(s/k)+(r-q+vol*vol/2)*t)/(vol*sqrt(t));d2=d1-vol*sqrt(t)
    if kind=='call':return s*exp(-q*t)*cdf(d1)-k*exp(-r*t)*cdf(d2)
    return k*exp(-r*t)*cdf(-d2)-s*exp(-q*t)*cdf(-d1)

def black76(forward,k,t,discount,vol,kind='call'):
    validate(forward,k,t,0,vol,kind=kind)
    if not isfinite(discount) or discount<=0:raise ValueError('Positive discount factor required')
    return discount*bsm(forward,k,t,0,vol,kind=kind)

def greeks(s,k,t,r,vol,q=0,kind='call'):
    validate(s,k,t,r,vol,q,kind)
    if t==0 or vol==0:
        return dict(status='BOUNDARY_GREEKS_UNAVAILABLE',delta=None,gamma=None,vega_per_vol_point=None,theta_per_calendar_day=None,rho_per_rate_point=None)
    d1=(log(s/k)+(r-q+vol*vol/2)*t)/(vol*sqrt(t));d2=d1-vol*sqrt(t)
    a,b=exp(-q*t),exp(-r*t)
    delta=a*cdf(d1) if kind=='call' else a*(cdf(d1)-1)
    common=-s*a*pdf(d1)*vol/(2*sqrt(t))
    if kind=='call':theta=common-r*k*b*cdf(d2)+q*s*a*cdf(d1);rho=k*t*b*cdf(d2)
    else:theta=common+r*k*b*cdf(-d2)-q*s*a*cdf(-d1);rho=-k*t*b*cdf(-d2)
    return dict(status='SMOOTH',delta=delta,gamma=a*pdf(d1)/(s*vol*sqrt(t)),
                vega_per_vol_point=s*a*pdf(d1)*sqrt(t)*.01,
                theta_per_calendar_day=theta/365,rho_per_rate_point=rho*.01)

def implied_vol(price,s,k,t,r,q=0,kind='call',*,tolerance=1e-9,max_vol=8.0,max_iterations=160):
    validate(s,k,t,r,0,q,kind)
    if not isfinite(price) or price<0 or tolerance<=0 or max_vol<=0 or max_iterations<1:raise ValueError('Invalid price/solver configuration')
    lo_price,hi_price=bounds(s,k,t,r,q,kind)
    if t==0:return dict(status='EXPIRED_NO_IV',iv=None,residual=None,iterations=0)
    if price<lo_price-tolerance or price>hi_price+tolerance:return dict(status='PRICE_OUTSIDE_BOUNDS',iv=None,residual=None,iterations=0)
    if abs(price-lo_price)<=tolerance:return dict(status='ZERO_VOL_BOUNDARY',iv=0.0,residual=lo_price-price,iterations=0)
    if price>=hi_price-tolerance:return dict(status='NO_FINITE_IV_AT_UPPER_BOUND',iv=None,residual=None,iterations=0)
    low,high=0.,min(.5,max_vol)
    while bsm(s,k,t,r,high,q,kind)<price and high<max_vol:high=min(2*high,max_vol)
    if bsm(s,k,t,r,high,q,kind)<price:return dict(status='BRACKET_LIMIT',iv=None,residual=bsm(s,k,t,r,high,q,kind)-price,iterations=0)
    for i in range(1,max_iterations+1):
        mid=(low+high)/2;residual=bsm(s,k,t,r,mid,q,kind)-price
        if abs(residual)<=tolerance:return dict(status='CONVERGED',iv=mid,residual=residual,iterations=i)
        if residual<0:low=mid
        else:high=mid
    return dict(status='ITERATION_LIMIT',iv=None,residual=residual,iterations=max_iterations)

def crr(s,k,t,r,vol,q=0,kind='call',steps=200):
    validate(s,k,t,r,vol,q,kind)
    if not isinstance(steps,int) or isinstance(steps,bool) or steps<1:raise ValueError('Positive integer steps required')
    if t==0 or vol==0:return bsm(s,k,t,r,vol,q,kind)
    dt=t/steps;u=exp(vol*sqrt(dt));d=1/u;p=(exp((r-q)*dt)-d)/(u-d)
    if not 0<=p<=1:raise ValueError('Tree probability outside [0,1]; increase steps')
    values=[payoff(s*u**j*d**(steps-j),k,kind) for j in range(steps+1)]
    discount=exp(-r*dt)
    for level in range(steps-1,-1,-1):values=[discount*((1-p)*values[j]+p*values[j+1]) for j in range(level+1)]
    return values[0]

def monte_carlo(s,k,t,r,vol,q=0,kind='call',pairs=10000,seed=1701):
    """Independent antithetic pair averages own the standard-error denominator."""
    validate(s,k,t,r,vol,q,kind)
    if not isinstance(pairs,int) or isinstance(pairs,bool) or pairs<2:raise ValueError('At least two independent pairs required')
    rng=Random(seed);drift=(r-q-vol*vol/2)*t;scale=vol*sqrt(t);disc=exp(-r*t)
    observations=[]
    for _ in range(pairs):
        z=rng.gauss(0,1)
        observations.append(disc*(payoff(s*exp(drift+scale*z),k,kind)+payoff(s*exp(drift-scale*z),k,kind))/2)
    estimate=mean(observations);se=stdev(observations)/sqrt(pairs)
    return dict(price=estimate,standard_error=se,ci95=[estimate-1.96*se,estimate+1.96*se],
                independent_pairs=pairs,terminal_draws=2*pairs,seed=seed,measure='risk_neutral',interval_method='normal approximation on antithetic pair averages')

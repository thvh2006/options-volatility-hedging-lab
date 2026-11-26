import unittest
from math import exp,sqrt
from copy import deepcopy
from options_lab.pricing import bsm,black76,crr,greeks,implied_vol,monte_carlo,payoff,bounds
from options_lab.hedging import gbm_path,hedge_path
from options_lab.quotes import quote_reasons

class PricingTests(unittest.TestCase):
    def test_textbook_value(self):
        self.assertAlmostEqual(bsm(100,100,1,.05,.2),10.450583572185565,places=10)
        self.assertAlmostEqual(bsm(100,100,1,.05,.2,kind='put'),5.573526022256971,places=10)
    def test_parity_with_yield_and_negative_rates(self):
        for r in [-.03,0,.1]:
            for q in [0,.04]:
                for s in [30,100,250]:
                    self.assertAlmostEqual(bsm(s,100,.6,r,.4,q)-bsm(s,100,.6,r,.4,q,'put'),s*exp(-q*.6)-100*exp(-r*.6),places=10)
    def test_forward_spot_conversion(self):
        s,k,t,r,q,vol=100,105,.7,.04,.02,.35
        for kind in ['call','put']:self.assertAlmostEqual(black76(s*exp((r-q)*t),k,t,exp(-r*t),vol,kind),bsm(s,k,t,r,vol,q,kind),places=11)
    def test_expiry_and_zero_vol(self):
        self.assertEqual(bsm(120,100,0,.1,.2),20)
        self.assertAlmostEqual(bsm(100,105,1,.1,0),exp(-.1)*max(100*exp(.1)-105,0),places=11)
        self.assertIsNone(greeks(100,100,0,0,.2)['delta'])
    def test_bounds_and_monotonicity(self):
        for kind in ['call','put']:
            values=[bsm(100,120,.4,-.02,sigma,.01,kind) for sigma in [.01,.1,.4,1,3]]
            lo,hi=bounds(100,120,.4,-.02,.01,kind)
            self.assertTrue(all(lo-1e-10<=x<=hi for x in values))
            self.assertEqual(values,sorted(values))
    def test_invalid_inputs(self):
        for s in [-1,0,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError):bsm(s,100,1,.05,.2)
    def test_tree_converges(self):
        target=bsm(100,100,1,.05,.2)
        errors=[abs(crr(100,100,1,.05,.2,steps=n)-target) for n in [50,200,800]]
        self.assertLess(errors[-1],.003);self.assertLess(errors[-1],errors[0])
    def test_invalid_tree_probability_is_not_clamped(self):
        with self.assertRaises(ValueError):crr(100,100,1,2,.01,steps=1)
    def test_iv_roundtrip_grid(self):
        for kind in ['call','put']:
            for k in [80,100,120]:
                for sigma in [.1,.25,.8]:
                    p=bsm(100,k,.5,.03,sigma,kind=kind)
                    result=implied_vol(p,100,k,.5,.03,kind=kind)
                    self.assertEqual(result['status'],'CONVERGED')
                    self.assertLess(abs(result['residual']),1e-9)
                    self.assertAlmostEqual(result['iv'],sigma,places=6)
    def test_iv_failure_modes(self):
        self.assertEqual(implied_vol(110,100,100,1,0)['status'],'PRICE_OUTSIDE_BOUNDS')
        self.assertEqual(implied_vol(100,100,100,1,0)['status'],'NO_FINITE_IV_AT_UPPER_BOUND')
        self.assertEqual(implied_vol(0,100,100,1,0)['status'],'ZERO_VOL_BOUNDARY')
        self.assertEqual(implied_vol(1,100,100,0,0)['status'],'EXPIRED_NO_IV')
        self.assertEqual(implied_vol(50,100,100,1,0,max_vol=.1)['status'],'BRACKET_LIMIT')
    def test_analytic_greeks_against_finite_differences(self):
        s,k,t,r,v,q=100,107,.8,.03,.32,.02;h=.01;eps=1e-5
        for kind in ['call','put']:
            g=greeks(s,k,t,r,v,q,kind);p=bsm(s,k,t,r,v,q,kind)
            self.assertAlmostEqual(g['delta'],(bsm(s+h,k,t,r,v,q,kind)-bsm(s-h,k,t,r,v,q,kind))/(2*h),places=7)
            self.assertAlmostEqual(g['gamma'],(bsm(s+h,k,t,r,v,q,kind)-2*p+bsm(s-h,k,t,r,v,q,kind))/h**2,places=7)
            self.assertAlmostEqual(g['vega_per_vol_point'],(bsm(s,k,t,r,v+eps,q,kind)-bsm(s,k,t,r,v-eps,q,kind))/(2*eps)*.01,places=7)
            self.assertAlmostEqual(g['rho_per_rate_point'],(bsm(s,k,t,r+eps,v,q,kind)-bsm(s,k,t,r-eps,v,q,kind))/(2*eps)*.01,places=7)
            self.assertAlmostEqual(g['theta_per_calendar_day'],(bsm(s,k,t-eps,r,v,q,kind)-bsm(s,k,t+eps,r,v,q,kind))/(2*eps)/365,places=7)
    def test_mc_pair_standard_error_and_seed(self):
        a=monte_carlo(100,100,1,.05,.2,pairs=5000,seed=71)
        self.assertEqual(a,monte_carlo(100,100,1,.05,.2,pairs=5000,seed=71))
        self.assertEqual(a['terminal_draws'],2*a['independent_pairs'])
        self.assertLess(abs(a['price']-bsm(100,100,1,.05,.2)),5*a['standard_error'])

class HedgeTests(unittest.TestCase):
    def test_cash_ledger_and_final_close(self):
        p=gbm_path(100,.25,.25,.04,256,41);v=hedge_path(p,100,.25,.04,.25,fee_bps=5)
        self.assertLess(abs(v['accounting_residual']),1e-10)
        self.assertEqual(v['terminal_holdings'],0)
        self.assertLess(max(abs(r['cash_roll_residual']) for r in v['ledger']),1e-12)
        self.assertAlmostEqual(v['ledger'][0]['net_wealth'],-v['ledger'][0]['costs'],places=10)
        self.assertEqual(v['ledger'][-1]['option_liability'],0)
    def test_more_cost_never_improves_fixed_path_hedge(self):
        p=gbm_path(100,.25,.4,.04,64,8)
        a=hedge_path(p,100,.25,.04,.25,fee_bps=0)
        b=hedge_path(p,100,.25,.04,.25,fee_bps=20)
        self.assertLess(b['hedging_error'],a['hedging_error'])
        self.assertEqual([r['trade_units'] for r in a['ledger']],[r['trade_units'] for r in b['ledger']])
    def test_multiplier_scales_all_cash_flows(self):
        p=[100,101,98,105]
        a=hedge_path(p,100,.25,.04,.25);b=hedge_path(p,100,.25,.04,.25,contracts=3,multiplier=10)
        self.assertAlmostEqual(b['hedging_error'],a['hedging_error']*30,places=10)
    def test_higher_borrow_cost_reduces_terminal_cash(self):
        p=[100,101,102,104]
        a=hedge_path(p,100,.25,.04,.25);b=hedge_path(p,100,.25,.04,.25,borrow_spread=.05)
        self.assertLess(b['hedging_error'],a['hedging_error'])
    def test_final_close_cost_is_included(self):
        p=[100,101,99,103];a=hedge_path(p,100,.25,.04,.25,fee_bps=10)
        self.assertGreater(a['ledger'][-1]['costs'],0)
        self.assertEqual(a['ledger'][-1]['option_cash'],-3)
    def test_unsupported_dividends_and_bad_paths_rejected(self):
        with self.assertRaises(ValueError):hedge_path([100,101],100,1,.05,.2,q=.02)
        with self.assertRaises(ValueError):hedge_path([100,float('nan')],100,1,.05,.2)

class QuoteTests(unittest.TestCase):
    def fixture(self):return dict(mode='SYNTHETIC',style='european',kind='call',instrument_type='linear',quote_currency='USD',settlement_currency='USD',bid=3,ask=3.1,bid_size=1,ask_size=1,quote_timestamp_ms=10000,underlying_timestamp_ms=10000,expiry_ms=100000,forward=100,discount=.99,contract_size=1,strike=100)
    def test_clean_fixture_is_not_relabelled_market_data(self):
        q=self.fixture();self.assertEqual(quote_reasons(q,11000),[]);self.assertEqual(q['mode'],'SYNTHETIC')
    def test_quote_failures_are_specific(self):
        cases=[('ask',2,'CROSSED_BOOK'),('bid_size',0,'MISSING_EXECUTABLE_SIZE'),('quote_timestamp_ms',0,'STALE_QUOTE'),('underlying_timestamp_ms',7000,'UNALIGNED_UNDERLYING'),('settlement_currency','BTC','CURRENCY_MISMATCH'),('instrument_type','reversed','UNSUPPORTED_CONTRACT'),('expiry_ms',0,'EXPIRED'),('bid',300,'MID_OUTSIDE_MODEL_BOUNDS')]
        for key,value,reason in cases:
            row=self.fixture();row[key]=value;self.assertIn(reason,quote_reasons(row,11000))
    def test_missing_is_not_zero(self):
        row=self.fixture();row['bid']=None;self.assertEqual(quote_reasons(row,11000),['MISSING_FIELD'])
    def test_future_timestamps_rejected(self):
        row=self.fixture();row['underlying_timestamp_ms']=20000
        self.assertIn('FUTURE_UNDERLYING_TIMESTAMP',quote_reasons(row,11000))

if __name__=='__main__':unittest.main()

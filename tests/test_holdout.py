import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_holdout import path_for,paired
from options_lab.hedging import gbm_path

class HoldoutTests(unittest.TestCase):
    def config(self):return dict(time=.25,steps=256,spot=100,drift=.04)
    def scenario(self,jump=1):return dict(first_vol=.25,second_vol=.25,jump_multiplier=jump)
    def test_constant_regime_matches_existing_gbm(self):
        self.assertEqual(path_for(self.config(),self.scenario(),304000),gbm_path(100,.25,.25,.04,256,304000))
    def test_jump_is_one_permanent_midpoint_multiplier(self):
        base=path_for(self.config(),self.scenario(),304000);jump=path_for(self.config(),self.scenario(.8),304000)
        for i,(a,b) in enumerate(zip(base,jump)):self.assertAlmostEqual(b/a,1 if i<128 else .8,places=12)
    def test_paired_bootstrap_preserves_identical_policies(self):
        r=paired([1,-2,3],[1,-2,3],17,100)
        self.assertEqual(r['rmse_difference_percentile95'],[0,0]);self.assertEqual(r['mean_error_difference'],0)
    def test_paired_direction_reverses_with_policy(self):
        a=paired([1,2,3],[2,4,6],17,100);b=paired([2,4,6],[1,2,3],17,100)
        self.assertAlmostEqual(a['rmse_difference'],-b['rmse_difference'])
        for x,y in zip(a['rmse_difference_percentile95'],reversed(b['rmse_difference_percentile95'])):self.assertAlmostEqual(x,-y)

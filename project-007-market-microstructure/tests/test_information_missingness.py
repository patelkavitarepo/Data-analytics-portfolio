"""Synthetic-only regression coverage for undefined directional AP."""
import unittest
from microstructure.information_bootstrap import missingness_aware_ap_lift

def metric(ap,base):
    return {"directions":{k:{"average_precision":ap,"base_rate":base} for k in ("1","3")}}

class MissingnessTests(unittest.TestCase):
    def test_undefined_ap_reports_stock_and_day_without_zero_imputation(self):
        x={"m":{"s1":{"d1":metric(.3,.1),"d2":metric(None,0),"d3":metric(.2,.1)},
                "s2":{"d1":metric(.2,.1),"d2":metric(.3,.1),"d3":metric(.4,.1)}}}
        r=missingness_aware_ap_lift(x,replicates=20)["m"]["1"]
        self.assertEqual(r["total_days"],3)
        self.assertEqual(r["complete_days"],2)
        self.assertEqual(r["unavailable_stock_day_slots"],1)
        self.assertEqual(r["incomplete_day_details"][0]["unavailable"][0]["stock"],"s1")
        self.assertAlmostEqual(r["mean_complete_day_ap_lift"],.175)
        self.assertEqual(r["interval_status"],"descriptive_complete_day_only")
    def test_no_positives_or_no_matches_has_no_interval(self):
        x={"m":{"s":{"d1":metric(None,0),"d2":metric(None,None)}}}
        r=missingness_aware_ap_lift(x,replicates=20)["m"]["3"]
        self.assertIsNone(r["day_cluster_percentile_95_interval"])
        self.assertIsNone(r["mean_complete_day_ap_lift"])
        self.assertEqual(r["incomplete_days"],2)
    def test_nonfinite_is_reported_not_averaged(self):
        x={"m":{"s":{"d1":metric(float("nan"),.1),"d2":metric(.3,.1)}}}
        r=missingness_aware_ap_lift(x,replicates=20)["m"]["1"]
        self.assertEqual(r["incomplete_day_details"][0]["unavailable"][0]["reason"],"nonfinite_ap_or_base")
    def test_unpaired_calendar_fails(self):
        x={"m":{"s1":{"d1":metric(.2,.1)},"s2":{"d2":metric(.2,.1)}}}
        with self.assertRaises(ValueError):missingness_aware_ap_lift(x)
if __name__=="__main__":unittest.main()

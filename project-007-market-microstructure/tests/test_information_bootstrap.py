"""Deterministic paired-day cluster bootstrap synthetic tests."""
import unittest
from microstructure.information_bootstrap import day_cluster_ap_lift, paired_model_ap_lift_difference, paired_model_ap_lift_difference

def leaf(ap,base):
    return {"directions":{k:{"average_precision":ap,"base_rate":base} for k in ("1","3")}}

class InformationBootstrapTests(unittest.TestCase):
    def test_identical_days_produce_exact_lift_and_deterministic_intervals(self):
        data={model:{stock:{day:leaf(.25,.1) for day in ("a","b","c")}
                     for stock in ("s1","s2")}
              for model in ("balanced","unweighted")}
        a=day_cluster_ap_lift(data,replicates=20)
        b=day_cluster_ap_lift(data,replicates=20)
        self.assertEqual(a,b)
        self.assertAlmostEqual(a["balanced"]["1"]["mean_stock_day_ap_minus_base"],.15)
        self.assertAlmostEqual(a["balanced"]["1"]["day_cluster_percentile_95_interval"][0],.15)
        self.assertTrue(a["balanced"]["1"]["not_pooled_ap"])
    def test_unpaired_calendar_fails_closed(self):
        data={"a":{"s":{"day1":leaf(.2,.1)}},
              "b":{"s":{"day2":leaf(.2,.1)}}}
        with self.assertRaises(ValueError):day_cluster_ap_lift(data)
    def test_missing_day_ap_fails_closed(self):
        data={"a":{"s":{"day1":leaf(None,.1)}}}
        with self.assertRaises(ValueError):day_cluster_ap_lift(data)
    def test_paired_model_difference_preserves_shared_days(self):
        data={"balanced":{"s":{d:leaf(.3,.1) for d in ("a","b","c")}},
              "unweighted":{"s":{d:leaf(.2,.1) for d in ("a","b","c")}}}
        result=paired_model_ap_lift_difference(data,"balanced","unweighted",replicates=30)
        self.assertAlmostEqual(result["1"]["mean_paired_stock_day_ap_lift_difference"],.1)
        self.assertAlmostEqual(result["3"]["day_cluster_percentile_95_interval"][1],.1)
    def test_paired_model_rejects_unaligned_dates(self):
        data={"balanced":{"s":{"a":leaf(.3,.1)}},
              "unweighted":{"s":{"b":leaf(.2,.1)}}}
        with self.assertRaises(ValueError):
            paired_model_ap_lift_difference(data,"balanced","unweighted")
    def test_paired_model_difference_preserves_shared_days(self):
        data={"balanced":{"s":{d:leaf(.3,.1) for d in ("a","b","c")}},
              "unweighted":{"s":{d:leaf(.2,.1) for d in ("a","b","c")}}}
        result=paired_model_ap_lift_difference(data,"balanced","unweighted",replicates=30)
        self.assertAlmostEqual(result["1"]["mean_paired_stock_day_ap_lift_difference"],.1)
        self.assertAlmostEqual(result["3"]["day_cluster_percentile_95_interval"][1],.1)
    def test_paired_model_rejects_unaligned_dates(self):
        data={"balanced":{"s":{"a":leaf(.3,.1)}},
              "unweighted":{"s":{"b":leaf(.2,.1)}}}
        with self.assertRaises(ValueError):
            paired_model_ap_lift_difference(data,"balanced","unweighted")
if __name__=="__main__":unittest.main()

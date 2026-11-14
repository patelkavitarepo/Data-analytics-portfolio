"""Synthetic tests for D018 joint-day paired reporting."""
import unittest
from microstructure.information_bootstrap import missingness_aware_paired_difference

def leaf(ap,base):
    return {"directions":{str(k):{"average_precision":ap,"base_rate":base} for k in (1,3)}}

class PairedMissingnessTests(unittest.TestCase):
    def test_joint_complete_day_only_and_missing_details(self):
        a={"s":{d:leaf(.3,.1) for d in ("a","b","c")}}
        b={"s":{"a":leaf(.2,.1),"b":leaf(None,0),"c":leaf(.2,.1)}}
        r=missingness_aware_paired_difference({"a":a,"b":b},"a","b",replicates=20)["1"]
        self.assertEqual(r["joint_complete_days"],2)
        self.assertEqual(len(r["excluded_days"]),1)
        self.assertEqual(r["excluded_days"][0]["missing"][0]["model"],"b")
        self.assertAlmostEqual(r["mean_joint_complete_day_difference"],.1)
    def test_no_joint_complete_days_withholds_interval(self):
        r=missingness_aware_paired_difference(
            {"a":{"s":{"d":leaf(None,0)}},"b":{"s":{"d":leaf(.2,.1)}}},
            "a","b",replicates=20)["3"]
        self.assertIsNone(r["day_cluster_percentile_95_interval"])
        self.assertEqual(r["interval_status"],"insufficient_joint_complete_days")
    def test_mismatched_dates_rejected(self):
        with self.assertRaises(ValueError):
            missingness_aware_paired_difference(
                {"a":{"s":{"d1":leaf(.2,.1)}},"b":{"s":{"d2":leaf(.3,.1)}}},"a","b")
if __name__=="__main__":unittest.main()

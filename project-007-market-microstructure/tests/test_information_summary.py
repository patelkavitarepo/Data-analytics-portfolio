"""No averaging stock-day AP into fictitious pooled ranking."""
import unittest
from microstructure.information_population import audit_stock_day
from microstructure.information_summary import summarize_information_days

class InformationSummaryTests(unittest.TestCase):
    def test_weighted_brier_and_no_pooled_ap(self):
        a=audit_stock_day((.9,.2),(.05,.6),(1,3),(True,True))
        b=audit_stock_day((.1,None),(.8,None),(3,None),(True,False))
        out=summarize_information_days({"000012.SZ":{"2022-10-13":a},
                                        "000025.SZ":{"2022-10-13":b}},1)
        self.assertEqual((out["source_n"],out["current_feature_ready_n"],
                          out["matched_n"],out["positive_support"]),(4,3,3,1))
        self.assertIsNone(out["pooled_average_precision"])
        self.assertAlmostEqual(out["matched_weighted_brier"],(.01+.04+.01)/3)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):summarize_information_days({},1)
        with self.assertRaises(ValueError):summarize_information_days({"s":{}},1)
if __name__=="__main__":unittest.main()

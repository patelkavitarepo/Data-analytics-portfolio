"""Source-origin alignment and conditional prevalence synthetic tests."""
import unittest
from microstructure.information_population import audit_stock_day

class InformationPopulationTests(unittest.TestCase):
    def test_missing_features_not_imputed_stationary(self):
        out=audit_stock_day((.8,None,.1,.2),(.1,None,.7,.3),
                            (1,3,3,None),(True,False,True,True))
        self.assertEqual(out["all_source"]["source_n"],4)
        self.assertEqual(out["all_source"]["verifiable_n"],3)
        self.assertEqual(out["feature_ready"]["source_n"],3)
        self.assertEqual(out["feature_ready"]["verifiable_n"],2)
        self.assertEqual(out["current_unavailable_n"],1)
        self.assertEqual(out["future_label_unverifiable_n"],1)
        self.assertEqual(out["directions"]["1"]["matched_n"],2)
        self.assertTrue(out["not_an_executable_policy"])
    def test_probability_and_feature_alignment_fail_closed(self):
        with self.assertRaises(ValueError):
            audit_stock_day((.9,),(.8,),(1,),(True,))
        with self.assertRaises(ValueError):
            audit_stock_day((.2,None),(.3,None),(1,2),(True,True))
        with self.assertRaises(ValueError):
            audit_stock_day((.2,),(.3,),(1,2),(True,))
if __name__=="__main__":unittest.main()

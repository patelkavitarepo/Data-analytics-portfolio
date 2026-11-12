"""Case 016 synthetic ranking/calibration and missing-label invariants."""
import unittest
from microstructure.information_audit import prevalence,average_precision,calibration,descriptive_top_fraction

class InformationAuditTests(unittest.TestCase):
    def test_source_and_label_denominators(self):
        x=prevalence((1,2,3,None,None))
        self.assertEqual((x["source_n"],x["verifiable_n"],x["unknown_n"]),(5,3,2))
        self.assertEqual(x["class_rates"][1],1/3)
    def test_perfect_ranking_and_base_rate(self):
        self.assertEqual(average_precision((.9,.8,.1,.0),(1,1,2,2),1),1)
        self.assertAlmostEqual(average_precision((.5,)*4,(1,1,2,2),1),.5)
        self.assertIsNone(average_precision((.5,.6),(2,2),1))
    def test_ties_and_missing_probabilities(self):
        x=descriptive_top_fraction((.8,.8,.1,None),(1,2,3,1),1,.05)
        self.assertEqual(x["n"],1)
        self.assertTrue(x["ties_at_boundary"])
        with self.assertRaises(ValueError):average_precision((.1,),(1,2),1)
        with self.assertRaises(ValueError):calibration((1.01,),(1,),1)
    def test_fixed_calibration_bins_and_brier(self):
        x=calibration((0,.1,.9,1,None),(2,1,3,3,1),3)
        self.assertEqual(x["n"],4)
        self.assertEqual(x["bins"][0]["n"],1)
        self.assertEqual(x["bins"][1]["n"],1)
        self.assertEqual(x["bins"][9]["n"],2)
        self.assertAlmostEqual(x["brier"],(.0+.01+.01+0)/4)
    def test_no_unknown_label_as_stationary(self):
        x=calibration((.9,.1),(None,3),3)
        self.assertEqual(x["n"],1)
        self.assertAlmostEqual(x["brier"],.81)

if __name__=="__main__":unittest.main()

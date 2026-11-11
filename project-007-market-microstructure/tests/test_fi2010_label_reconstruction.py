import unittest
from microstructure.fi2010_label_reconstruction import (
    LabelReconstructionError, reconstruct_publisher_rule
)


class SourceLabelFormulaTests(unittest.TestCase):
    def test_h1_matches_published_threshold(self):
        # mid prices 100.0 -> 100.3 -> 100.6, each +0.3%
        bid=[99.9,100.2,100.5]
        ask=[100.1,100.4,100.7]
        source=[1,1,2]
        got=reconstruct_publisher_rule(ask,bid,source,1)
        self.assertEqual(got["valid_processed_quote_windows"],2)
        self.assertEqual(got["agreement_pct"],100.0)

    def test_h5_uses_mean_not_last_future_midpoint(self):
        # source mid 100, future mids 100,100,100,100,102
        mids=[100,100,100,100,100,102,102]
        bid=[m-0.1 for m in mids]
        ask=[m+0.1 for m in mids]
        labels=[1]*7
        labels[0]=2
        got=reconstruct_publisher_rule(ask,bid,labels,5)
        self.assertEqual(got["valid_processed_quote_windows"],2)
        # At origin 0 the future mean is 100.4: up (0.4%)
        self.assertLess(got["agreement_pct"],100.0)
        self.assertEqual(got["confusion_publisher_rows_candidate_columns"]["2"]["1"],1)

    def test_invalid_quote_window_excluded(self):
        ask=[100.1,99.9,100.4]
        bid=[100,100,100.2]
        got=reconstruct_publisher_rule(ask,bid,[2,2,2],1)
        self.assertEqual(got["valid_processed_quote_windows"],0)
        self.assertEqual(got["invalid_quote_windows"],2)

    def test_width_and_horizon_checks(self):
        with self.assertRaises(ValueError):
            reconstruct_publisher_rule([100,101],[99],[2,2],1)
        with self.assertRaises(ValueError):
            reconstruct_publisher_rule([100,101],[99,100],[2,2],3)


if __name__=="__main__":
    unittest.main()

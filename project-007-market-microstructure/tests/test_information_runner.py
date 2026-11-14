"""D016 one-time runner pre-price manifest and pure output checks."""
import unittest
from research.run_information_audit_once import DATE_SHA
from research.freeze_information_dates_once import load_manifest
from microstructure.information_population import audit_stock_day

class InformationRunnerTests(unittest.TestCase):
    def test_frozen_manifest(self):
        m=load_manifest()
        self.assertEqual(m["date_list_sha256"],DATE_SHA)
        self.assertIs(m["price_or_label_columns_read"],False)
        self.assertEqual(m["dates"]["confirmation"][0],"2022-10-13")
        self.assertEqual(m["dates"]["sealed_final"][0],"2022-10-27")
    def test_all_missing_scores_have_no_invented_information(self):
        a=audit_stock_day((None,None),(None,None),(1,None),(False,False))
        self.assertEqual(a["all_source"]["source_n"],2)
        self.assertEqual(a["feature_ready"]["source_n"],0)
        self.assertIsNone(a["directions"]["1"]["average_precision"])
        self.assertIsNone(a["directions"]["3"]["calibration"]["brier"])

if __name__=="__main__":unittest.main()

import copy
import tempfile
import unittest
from pathlib import Path

from microstructure.diagnostics import describe_pairs
from microstructure.independent_verify import VerificationError, independently_verify


class IndependentVerificationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.m = Path(folder.name) / "m.csv"
        self.b = Path(folder.name) / "b.csv"

    def fixture(self):
        self.m.write_text(
            "34200.000000001,1,101,80,1000000,1\n"
            "34201,2,101,20,1000000,1\n"
            "34202,7,0,0,-1,-1\n"
            "34203,7,0,0,0,-1\n"
            "34204,7,0,0,1,-1\n"
            "34500,1,102,50,1000100,-1\n"
            "34501,3,103,10,1000000,1\n"
            "34502,1,104,30,1000000,1\n",
            encoding="utf-8",
        )
        self.b.write_text(
            "1000100,60,1000000,40\n"
            "1000100,50,1000000,50\n"
            "1000100,50,1000000,50\n"
            "1000100,50,1000000,50\n"
            "1000100,50,1000000,50\n"
            "1000200,50,1000000,50\n"
            "9999999999,0,1000000,50\n"
            "1000200,50,1000100,50\n",
            encoding="utf-8",
        )
        return describe_pairs(self.m, self.b, levels=1, bucket_seconds=300)

    def test_independent_recalculation_succeeds(self):
        report = self.fixture()
        verification = independently_verify(self.m, self.b, report)
        self.assertEqual(verification["events_verified"], 8)
        self.assertEqual(verification["windows_verified"], 2)
        self.assertEqual(verification["status"], "independently_verified_descriptive_report")

    def test_corrupted_report_mid_move_is_detected(self):
        report = self.fixture()
        bad = copy.deepcopy(report)
        bad["windows"][1]["mid_move_up_count"] += 1
        with self.assertRaisesRegex(VerificationError, "mid_move_up_count"):
            independently_verify(self.m, self.b, bad)

    def test_corrupted_mean_is_detected(self):
        bad = self.fixture()
        bad["windows"][0]["mean_depth_imbalance_event_weighted"] += 0.1
        with self.assertRaisesRegex(VerificationError, "mean depth imbalance"):
            independently_verify(self.m, self.b, bad)

    def test_corrupted_row_count_is_detected(self):
        bad = self.fixture()
        bad["audit"]["events_checked"] += 1
        with self.assertRaisesRegex(VerificationError, "overall row count"):
            independently_verify(self.m, self.b, bad)

    def test_source_mutation_detected(self):
        report = self.fixture()
        self.m.write_text(self.m.read_text() + "34503,1,105,10,1000000,1\n")
        with self.assertRaisesRegex(VerificationError, "SHA256"):
            independently_verify(self.m, self.b, report)

    def test_prefix_report_is_rejected(self):
        report = self.fixture()
        report["audit"]["scope"] = "prefix_only"
        with self.assertRaisesRegex(VerificationError, "full-file"):
            independently_verify(self.m, self.b, report)

    def test_audit_counts_one_sided_quotes_through_halt(self):
        self.m.write_text(
            "34200,1,101,80,1000000,1\n"
            "34201,7,0,0,-1,-1\n"
            "34202,7,0,0,0,-1\n"
            "34203,7,0,0,1,-1\n"
            "34204,1,102,50,1000100,-1\n",
            encoding="utf-8",
        )
        self.b.write_text(
            "9999999999,0,1000000,50\n" * 4
            + "1000200,50,1000000,50\n",
            encoding="utf-8",
        )
        report = describe_pairs(self.m, self.b, levels=1)
        self.assertEqual(report["audit"]["one_sided_or_empty_quotes"], 4)
        self.assertEqual(report["windows"][0]["one_sided_count"], 1)
        result = independently_verify(self.m, self.b, report)
        self.assertEqual(result["events_verified"], 5)

    def test_missing_window_is_rejected(self):
        report = self.fixture()
        report["windows"].pop()
        with self.assertRaisesRegex(VerificationError, "window count"):
            independently_verify(self.m, self.b, report)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from microstructure.audit import AuditError
from microstructure.diagnostics import describe_pairs


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.messages = Path(tmp.name) / "messages.csv"
        self.book = Path(tmp.name) / "book.csv"

    def diagnose(self, messages, book, bucket_seconds=300, levels=1):
        self.messages.write_text(messages, encoding="utf-8")
        self.book.write_text(book, encoding="utf-8")
        return describe_pairs(
            self.messages, self.book, levels=levels, bucket_seconds=bucket_seconds
        )

    def test_hand_calculated_two_buckets_and_mid_directions(self):
        result = self.diagnose(
            "34200.000000001,1,1,10,1000000,1\n"
            "34210,2,1,10,1000000,1\n"
            "34220,4,1,10,1000000,1\n"
            "34501,1,2,10,1000050,1\n",
            "1000100,60,1000000,40\n"
            "1000100,50,1000000,50\n"
            "1000100,50,1000050,50\n"
            "1000150,50,1000050,50\n",
        )
        w0, w1 = result["windows"]
        self.assertEqual([w0["window_start"], w1["window_start"]], ["09:30:00", "09:35:00"])
        self.assertEqual(w0["event_count"], 3)
        self.assertEqual(w0["eligible_quote_count"], 3)
        self.assertEqual(w0["mean_spread_usd_event_weighted"], 0.00833333)
        self.assertEqual(w0["mean_depth_imbalance_event_weighted"], -0.06666667)
        self.assertEqual((w0["mid_move_up_count"], w0["mid_move_unchanged_count"]), (1, 1))
        self.assertEqual((w1["mid_move_up_count"], w1["event_count"]), (1, 1))
        self.assertEqual(result["audit"]["events_checked"], 4)
        self.assertEqual(result["status"], "descriptive_only_no_forecast_or_execution")

    def test_halt_and_resume_reset_mid_comparison(self):
        result = self.diagnose(
            "34200,1,1,10,1000000,1\n"
            "34201,7,0,0,-1,-1\n"
            "34202,7,0,0,0,-1\n"
            "34203,1,2,10,1000000,1\n"
            "34204,7,0,0,1,-1\n"
            "34205,1,3,10,1000000,1\n",
            "1000100,10,1000000,10\n" * 5
            + "1000200,10,1000000,10\n",
        )
        w = result["windows"][0]
        self.assertEqual(w["event_count"], 6)
        self.assertEqual(w["halt_marker_count"], 3)
        self.assertEqual(w["halted_event_count"], 3)
        self.assertEqual(w["eligible_quote_count"], 2)
        self.assertEqual(
            (w["mid_move_up_count"], w["mid_move_down_count"], w["mid_move_unchanged_count"]),
            (0, 0, 0),
        )

    def test_one_sided_and_locked_quote_interrupt_comparison(self):
        got = self.diagnose(
            "34200,1,1,10,1000000,1\n"
            "34201,3,1,10,1000000,1\n"
            "34202,1,2,10,1000000,1\n"
            "34203,1,3,10,1000000,1\n",
            "1000100,10,1000000,10\n"
            "9999999999,0,1000000,10\n"
            "1000000,10,1000000,10\n"
            "1000200,10,1000000,10\n",
        )
        w = got["windows"][0]
        self.assertEqual((w["one_sided_count"], w["locked_or_crossed_count"]), (1, 1))
        self.assertEqual(w["eligible_quote_count"], 2)
        self.assertEqual(w["mid_move_up_count"], 0)

    def test_mismatched_pairs_are_rejected_before_aggregation(self):
        with self.assertRaisesRegex(AuditError, "counts differ"):
            self.diagnose(
                "34200,1,1,10,1000000,1\n34201,1,2,10,1000000,1\n",
                "1000100,10,1000000,10\n",
            )

    def test_bad_bucket_intervals_fail(self):
        self.messages.write_text("34200,1,1,10,1000000,1\n")
        self.book.write_text("1000100,10,1000000,10\n")
        for interval in (0, -30, 700, 86401, True, 1.5):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                describe_pairs(self.messages, self.book, bucket_seconds=interval)

    def test_halt_marker_invalid_snapshot_rejected_before_diagnostics(self):
        with self.assertRaisesRegex(AuditError, "halt marker must duplicate"):
            self.diagnose(
                "34200,1,1,10,1000000,1\n34201,7,0,0,-1,-1\n",
                "1000100,10,1000000,10\n1000100,11,1000000,10\n",
            )


if __name__ == "__main__":
    unittest.main()

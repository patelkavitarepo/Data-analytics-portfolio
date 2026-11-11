import tempfile
import unittest
from pathlib import Path
from microstructure.audit import AuditError, audit_pairs


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        base = Path(self.folder.name)
        self.messages = base / "messages.csv"
        self.books = base / "orderbook.csv"

    def load(self, messages, books, levels=1, max_events=None):
        self.messages.write_text(messages, encoding="utf-8")
        self.books.write_text(books, encoding="utf-8")
        return audit_pairs(self.messages, self.books, levels, max_events)

    def test_valid_paired_quotes_and_fixed_point_spread(self):
        got = self.load(
            "34200.100000001,1,10,100,1000000,1\n"
            "34200.200000001,2,10,20,1000000,1\n",
            "1000100,90,1000000,110\n"
            "1000100,90,1000000,90\n",
        )
        self.assertEqual(got["events_checked"], 2)
        self.assertEqual(got["event_type_counts"], {"1": 1, "2": 1})
        self.assertEqual(got["mean_spread_usd"], 0.01)
        self.assertEqual(got["valid_two_sided_nonhalt_quotes"], 2)
        self.assertEqual(got["scope"], "complete_pair")

    def test_row_count_mismatch_fails_closed(self):
        with self.assertRaisesRegex(AuditError, "counts differ"):
            self.load("34200,1,10,100,1000000,1\n", "")

    def test_reversed_timestamp_fails_not_sorted(self):
        with self.assertRaisesRegex(AuditError, "time reversed"):
            self.load(
                "34202,1,10,10,1000000,1\n34201,1,11,10,1000000,1\n",
                "1000100,10,1000000,10\n" * 2,
            )

    def test_duplicate_timestamp_retains_both_events(self):
        got = self.load(
            "34200.123456789,1,10,10,1000000,1\n"
            "34200.123456789,4,10,10,1000000,1\n",
            "1000100,10,1000000,10\n" * 2,
        )
        self.assertEqual(got["equal_timestamp_neighbors"], 1)
        self.assertEqual(got["events_checked"], 2)

    def test_unexpected_event_fails(self):
        with self.assertRaisesRegex(AuditError, "unknown event"):
            self.load("34200,9,1,10,1000000,1\n", "1000100,10,1000000,10\n")

    def test_halt_duplicates_are_not_normal_quotes(self):
        got = self.load(
            "34200,7,0,0,-1,-1\n", "1000100,10,1000000,10\n"
        )
        self.assertEqual(got["valid_two_sided_nonhalt_quotes"], 0)

    def test_locked_quote_counted_not_cleaned(self):
        got = self.load(
            "34200,1,1,10,1000000,1\n", "1000000,10,1000000,10\n"
        )
        self.assertEqual(got["locked_or_crossed_quotes"], 1)
        self.assertIsNone(got["mean_spread_usd"])

    def test_invalid_level_order_fails(self):
        with self.assertRaisesRegex(AuditError, "asks not strictly ascending"):
            self.load(
                "34200,1,1,10,1000000,1\n",
                "1000200,10,1000000,10,1000100,20,999900,20\n", levels=2,
            )

    def test_empty_depth_sentinel_is_not_quote(self):
        got = self.load(
            "34200,5,0,10,1000000,-1\n",
            "9999999999,0,-9999999999,0\n",
        )
        self.assertEqual(got["one_sided_or_empty_quotes"], 1)
        self.assertIsNone(got["mean_best_level_imbalance"])

    def test_prefix_cannot_claim_complete_file(self):
        got = self.load(
            "34200,1,1,10,1000000,1\n34201,1,2,10,1000000,1\n",
            "1000100,10,1000000,10\n",
            max_events=1,
        )
        self.assertEqual(got["scope"], "prefix_only")
        self.assertEqual(got["events_checked"], 1)

    def test_nonfinite_time_rejected(self):
        with self.assertRaisesRegex(AuditError, "nonfinite"):
            self.load("NaN,1,1,10,1000000,1\n", "1000100,10,1000000,10\n")


if __name__ == "__main__":
    unittest.main()

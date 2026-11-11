import unittest
from datetime import date, timedelta
from decimal import Decimal

from microstructure.chronology import (
    Snapshot, label_after_elapsed_time, prototype_session_partition
)


def q(t, bid=1000000, ask=1000100, bs=50, ass=50, state="active", day="2026-01-02"):
    return Snapshot(day, Decimal(str(t)), state, bid, ask, bs, ass)


class ProspectiveLabelTests(unittest.TestCase):
    def test_post_event_future_target_strictly_later(self):
        rows = [q("34200", bs=90, ass=10), q("34200", bid=1000050),
                q("34200.25", bid=1000050), q("34200.5", bid=999950)]
        labels = label_after_elapsed_time(rows, Decimal("0.25"))
        self.assertEqual(labels[0].target_index, 2)
        self.assertEqual(labels[0].target_time, Decimal("34200.25"))
        self.assertEqual(labels[0].origin_imbalance, Decimal("0.8"))
        self.assertEqual(labels[0].direction, 1)
        self.assertEqual(labels[1].target_index, 2)
        self.assertEqual(labels[2].target_index, 3)
        self.assertIsNone(labels[3].direction)
        self.assertEqual(labels[3].reason, "end_of_session")

    def test_time_horizon_is_elapsed_seconds_not_number_of_events(self):
        rows = [q("10"), q("11"), q("11.5"), q("12.1", bid=1000100, ask=1000200)]
        labels = label_after_elapsed_time(rows, 2)
        self.assertEqual(labels[0].target_index, 3)
        self.assertEqual(labels[0].direction, 1)
        self.assertEqual(labels[1].reason, "end_of_session")

    def test_exact_horizon_boundary_is_inclusive_but_origin_is_not(self):
        labels = label_after_elapsed_time([q(100), q(101, bid=1000100, ask=1000200)], 1)
        self.assertEqual(labels[0].target_time, Decimal(101))

    def test_unchanged_price_is_explicit_neutral_class(self):
        labels = label_after_elapsed_time([q(100), q(101)], 1)
        self.assertEqual(labels[0].direction, 0)

    def test_halt_interrupts_before_horizon(self):
        rows = [q(100), q(101, state="halt"), q(102, bid=1000100, ask=1000200)]
        labels = label_after_elapsed_time(rows, 1)
        self.assertIsNone(labels[0].target_index)
        self.assertEqual(labels[0].reason, "interrupted_before_horizon")
        self.assertEqual(labels[1].reason, "halt")

    def test_invalid_quote_interrupts_even_if_future_is_good(self):
        rows = [q(100), q(101, bid=1000100, ask=1000100),
                q(102, bid=1000050, ask=1000150)]
        labels = label_after_elapsed_time(rows, 1)
        self.assertEqual(labels[0].reason, "interrupted_before_horizon")
        self.assertEqual(labels[1].reason, "unusable_origin")
        self.assertEqual(labels[2].reason, "end_of_session")

    def test_no_cross_session_target_and_no_time_travel(self):
        rows = [q(86398), q(86399), q(10, day="2026-01-03", bid=1000200, ask=1000300)]
        labels = label_after_elapsed_time(rows, 2)
        self.assertEqual(labels[0].reason, "end_of_session")
        self.assertEqual(labels[1].reason, "end_of_session")
        self.assertEqual(labels[2].reason, "end_of_session")

    def test_feature_cannot_change_when_only_future_price_changes(self):
        rows = [q(100, bs=80, ass=20), q(101)]
        later = [rows[0], q(101, bid=1000200, ask=1000300)]
        a, b = label_after_elapsed_time(rows, 1), label_after_elapsed_time(later, 1)
        self.assertEqual(a[0].origin_imbalance, b[0].origin_imbalance)
        self.assertNotEqual(a[0].direction, b[0].direction)

    def test_all_input_rows_preserved(self):
        rows = [q(1, state="unusable"), q(2, bs=0), q(3), q(4)]
        labels = label_after_elapsed_time(rows, 1)
        self.assertEqual(len(labels), len(rows))
        self.assertEqual([x.origin_index for x in labels], list(range(len(rows))))
        self.assertEqual(labels[0].reason, "unusable")
        self.assertEqual(labels[1].reason, "unusable_origin")
        self.assertEqual(labels[2].direction, 0)

    def test_order_or_illegal_time_refused(self):
        for rows in ([q(2), q(1)], [q(1, day="2026-01-03"), q(2)],
                     [q(86400)], [q("NaN")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                label_after_elapsed_time(rows, 1)

    def test_invalid_horizons_refused(self):
        for horizon in (0, -1, "NaN", "Infinity", True, 86400):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                label_after_elapsed_time([q(1)], horizon)

    def test_empty_input_has_no_synthetic_results(self):
        self.assertEqual(label_after_elapsed_time([], 1), ())


class SessionSplitTests(unittest.TestCase):
    def setUp(self):
        self.days = [(date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(9)]

    def test_sessions_are_disjoint_with_explicit_embargo(self):
        plan = prototype_session_partition(self.days, 3, 2, 2, 1)
        self.assertEqual(plan.train, tuple(self.days[:3]))
        self.assertEqual(plan.embargo_train_validation, (self.days[3],))
        self.assertEqual(plan.validation, tuple(self.days[4:6]))
        self.assertEqual(plan.embargo_validation_holdout, (self.days[6],))
        self.assertEqual(plan.holdout, tuple(self.days[7:]))
        self.assertEqual(len(set(sum((plan.train, plan.embargo_train_validation,
                                      plan.validation, plan.embargo_validation_holdout,
                                      plan.holdout), ()))), 9)

    def test_one_day_refused_and_no_implicit_split(self):
        with self.assertRaisesRegex(ValueError, "need exactly"):
            prototype_session_partition(self.days[:1], 3, 2, 2)

    def test_duplicate_or_unsorted_sessions_refused(self):
        for days in (self.days[:3] + self.days[3:4] + self.days[3:],
                     tuple(reversed(self.days))):
            with self.subTest(days=days), self.assertRaises(ValueError):
                prototype_session_partition(days, 3, 2, 2)

    def test_invalid_sizes_or_dates_refused(self):
        for args in ((3, 2, 2, 0), (3, 2, 2, True), (3, -1, 3, 1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                prototype_session_partition(self.days, *args)
        with self.assertRaises(ValueError):
            prototype_session_partition(["2026-01-01", "abc"] + self.days[2:], 3, 2, 2)


if __name__ == "__main__":
    unittest.main()

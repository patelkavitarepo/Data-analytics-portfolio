"""Synthetic-only scheduled-gap provenance and non-gap counterfactual tests."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
import unittest

from microstructure.stockday_labels import Quote
from microstructure.gap_boundary_audit import (
    gap_boundary_report, _long_gap_edges, _lunch_match, _spans,
)
from microstructure.quote_quality_sensitivity import FROZEN_PRIMARY, _counts
from microstructure.stockday_labels import labels_from_quotes

TZ = timezone(timedelta(hours=8))
DAYS = ("2022-01-04", "2022-01-05", "2022-01-06",
        "2022-01-07", "2022-01-10")


def examples(*, stale=False):
    results = []
    clock = ("11:29:30", "11:29:45", "11:30:00",
             "13:00:00", "13:00:15", "13:00:30",
             "13:00:45", "13:01:00", "13:01:15", "13:01:30")
    for day in DAYS:
        for i, t in enumerate(clock):
            dt = datetime.fromisoformat(day + "T" + t).replace(tzinfo=TZ)
            mid = Decimal("100") + Decimal(i) / Decimal("100")
            results.append(Quote(
                "000012.SZ", day, dt,
                mid-Decimal("0.01"), mid+Decimal("0.01"),
                stale=bool(stale and i == 4), missing_depth=False
            ))
    return tuple(results)


class BoundaryAuditTests(unittest.TestCase):
    def test_detects_exact_five_lunch_gaps_and_timestamp_edges(self):
        q = examples()
        gaps = _long_gap_edges(q, "000012.SZ")
        self.assertEqual(len(gaps), 5)
        self.assertEqual(set(x["duration_seconds"] for x in gaps), {5400})
        self.assertTrue(all(x["matches_frozen_lunch_time_heuristic"] for x in gaps))
        self.assertTrue(all(x["start_local"] == "11:30:00" for x in gaps))
        self.assertTrue(all(x["end_local"] == "13:00:00" for x in gaps))

    def test_regular_gap_does_not_get_called_lunch(self):
        q = examples()
        self.assertFalse(_lunch_match(q[1].available_at, q[4].available_at))
        bogus = list(q)
        bogus[3] = Quote(
            bogus[3].symbol, bogus[3].trading_date,
            bogus[2].available_at + timedelta(minutes=12),
            bogus[3].bid, bogus[3].ask
        )
        # This would reorder data and should fail in full label validation.
        with self.assertRaisesRegex(ValueError, "unsorted"):
            labels_from_quotes(bogus, 5)

    def test_frozen_reference_and_unsafe_no_gap_counterfactual(self):
        q = examples()
        first = labels_from_quotes(q, 5, max_gap_seconds=30)
        c = _counts(first)
        frozen = (c["all"], c["up"], c["stationary"], c["down"], c["unlabelled"])
        with patch.dict(FROZEN_PRIMARY, {"000012.SZ": frozen}):
            result = gap_boundary_report(q, "000012.SZ", DAYS)
        self.assertEqual(result["lunch_heuristic_matches"], 5)
        self.assertEqual(result["unexplained_by_lunch_heuristic"], 0)
        self.assertEqual(result["strict_reference_gap_crossings"]["distinct_origins_crossing_any_long_gap"], 0)
        no_gap = result["unsafe_no_gap_counterfactuals"]["flags_respected"]
        self.assertGreater(no_gap["source_gap_crossings"]["distinct_origins_crossing_any_long_gap"], 0)
        self.assertGreater(no_gap["vs_strict_30s"]["newly_eligible_from_excluded"], 0)
        self.assertEqual(result["oracle_mismatches"], 0)
        self.assertEqual(result["oracle_verified_origin_count"], len(q)*3)
        self.assertEqual(result["unsafe_no_gap_counterfactuals"]["both_flags_ignored"]["independent_oracle_mismatches"], 0)

    def test_flagged_quote_can_interrupt_gap_spanning_even_without_time_rule(self):
        q = examples(stale=True)
        first = labels_from_quotes(q, 5, max_gap_seconds=30)
        c = _counts(first)
        frozen = (c["all"], c["up"], c["stationary"], c["down"], c["unlabelled"])
        with patch.dict(FROZEN_PRIMARY, {"000012.SZ": frozen}):
            result = gap_boundary_report(q, "000012.SZ", DAYS)
        strict = result["unsafe_no_gap_counterfactuals"]["flags_respected"]
        ignored = result["unsafe_no_gap_counterfactuals"]["both_flags_ignored"]
        self.assertGreater(
            ignored["counts"]["eligible"], strict["counts"]["eligible"]
        )
        self.assertEqual(ignored["independent_oracle_mismatches"], 0)

    def test_reject_nonfrozen_source(self):
        with self.assertRaisesRegex(AssertionError, "reference"):
            gap_boundary_report(examples(), "000012.SZ", DAYS)
        with self.assertRaisesRegex(ValueError, "nonpreregistered"):
            gap_boundary_report(examples(), "000099.SZ", DAYS)


if __name__ == "__main__":
    unittest.main()

"""D008 session-aware labeling: synthetic source-like quote fixtures only.

No vendor network or original market quotes. The slow reference recomputes
targets independently and tests unchanged older behavior where applicable.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
import unittest

from microstructure.session_labels import (
    exchange_session, session_labels_from_quotes
)
from microstructure.session_oracle import (
    independent_session_labels, verify_session_labels
)
from microstructure.stockday_labels import Quote, labels_from_quotes

TZ = timezone(timedelta(hours=8))


def q(clock, mid="100", *, day="2022-01-04", stock="000012.SZ",
      stale=False, missing=False, bad=False):
    stamp = datetime.fromisoformat(day + "T" + clock).replace(tzinfo=TZ)
    center = Decimal(str(mid))
    return Quote(stock, day, stamp, center-Decimal("0.01"),
                 center-Decimal("0.01") if bad else center+Decimal("0.01"),
                 stale, missing)


class ShenzhenSessionLabelsTests(unittest.TestCase):
    def test_explicit_local_session_endpoints(self):
        self.assertEqual(exchange_session(q("09:30:00").available_at), "morning")
        self.assertEqual(exchange_session(q("11:30:00").available_at), "morning")
        self.assertEqual(exchange_session(q("13:00:00").available_at), "afternoon")
        self.assertEqual(exchange_session(q("14:57:00").available_at), "afternoon")
        self.assertEqual(exchange_session(q("15:00:00").available_at), "afternoon")
        for clock in ("09:29:59", "11:30:01", "12:00:00", "12:59:59", "15:00:01"):
            with self.subTest(clock=clock):
                self.assertIsNone(exchange_session(q(clock).available_at))

    def test_no_long_gap_rule_still_prevents_lunch_crossing(self):
        # Four morning quotes followed by six afternoon quotes. The legacy
        # no-gap algorithm creates four artificial targets across lunch.
        rows = [
            q("11:29:15"), q("11:29:30"), q("11:29:45"), q("11:30:00"),
            q("13:00:00", "101"), q("13:00:15", "101"),
            q("13:00:30", "101"), q("13:00:45", "101"),
            q("13:01:00", "101"), q("13:01:15", "101"),
        ]
        legacy = labels_from_quotes(rows, 5, max_gap_seconds=None)
        self.assertTrue(any(x.classification is not None for x in legacy[:4]))
        independent = session_labels_from_quotes(rows, 5, max_gap_seconds=None)
        self.assertTrue(all(x.classification is None for x in independent[:4]))
        self.assertEqual(independent[4].classification, 2)
        self.assertEqual(independent[4].target_indices, (5, 6, 7, 8, 9))
        self.assertEqual(verify_session_labels(rows, 5, max_gap_seconds=None)["mismatches"], 0)

    def test_outside_source_session_always_unlabelled(self):
        rows = [q("11:30:00"), q("12:00:00"), q("13:00:00"),
                q("13:00:15"), q("13:00:30")]
        labels = session_labels_from_quotes(rows, 1, max_gap_seconds=None)
        self.assertEqual(labels[1].excluded, "outside_session")
        self.assertEqual(labels[0].excluded, "incomplete_future")
        self.assertEqual(labels[2].classification, 2)
        self.assertEqual(verify_session_labels(rows, 1, max_gap_seconds=None)["mismatches"], 0)

    def test_short_quote_gap_still_breaks_inside_session(self):
        rows = [q("09:30:00"), q("09:30:15"),
                q("09:31:10"), q("09:31:25")]
        strict = session_labels_from_quotes(rows, 1, max_gap_seconds=30)
        loose = session_labels_from_quotes(rows, 1, max_gap_seconds=None)
        self.assertIsNone(strict[1].classification)
        self.assertEqual(loose[1].classification, 2)
        self.assertEqual(verify_session_labels(rows, 1, max_gap_seconds=30)["mismatches"], 0)

    def test_stock_and_day_never_cross(self):
        rows = [
            q("13:00:00", stock="000012.SZ"),
            q("13:00:00", stock="000025.SZ"),
            q("13:00:00", day="2022-01-05", stock="000012.SZ"),
        ]
        labels = session_labels_from_quotes(rows, 1, max_gap_seconds=None)
        self.assertEqual([x.classification for x in labels], [None, None, None])
        self.assertEqual(verify_session_labels(rows, 1, max_gap_seconds=None)["mismatches"], 0)

    def test_invalid_quote_and_flags_break_forward_window(self):
        rows = [q("13:00:00"), q("13:00:15", stale=True),
                q("13:00:30"), q("13:00:45", missing=True),
                q("13:01:00"), q("13:01:15", bad=True)]
        labels = session_labels_from_quotes(rows, 1)
        self.assertEqual(labels[0].excluded, "incomplete_future")
        self.assertEqual(labels[1].excluded, "invalid_or_stale_quote")
        self.assertEqual(labels[3].excluded, "invalid_or_stale_quote")
        self.assertEqual(labels[5].excluded, "invalid_or_stale_quote")
        self.assertEqual(verify_session_labels(rows, 1)["mismatches"], 0)

    def test_different_future_mean_not_end_price(self):
        rows = [q("13:00:00", "100"), q("13:00:15","100"),
                q("13:00:30","100"),q("13:00:45","100.3")]
        # Mean next three: 100.1 (+0.1%), stationary; final +0.3%.
        self.assertEqual(session_labels_from_quotes(rows,3)[0].classification,2)

    def test_reject_utc_and_duplicate_or_unsorted_source_rows(self):
        old = q("13:00:00")
        utc = replace(old, available_at=old.available_at.astimezone(timezone.utc))
        with self.assertRaisesRegex(ValueError, "UTC\\+08:00"):
            session_labels_from_quotes([utc], 1)
        with self.assertRaisesRegex(ValueError, "unsorted"):
            session_labels_from_quotes([q("13:00:15"), q("13:00:00")], 1)
        with self.assertRaisesRegex(ValueError, "duplicated"):
            session_labels_from_quotes([old,old], 1)

    def test_reject_invalid_options(self):
        rows = [q("13:00:00")]
        for k in (0,-1,True,1.5):
            with self.subTest(k=k), self.assertRaises(ValueError):
                session_labels_from_quotes(rows,k)
        for gap in (0, -10, True, 90000):
            with self.subTest(gap=gap), self.assertRaises(ValueError):
                session_labels_from_quotes(rows,1,max_gap_seconds=gap)
        for threshold in ("NaN",0,1):
            with self.subTest(t=threshold), self.assertRaises(ValueError):
                session_labels_from_quotes(rows,1,threshold=threshold)

    def test_oracle_detects_modified_optimized_class(self):
        from unittest.mock import patch
        rows = [q("13:00:00"), q("13:00:15")]
        real = list(session_labels_from_quotes(rows,1))
        real[0] = replace(real[0], classification=1)
        with patch("microstructure.session_oracle.session_labels_from_quotes",
                   return_value=tuple(real)):
            with self.assertRaisesRegex(AssertionError, "disagreement"):
                verify_session_labels(rows,1)

    def test_seeded_differential_across_five_horizons(self):
        rnd = random.Random(8008)
        rows = []
        for day in ("2022-01-04", "2022-01-05"):
            for start, clock in ((datetime.fromisoformat(day+"T09:30:00"),
                                  "morning"), (datetime.fromisoformat(day+"T13:00:00"),
                                               "afternoon")):
                elapsed = 0
                for i in range(80):
                    elapsed += 45 if i%23==0 else 15
                    dt = (start+timedelta(seconds=elapsed)).time().isoformat()
                    mid = Decimal("100") + Decimal(rnd.randrange(-30,30))/1000
                    rows.append(q(dt, str(mid),day=day,stale=i%19==0,
                                  missing=i%29==0))
        for k in (1,2,3,5,10):
            with self.subTest(k=k):
                x = verify_session_labels(rows,k,max_gap_seconds=30)
                self.assertEqual(x["rows_verified"], len(rows))
                self.assertEqual(x["mismatches"], 0)

if __name__ == "__main__":
    unittest.main()

"""Independent label oracle tests. All observations are synthetic."""
import random
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
from dataclasses import replace

from microstructure.stockday_labels import Quote, labels_from_quotes
from microstructure.stockday_oracle import verify_labels, slow_labels


TZ = timezone(timedelta(hours=8))


def quotes(seed=7007):
    randomizer = random.Random(seed)
    rows = []
    for day in ("2022-01-04", "2022-01-05"):
        base = datetime.fromisoformat(day + "T09:30:00").replace(tzinfo=TZ)
        seconds = 0
        for index in range(160):
            seconds += 60 if index % 19 == 0 else 15
            mid = Decimal("100") + Decimal(randomizer.randrange(-50, 51)) / 1000
            rows.append(Quote(
                "000012.SZ", day, base + timedelta(seconds=seconds),
                mid - Decimal("0.01"), mid + Decimal("0.01"),
                stale=index % 37 == 0,
                missing_depth=index % 43 == 0,
            ))
    return rows


class IndependentStockdayOracleTests(unittest.TestCase):
    def test_seeded_differential_stress_at_all_horizons(self):
        rows = quotes()
        for h in (1, 2, 3, 5, 10):
            with self.subTest(horizon=h):
                report = verify_labels(rows, h)
                self.assertEqual(report["rows_verified"], len(rows))
                self.assertEqual(report["mismatched_rows"], 0)

    def test_detects_corrupted_optimized_class(self):
        rows = quotes()
        normal = list(labels_from_quotes(rows, 1))
        eligible = next(i for i, x in enumerate(normal) if x.classification is not None)
        normal[eligible] = replace(
            normal[eligible],
            classification=(3 if normal[eligible].classification != 3 else 1),
        )
        with patch("microstructure.stockday_oracle.labels_from_quotes",
                   return_value=tuple(normal)):
            with self.assertRaisesRegex(AssertionError, "disagrees"):
                verify_labels(rows, 1)

    def test_no_averaging_across_trading_date(self):
        x = [
            Quote("000012.SZ", "2022-01-04",
                  datetime(2022,1,4,15,0,tzinfo=TZ),
                  Decimal("100"), Decimal("100.02")),
            Quote("000012.SZ", "2022-01-05",
                  datetime(2022,1,5,9,30,tzinfo=TZ),
                  Decimal("102"), Decimal("102.02")),
        ]
        self.assertEqual(slow_labels(x,1)[0][0], None)
        self.assertEqual(verify_labels(x,1)["mismatched_rows"],0)


if __name__ == "__main__":
    unittest.main()

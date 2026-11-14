"""Synthetic local quote rows; no real Quant-Arena data used."""
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from microstructure.quant_arena_pilot import (
    PilotError, REQUIRED_FIELDS, convert_quote_rows, pilot_summary
)


def row(day, seconds, mid, symbol="000012.SZ", *, stale=False, missing=False):
    tz = timezone(timedelta(hours=8))
    moment = datetime.fromisoformat(day + "T09:30:00").replace(tzinfo=tz) + timedelta(seconds=seconds)
    center = Decimal(str(mid))
    return {
        "symbol": symbol,
        "available_at": moment,
        "source_event_time": moment - timedelta(seconds=1),
        "bid_price_1": center - Decimal("0.01"),
        "ask_price_1": center + Decimal("0.01"),
        "stale": stale,
        "missing_depth": missing,
    }


class QuantArenaPilotTests(unittest.TestCase):
    def test_realistic_two_day_synthetic_counts_and_no_cross_day(self):
        raw = [
            row("2022-01-04", 0, 100),
            row("2022-01-04", 15, 100.2),
            row("2022-01-04", 30, 100.4),
            row("2022-01-05", 0, 101),
            row("2022-01-05", 15, 101.5),
            row("2022-01-05", 30, 101.5),
        ]
        observations, qc = convert_quote_rows(
            raw, "000012.SZ", ["2022-01-04", "2022-01-05"]
        )
        report = pilot_summary(
            observations, "000012.SZ", ["2022-01-04", "2022-01-05"]
        )
        first = report["counts_by_horizon"]["1"]
        self.assertEqual(qc["selected_observations"], 6)
        self.assertEqual(first["up"], 2)
        self.assertEqual(first["stationary"], 2)
        self.assertEqual(first["unlabelled"], 2)
        self.assertEqual(first["stock_date_boundary_crossings"], 0)
        self.assertEqual(sum(first[field] for field in (
            "up", "stationary", "down", "unlabelled"
        )), 6)
        self.assertEqual(report["counts_by_horizon"]["10"]["unlabelled"], 6)

    def test_null_stale_and_missing_are_not_healthy(self):
        data = [
            row("2022-01-04", 0, 100),
            row("2022-01-04", 15, 100, stale=None),
            row("2022-01-04", 30, 100, missing=None),
            row("2022-01-04", 45, 100),
        ]
        obs, _ = convert_quote_rows(data, "000012.SZ", ["2022-01-04"])
        self.assertFalse(obs[0].stale)
        self.assertTrue(obs[1].stale)
        self.assertTrue(obs[2].missing_depth)
        result = pilot_summary(obs, "000012.SZ", ["2022-01-04"])
        self.assertEqual(result["counts_by_horizon"]["1"]["unlabelled"], 4)

    def test_gap_is_not_interpolated(self):
        data = [row("2022-01-04", 0, 100), row("2022-01-04", 45, 101)]
        obs, _ = convert_quote_rows(data, "000012.SZ", ["2022-01-04"])
        result = pilot_summary(obs, "000012.SZ", ["2022-01-04"])
        self.assertEqual(result["counts_by_horizon"]["1"]["unlabelled"], 2)

    def test_wrong_tz_and_future_source_event_rejected(self):
        good = row("2022-01-04", 0, 100)
        bad = dict(good)
        bad["available_at"] = good["available_at"].astimezone(timezone.utc)
        with self.assertRaisesRegex(PilotError, "Asia/Shanghai"):
            convert_quote_rows([bad], "000012.SZ", ["2022-01-04"])
        bad = dict(good)
        bad["source_event_time"] = good["available_at"] + timedelta(seconds=1)
        with self.assertRaisesRegex(PilotError, "after its availability"):
            convert_quote_rows([bad], "000012.SZ", ["2022-01-04"])

    def test_out_of_universe_dates_and_symbol_rejected(self):
        with self.assertRaisesRegex(PilotError, "2022-2023"):
            convert_quote_rows([], "000012.SZ", ["2024-01-01"])
        with self.assertRaisesRegex(PilotError, "symbol"):
            convert_quote_rows([row("2022-01-04", 0, 100, symbol="000001.SZ")],
                               "000012.SZ", ["2022-01-04"])

    def test_missing_columns_and_invalid_flags_rejected(self):
        x = row("2022-01-04", 0, 100)
        del x["stale"]
        with self.assertRaisesRegex(PilotError, "column"):
            convert_quote_rows([x], "000012.SZ", ["2022-01-04"])
        x = row("2022-01-04", 0, 100)
        x["missing_depth"] = "false"
        with self.assertRaisesRegex(PilotError, "flags"):
            convert_quote_rows([x], "000012.SZ", ["2022-01-04"])

    def test_entire_source_chronology_checked_even_after_selected_days(self):
        raw = [row("2022-01-04", 0, 100),
               row("2022-01-05", 0, 101),
               row("2022-01-06", 20, 102),
               row("2022-01-06", 10, 102)]
        with self.assertRaisesRegex(PilotError, "repeated or reversed"):
            convert_quote_rows(raw, "000012.SZ", ["2022-01-04", "2022-01-05"])

    def test_boolean_quality_flags_reject_numeric_aliases(self):
        r = row("2022-01-04", 0, 100)
        r["stale"] = 0
        with self.assertRaisesRegex(PilotError, "flags"):
            convert_quote_rows([r], "000012.SZ", ["2022-01-04"])

    def test_selected_dates_do_not_hide_source_rows(self):
        data = [row("2022-01-04", 0, 100),
                row("2022-01-05", 0, 101),
                row("2022-01-06", 0, 102)]
        obs, qc = convert_quote_rows(data, "000012.SZ", ["2022-01-04"])
        self.assertEqual(qc["source_rows_seen"], 3)
        self.assertEqual(len(obs), 1)
        self.assertEqual(qc["selected_rows_by_date"], {"2022-01-04": 1})


if __name__ == "__main__":
    unittest.main()

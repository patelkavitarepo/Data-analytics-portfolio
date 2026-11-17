"""Synthetic tests for D010 snapshot spread / displayed-book imbalance.

These tests do not import scikit-learn or read a vendor dataset.
"""
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from microstructure.liquidity_features import (
    snapshot_features, make_feature_rows, SOURCE_FIELDS, REQUIRED_FEATURE_FIELDS
)

TZ = timezone(timedelta(hours=8))


def source_quote(*, day="2022-01-11", clock="13:00:00", symbol="000012.SZ",
                 volume_bid=20, volume_ask=10):
    now = datetime.fromisoformat(day+"T"+clock).replace(tzinfo=TZ)
    row = {
        "symbol":symbol, "available_at":now,
        "source_event_time":now-timedelta(seconds=1),
        "stale":False, "missing_depth":False
    }
    for level in range(1,6):
        row[f"bid_price_{level}"] = Decimal("99.99")-Decimal(level-1)*Decimal("0.01")
        row[f"ask_price_{level}"] = Decimal("100.01")+Decimal(level-1)*Decimal("0.01")
        row[f"bid_volume_{level}"] = volume_bid
        row[f"ask_volume_{level}"] = volume_ask
    return row


class LiquidityFeatureTests(unittest.TestCase):
    def test_expected_three_feature_values(self):
        row = source_quote()
        spread, best, depth = snapshot_features(row)
        self.assertAlmostEqual(spread,2.0,places=8)
        self.assertAlmostEqual(best,1/3,places=10)
        self.assertAlmostEqual(depth,1/3,places=10)

    def test_feature_is_current_only(self):
        a=source_quote()
        b=source_quote(clock="13:00:15",volume_bid=1,volume_ask=300)
        first,_=make_feature_rows([a,b],"000012.SZ",["2022-01-11"])
        b["bid_volume_1"]=999999
        b["ask_price_2"]=Decimal("200")
        second,_=make_feature_rows([a,b],"000012.SZ",["2022-01-11"])
        self.assertEqual(first[0],second[0])
        self.assertNotEqual(first[1],second[1])

    def test_fail_closed_for_quality_and_session(self):
        for key,val in (("stale",True),("missing_depth",True),
                        ("source_event_time",None)):
            with self.subTest(k=key):
                row=source_quote()
                row[key]=val
                self.assertIsNone(snapshot_features(row))
        self.assertIsNone(snapshot_features(source_quote(clock="14:57:00")))
        self.assertIsNone(snapshot_features(source_quote(clock="12:00:00")))

    def test_bad_future_event_time_is_rejected(self):
        row=source_quote()
        row["source_event_time"]=row["available_at"]+timedelta(milliseconds=100)
        with self.assertRaisesRegex(ValueError,"later"):
            snapshot_features(row)

    def test_price_ladder_and_cross_rejected(self):
        for key,val in (("bid_price_2",Decimal("100.00")),
                        ("ask_price_3",Decimal("99.99")),
                        ("ask_price_1",Decimal("99.99")),
                        ("bid_price_4",None),
                        ("ask_price_5",Decimal("NaN")),
                        ("bid_price_5",Decimal("-1"))):
            with self.subTest(k=key):
                row=source_quote()
                row[key]=val
                self.assertIsNone(snapshot_features(row))

    def test_price_only_source_data_is_not_sufficient_for_depth_model(self):
        row=source_quote()
        del row["bid_volume_4"]
        with self.assertRaisesRegex(ValueError,"missing mandatory"):
            snapshot_features(row)

    def test_volume_integrity_and_missing_levels(self):
        for key,val in (("bid_volume_1",-1),("ask_volume_3",None),
                        ("bid_volume_5",True),("bid_volume_2",1.5)):
            with self.subTest(k=key):
                row=source_quote()
                row[key]=val
                self.assertIsNone(snapshot_features(row))
        self.assertIsNone(snapshot_features(source_quote(volume_bid=0)))
        self.assertIsNone(snapshot_features(source_quote(volume_ask=0)))

    def test_zero_best_side_rejected_and_source_price_gap_bps_clipped(self):
        row=source_quote()
        row["bid_volume_1"]=row["ask_volume_1"]=0
        self.assertIsNone(snapshot_features(row))
        row=source_quote()
        for level in range(1,6):
            row[f"ask_price_{level}"] += Decimal("5")
        self.assertEqual(snapshot_features(row)[0],100.0)

    def test_source_order_still_aligned_with_label_row_indices(self):
        rows=[source_quote(),source_quote(clock="13:00:15")]
        rows[1]["stale"]=True
        features,counts=make_feature_rows(rows,"000012.SZ",["2022-01-11"])
        self.assertEqual(len(features),2)
        self.assertIsNotNone(features[0])
        self.assertIsNone(features[1])
        self.assertEqual(counts,{"accepted":1,"not_usable":1})

    def test_prevent_out_of_split_stock_and_date(self):
        with self.assertRaisesRegex(ValueError,"stock/date"):
            make_feature_rows([source_quote(symbol="000099.SZ")],
                              "000012.SZ",["2022-01-11"])
        with self.assertRaisesRegex(ValueError,"stock/date"):
            make_feature_rows([source_quote(day="2022-02-22")],
                              "000012.SZ",["2022-01-11"])

    def test_source_field_names_registered(self):
        self.assertEqual(len(SOURCE_FIELDS),20)
        self.assertEqual(len(REQUIRED_FEATURE_FIELDS),24)
        self.assertIn("bid_volume_5",REQUIRED_FEATURE_FIELDS)
        self.assertIn("ask_price_5",REQUIRED_FEATURE_FIELDS)


if __name__=="__main__":
    unittest.main()

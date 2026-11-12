"""D009 source-blind chronological manifest and baseline tests."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from microstructure.chronological_baselines import (
    make_examples, choose_training_majority, summarize_validation,
    continuous_phase, _confusion, K
)
from microstructure.stockday_labels import Quote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "d009_metadata_only", ROOT/"research"/"freeze_chronological_dates_once.py"
)
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)
TZ=timezone(timedelta(hours=8))


def quote(day, clock, mid=100, *, stock="000012.SZ", stale=False):
    stamp=datetime.fromisoformat(day+"T"+clock).replace(tzinfo=TZ)
    midpoint=Decimal(str(mid))
    return Quote(stock,day,stamp,midpoint-Decimal("0.01"),
                 midpoint+Decimal("0.01"),stale,False)


def five_sessions():
    dates=["2022-01-04","2022-01-05"]
    source=[]
    for day in dates:
        for phase in ("09:30:00","13:00:00"):
            start=datetime.fromisoformat(day+"T"+phase)
            for i in range(20):
                t=(start+timedelta(seconds=15*i)).time().isoformat()
                source.append(quote(day,t,Decimal("100")+Decimal(i)/100))
        source.append(quote(day,"14:57:00",150))  # auction quote excluded
    return source


class ChronologicalManifestTests(unittest.TestCase):
    def inventory(self):
        from datetime import date
        import datetime as dt
        start=date(2022,1,4)
        # No holidays needed: synthetic array is already an ordered business calendar.
        dates=[]
        day=start
        while len(dates)<60:
            if day.weekday()<5:
                dates.append(day.isoformat())
            day+=dt.timedelta(days=1)
        fixed=list(manifest.FROZEN_DAYS)
        dates=fixed+list(x for x in dates if x>fixed[-1])
        return {s.removesuffix(".parquet"):{d:100 for d in dates}
                for s in manifest.FROZEN_MEMBERS}

    def test_frozen_dates_deterministic_and_disjoint(self):
        out, info=manifest.select_dates(self.inventory())
        self.assertEqual([len(out[x]) for x in ("discovery","train","validation","holdout")],
                         [5,20,5,10])
        self.assertLess(out["train"][-1],out["validation"][0])
        self.assertLess(out["validation"][-1],out["holdout"][0])
        digest=manifest.canonical_manifest_hash(
            [s.removesuffix(".parquet") for s in manifest.FROZEN_MEMBERS],out
        )
        self.assertEqual(len(digest),64)
        self.assertEqual(digest,manifest.canonical_manifest_hash(
            [s.removesuffix(".parquet") for s in manifest.FROZEN_MEMBERS],out))

    def test_fewer_than_35_future_days_rejected(self):
        self.assertRaisesRegex(
            ValueError,"fewer than 35",
            manifest.select_dates,
            {k:dict(list(v.items())[:25]) for k,v in self.inventory().items()}
        )

    def test_missing_discovery_date_rejected_not_replaced(self):
        inputs=self.inventory()
        del inputs["000025.SZ"][manifest.FROZEN_DAYS[2]]
        with self.assertRaisesRegex(ValueError,"discovery dates changed"):
            manifest.select_dates(inputs)

    def test_no_new_stock_is_allowed(self):
        inputs=self.inventory()
        inputs["999999.SZ"]=dict(inputs["000012.SZ"])
        with self.assertRaisesRegex(ValueError,"stock set not frozen"):
            manifest.select_dates(inputs)


class ChronologicalBaselineTests(unittest.TestCase):
    def test_continuous_boundary_and_auction_exclusion(self):
        self.assertEqual(continuous_phase(quote("2022-01-04","11:30:00").available_at),
                         "morning")
        self.assertEqual(continuous_phase(quote("2022-01-04","14:56:59").available_at),
                         "afternoon")
        self.assertIsNone(continuous_phase(quote("2022-01-04","14:57:00").available_at))
        self.assertIsNone(continuous_phase(quote("2022-01-04","12:00:00").available_at))

    def test_no_cross_day_lunch_auction_or_invalid_quote(self):
        source=five_sessions()
        outcome=make_examples(source)
        self.assertEqual(len(source),len(outcome))
        for row in outcome:
            if row.target is not None:
                original=source[row.row_index]
                for j in row.target_indices:
                    self.assertEqual(source[j].trading_date,original.trading_date)
                    self.assertEqual(continuous_phase(source[j].available_at),
                                     continuous_phase(original.available_at))
            if source[row.row_index].available_at.time().isoformat()=="14:57:00":
                self.assertEqual(row.exclusion,"outside_continuous_auction")
        self.assertTrue(all(x.target is None for x in outcome if x.exclusion is not None))

    def test_b1_uses_past_five_not_future_or_future_labels(self):
        source=five_sessions()
        a=make_examples(source)
        # Changing a later price does not change B1 for earlier row 7
        changed=list(source)
        later=changed[9]
        changed[9]=Quote(later.symbol,later.trading_date,later.available_at,
                         Decimal("1000"),Decimal("1000.02"),False,False)
        b=make_examples(changed)
        self.assertEqual(a[7].b1_prediction,b[7].b1_prediction)
        self.assertIsNone(a[4].b1_prediction)
        self.assertIsNotNone(a[5].b1_prediction)
        self.assertEqual(a[-1].exclusion,"outside_continuous_auction")

    def test_abstention_and_coverage_reporting(self):
        outcomes=make_examples(five_sessions())
        majority,counts=choose_training_majority(outcomes)
        self.assertIn(majority,(1,2,3))
        result=summarize_validation(outcomes,majority)
        self.assertGreater(result["eligible_targets"],result["b1_covered_targets"])
        self.assertEqual(result["B0_on_B1_covered"]["n"],result["B1_on_same_covered"]["n"])
        self.assertEqual(sum(result["B0_all_eligible"]["true_support"].values()),
                         result["eligible_targets"])
        self.assertEqual(len(result["by_stock_date"]),2)

    def test_training_tie_priority_never_validation_tuned(self):
        from microstructure.chronological_baselines import Example
        cases=[Example(i,"S","2022-01-04",c,None,None,())
               for i,c in enumerate([1,2,3])]
        selected,c=choose_training_majority(cases)
        self.assertEqual(selected,2)
        cases=[Example(i,"S","2022-01-04",c,None,None,())
               for i,c in enumerate([1,1,3,3])]
        self.assertEqual(choose_training_majority(cases)[0],1)

    def test_three_class_metric_includes_unsupported_class(self):
        from microstructure.chronological_baselines import Example
        rows=[Example(i,"S","2022-01-04",2,2,None,()) for i in range(4)]
        report=_confusion(rows,lambda x:x.b1_prediction)
        self.assertEqual(report["accuracy"],1)
        self.assertAlmostEqual(report["macro_f1_three_class"],1/3)
        self.assertAlmostEqual(report["balanced_accuracy_three_class"],1/3)
        self.assertEqual(report["true_support"],{"1":0,"2":4,"3":0})

    def test_invalid_flags_segment_break_lagged_feature(self):
        rows=[quote("2022-01-04",
             (datetime(2022,1,4,13,0)+timedelta(seconds=i*15)).time().isoformat(),
             100+i*0.1,stale=(i==8)) for i in range(25)]
        examples=make_examples(rows)
        self.assertEqual(examples[8].exclusion,"invalid_or_stale_quote")
        for i in range(9,14):
            self.assertIsNone(examples[i].b1_prediction)
        self.assertIsNotNone(examples[14].b1_prediction)

    def test_source_order_rejected(self):
        rows=[quote("2022-01-04","13:00:15"),quote("2022-01-04","13:00:00")]
        with self.assertRaisesRegex(ValueError,"unsorted"):
            make_examples(rows)


if __name__=="__main__":
    unittest.main()

"""Synthetic-only D006 sensitivity tests. No vendor data or network reads."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
import unittest

from microstructure.stockday_labels import Quote, labels_from_quotes
from microstructure.quote_quality_sensitivity import (
    _compare, _counts, _transform_flags, FLAG_MODES, GAP_LIMITS,
    FROZEN_PRIMARY, source_quality, sensitivity_panel,
)

DATES = ("2022-01-04","2022-01-05","2022-01-06",
         "2022-01-07","2022-01-10")
TZ = timezone(timedelta(hours=8))


def make_days():
    """One quote/day with missing, stale, crossed, short and long gaps."""
    data=[]
    for day in DATES:
        moment=datetime.fromisoformat(day+"T09:30:00").replace(tzinfo=TZ)
        seconds=0
        for i in range(20):
            seconds += (30 if i == 3 else 45 if i == 10 else 15)
            midpoint=Decimal("100") + Decimal(i)/Decimal("200")
            bid=midpoint-Decimal("0.01")
            ask=midpoint+Decimal("0.01")
            if i == 18:
                ask=bid  # hard-invalid should NEVER be admitted
            data.append(Quote("000012.SZ",day,moment+timedelta(seconds=seconds),
                              bid,ask,stale=i==8,missing_depth=i==15))
    return tuple(data)


class QuoteQualitySensitivityTests(unittest.TestCase):
    def test_compare_eligibility_and_class_changes(self):
        rows=make_days()
        baseline=labels_from_quotes(rows, 5, max_gap_seconds=30)
        more=labels_from_quotes(rows, 5, max_gap_seconds=60)
        diff=_compare(baseline, more)
        self.assertGreaterEqual(diff["newly_eligible_from_excluded"],0)
        self.assertEqual(diff["newly_excluded_from_eligible"],0)
        self.assertEqual(sum(_counts(baseline)[k] for k in ("up","down","stationary","unlabelled")),len(rows))

    def test_stale_and_missing_flags_counterfactual_without_mutating_source(self):
        original=make_days()
        both=_transform_flags(original, "FSD")
        self.assertEqual(original[8].stale, True)
        self.assertEqual(both[8].stale, False)
        self.assertEqual(original[15].missing_depth, True)
        self.assertEqual(both[15].missing_depth, False)
        self.assertEqual(original[18].ask,original[18].bid)
        self.assertEqual(both[18].ask,both[18].bid)
        for mode in FLAG_MODES:
            transformed=_transform_flags(original,mode)
            self.assertEqual(len(transformed),len(original))

    def test_cross_tab_is_mutually_exclusive_and_gaps_by_source_day(self):
        data=make_days()
        quality=source_quality(data)
        self.assertEqual(sum(quality["exclusive_quality_crosstab"].values()),len(data))
        self.assertEqual(quality["adjacent_same_stock_day_gap_gt_seconds"]["15"],10)
        self.assertEqual(quality["adjacent_same_stock_day_gap_gt_seconds"]["30"],5)
        self.assertEqual(quality["adjacent_same_stock_day_gap_gt_seconds"]["60"],0)
        self.assertEqual(len(quality["daily_source_quality"]),5)

    def test_frozen_baseline_unchanged_and_eight_oracles(self):
        source=make_days()
        c=_counts(labels_from_quotes(source,5,max_gap_seconds=30))
        frozen=(c["all"],c["up"],c["stationary"],c["down"],c["unlabelled"])
        with patch.dict(FROZEN_PRIMARY,{"000012.SZ":frozen}):
            output=sensitivity_panel(source,"000012.SZ",DATES)
        self.assertEqual(set(output["scenarios"]),set(GAP_LIMITS)|set(FLAG_MODES))
        self.assertTrue(output["all_eight_modes_oracle_verified"])
        self.assertEqual(output["total_primary_oracle_checks"],len(source)*8)
        self.assertEqual(output["scenarios"]["F0"]["pooled_counts"],
                         output["scenarios"]["G30"]["pooled_counts"])
        for key in output["scenarios"]:
            self.assertEqual(output["scenarios"][key]["oracle_disagreements"],0)
            self.assertEqual(output["scenarios"][key]["pooled_counts"]["all"],len(source))
            self.assertEqual(len(output["scenarios"][key]["per_day"]),5)
        self.assertEqual(output["scenarios"]["FSD"]["pooled_counts"]["unlabelled"] >= 5,True)

    def test_reject_when_frozen_primary_does_not_match_source(self):
        with self.assertRaisesRegex(AssertionError,"frozen reference"):
            sensitivity_panel(make_days(),"000012.SZ",DATES)

    def test_reject_unregistered_source_and_dates(self):
        with self.assertRaisesRegex(ValueError,"preregistered"):
            sensitivity_panel(make_days(),"999999.SZ",DATES)
        with self.assertRaisesRegex(ValueError,"five distinct"):
            sensitivity_panel(make_days(),"000012.SZ",DATES[:2])

if __name__=="__main__":
    unittest.main()

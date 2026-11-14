"""D012 synthetic-only chronological date/alert/calibration isolation tests."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
from collections import Counter
import importlib.util
import json
import sys
import tempfile
import unittest

from microstructure.selective_alerts import (
    source_past5_coverage,get_direction_score,frozen_high_quantile,
    cutoff_by_stock,emit_alert,alert_report
)
from microstructure.stockday_labels import Quote
from microstructure.chronological_baselines import Example

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
spec=importlib.util.spec_from_file_location(
    "d012_fresh_dates",ROOT/"research"/"freeze_fresh_selective_dates_once.py"
)
dates_mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(dates_mod)
TZ=timezone(timedelta(hours=8))
STOCKS=("000012.SZ","000025.SZ","000031.SZ")


def sample_quote(day,clock,*,stock="000012.SZ",stale=False):
    timestamp=datetime.fromisoformat(day+"T"+clock).replace(tzinfo=TZ)
    return Quote(stock,day,timestamp,Decimal("99.99"),Decimal("100.01"),stale,False)


class DateSelectionTests(unittest.TestCase):
    def test_new_dates_selected_after_legacy_holdout_and_no_replacement(self):
        from datetime import date
        begin=date(2022,3,8)
        days=[]
        for offset in range(120):
            d=begin+timedelta(days=offset)
            if d.weekday()<5: days.append(d.isoformat())
        inventories={s:{d:100 for d in days} for s in STOCKS}
        selection,detail=dates_mod.fresh_selection(inventories)
        self.assertEqual([len(selection[k]) for k,n in dates_mod.STUDY_PARTS],[20,10,5,10])
        self.assertTrue(selection["fit"][0]>"2022-03-07")
        self.assertLess(selection["fit"][-1],selection["calibration"][0])
        self.assertLess(selection["calibration"][-1],selection["confirmation"][0])
        self.assertLess(selection["confirmation"][-1],selection["sealed_final"][0])
        digest=dates_mod.fresh_sha(STOCKS,selection)
        self.assertEqual(len(digest),64)
        self.assertEqual(digest,dates_mod.fresh_sha(STOCKS,selection))
        inventories["000025.SZ"].pop(selection["calibration"][0])
        altered,_=dates_mod.fresh_selection(inventories)
        self.assertNotEqual(digest,dates_mod.fresh_sha(STOCKS,altered))

    def test_insufficient_dates_and_wrong_stock_fail(self):
        inventories={s:{"2022-03-08":1,"2022-03-09":1} for s in STOCKS}
        with self.assertRaisesRegex(ValueError,"at least 45"):
            dates_mod.fresh_selection(inventories)
        inventories["000999.SZ"]=inventories.pop("000025.SZ")
        with self.assertRaisesRegex(ValueError,"stock"):
            dates_mod.fresh_selection(inventories)

    def test_date_hash_rejects_partition_change(self):
        candidate={
            "fit":["2022-03-08"]*20,
            "calibration":["2022-03-09"]*10,
            "confirmation":["2022-03-10"]*5,
            "sealed_final":["2022-03-11"]*10
        }
        self.assertEqual(len(dates_mod.fresh_sha(STOCKS,candidate)),64)
        candidate["fit"].pop()
        with self.assertRaisesRegex(ValueError,"partition sizes"):
            dates_mod.fresh_sha(STOCKS,candidate)


class SelectiveAlertsTests(unittest.TestCase):
    def test_past_only_gating_does_not_allow_lunch_overnight_or_gaps(self):
        first=datetime(2022,3,10,11,28,30)
        points=[sample_quote("2022-03-10",(first+timedelta(seconds=i*15)).time().isoformat())
                for i in range(7)]
        afternoon=datetime(2022,3,10,13,0,0)
        points += [sample_quote("2022-03-10",(afternoon+timedelta(seconds=i*15)).time().isoformat())
                   for i in range(7)]
        readiness=source_past5_coverage(points)
        self.assertEqual(readiness[:7],(False,False,False,False,False,True,True))
        self.assertEqual(readiness[7:],(False,False,False,False,False,True,True))
        changed=list(points)
        # A future price mutation cannot change earlier past-only readiness
        changed[9]=Quote(changed[9].symbol,changed[9].trading_date,
                         changed[9].available_at,Decimal("1"),Decimal("1.5"),False,False)
        self.assertEqual(readiness[:9],source_past5_coverage(changed)[:9])

    def test_nontrading_break_and_invalid_quote_reset_lag(self):
        start=datetime(2022,3,10,13,0)
        rows=[sample_quote("2022-03-10",(start+timedelta(seconds=i*15)).time().isoformat(),
                           stale=(i==6)) for i in range(13)]
        ready=source_past5_coverage(rows)
        self.assertTrue(ready[5])
        self.assertFalse(ready[6])
        self.assertTrue(ready[12])

    def test_current_only_probabilities_and_tie_sign(self):
        score,side=get_direction_score((0.4,0.2,0.4),(1,2,3))
        self.assertEqual(side,1)
        self.assertGreater(score,1.9)
        for p in ((-0.1,1,0.1),(0.5,0.5,0.3),(float("nan"),0.5,0.5)):
            with self.subTest(p=p),self.assertRaises(ValueError):
                get_direction_score(p,(1,2,3))
        with self.assertRaisesRegex(ValueError,"order"):
            get_direction_score((0.3,0.4,0.3),(2,1,3))

    def test_exact_2percent_cutoff_and_no_tie_mass_alerts(self):
        s=list(range(100))
        x=frozen_high_quantile(s)
        self.assertEqual(x,98.0)
        self.assertEqual(sum(v>x for v in s),1)
        ties=[1.0]*100
        self.assertEqual(frozen_high_quantile(ties),1.0)
        self.assertEqual(sum(v>frozen_high_quantile(ties) for v in ties),0)
        self.assertEqual(emit_alert(4,1,3),1)
        self.assertIsNone(emit_alert(3,3,3))

    def test_calibration_without_labels_and_fixed_stock_set(self):
        refs=[(s,True) for s in STOCKS for _ in range(100)]
        probs=[]
        for stock in STOCKS:
            probs.extend([(0.02+i/10000,0.95-i/10000,0.03) for i in range(100)])
        cuts,counts=cutoff_by_stock(refs,probs,(1,2,3))
        self.assertEqual(counts,{s:100 for s in STOCKS})
        self.assertEqual(set(cuts),set(STOCKS))
        only_two=[r for r in refs if r[0]!="000031.SZ"]
        with self.assertRaisesRegex(ValueError,"three stocks"):
            cutoff_by_stock(only_two,probs[:len(only_two)],(1,2,3))

    def test_false_alert_metrics_no_alert_is_not_claimed_stationary(self):
        labels=[1,2,3,2]
        examples=[Example(i,"S","2022-04-01",target,2,None,())
                  for i,target in enumerate(labels)]
        report=alert_report(examples,[1,1,3,None],2)
        self.assertEqual(report["directional_alerts"],3)
        self.assertEqual(report["true_direction_alerts"],2)
        self.assertEqual(report["false_direction_alerts"],1)
        self.assertEqual(report["no_alert_count"],1)
        self.assertEqual(report["directional_precision"],2/3)
        self.assertIn("abstention",report["note"])

    def test_identical_index_across_stock_date_does_not_collide(self):
        e=[Example(0,"S1","2022-04-01",1,1,None,()),
           Example(0,"S2","2022-04-01",3,3,None,())]
        r=alert_report(e,[1,3],2)
        self.assertEqual(r["true_direction_alerts"],2)


if __name__=="__main__":
    unittest.main()

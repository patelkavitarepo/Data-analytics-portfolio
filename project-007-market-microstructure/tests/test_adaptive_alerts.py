"""D014 synthetic-only chronology, rolling-label-blind and source-date tests.

No provider source is fetched, no scikit-learn/pyarrow required.
"""
from datetime import date,timedelta
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))

from microstructure.adaptive_alerts import (
    ORIGINAL_CUTOFFS,validate_calendar,rolling_cutoff_before_day,
    daily_threshold_replay,labelled_alert_metrics,cluster_bootstrap_day_sums
)
from freeze_adaptive_dates_once import select_dates,checksum,STOCKS


def chosen_dates():
    start=date(2022,5,17)
    dates=[]
    for i in range(70):
        d=start+timedelta(days=i)
        if d.weekday()<5:
            dates.append(d.isoformat())
    return dates[:40]


class AdaptiveCalendarTests(unittest.TestCase):
    def test_fresh_after_D012_and_no_duplicate_dates(self):
        d=chosen_dates()
        self.assertEqual(len(d),40)
        validate_calendar(d[:20],d[20:30],d[30:40])
        with self.assertRaises(ValueError):
            validate_calendar(d[:20],d[20:30],d[29:39])
        with self.assertRaises(ValueError):
            validate_calendar(["2022-05-16"]+d[1:20],d[20:30],d[30:40])

    def test_timestamp_only_selection_and_hash_changes_on_modified_calendar(self):
        calendar=chosen_dates()+["2022-07-30"]
        obs={s:{d:1000 for d in calendar} for s in STOCKS}
        frozen,counts=select_dates(obs)
        self.assertEqual(frozen["warmup"],calendar[:20])
        self.assertEqual(frozen["confirmation"],calendar[20:30])
        self.assertEqual(frozen["sealed_final"],calendar[30:40])
        h=checksum(frozen)
        self.assertEqual(len(h),64)
        changed={k:list(v) for k,v in frozen.items()}
        changed["confirmation"][0]="2022-05-16"
        with self.assertRaises(ValueError):
            checksum(changed)
        obs[STOCKS[0]].pop(calendar[0])
        altered,_=select_dates(obs)
        self.assertNotEqual(checksum(altered),h)

    def test_stock_member_composition_locked(self):
        obs={s:{d:1 for d in chosen_dates()} for s in STOCKS[:2]}
        with self.assertRaises(ValueError):
            select_dates(obs)


class AdaptiveThresholdTests(unittest.TestCase):
    def test_rolling_past_ten_days_no_current_day_information(self):
        days=chosen_dates()
        history=[(d,(1.0,)*5) for d in days[:20]]
        self.assertEqual(rolling_cutoff_before_day(history,days[20]),1.0)
        with self.assertRaisesRegex(ValueError,"current/future"):
            rolling_cutoff_before_day(history[1:]+[(days[20],(999.0,))],days[20])
        with self.assertRaisesRegex(ValueError,"ten"):
            rolling_cutoff_before_day(history[:9],days[20])
        history[-1]=(days[19],())
        with self.assertRaisesRegex(ValueError,"each day"):
            rolling_cutoff_before_day(history,days[20])

    def test_day_close_updates_only_next_day_and_ties_abstain(self):
        days=chosen_dates()
        scored={d:((1.0,1),)*5 for d in days[:20]}
        for i,d in enumerate(days[20:30]):
            scored[d]=((9.0 if i==0 else 8.0,3),)
        replay=daily_threshold_replay(days[:20],days[20:30],scored,2.0)
        self.assertEqual(replay[days[20]]["rolling_cutoff"],1.0)
        self.assertEqual(replay[days[20]]["rolling"],(3,))
        self.assertEqual(replay[days[20]]["static"],(3,))
        self.assertEqual(replay[days[21]]["rolling_cutoff"],9.0)
        self.assertEqual(replay[days[21]]["rolling"],(None,))
        self.assertEqual(replay[days[21]]["static"],(3,))
        scored2=dict(scored)
        scored2[days[29]]=((100000.0,1),)
        replay2=daily_threshold_replay(days[:20],days[20:30],scored2,2.0)
        self.assertEqual(replay[days[20]],replay2[days[20]])
        self.assertEqual(replay[days[21]],replay2[days[21]])

    def test_sealed_score_cannot_enter_replay(self):
        dates=chosen_dates()
        scores={d:((1.0,1),) for d in dates}
        with self.assertRaisesRegex(ValueError,"sealed"):
            daily_threshold_replay(dates[:20],dates[20:30],scores,2.0)
        with self.assertRaisesRegex(ValueError,"missing"):
            daily_threshold_replay(dates[:20],dates[20:30],
                                  {d:scores[d] for d in dates[:29]},2.0)

    def test_original_frozen_stock_cutoffs_are_not_reestimated(self):
        self.assertEqual(set(ORIGINAL_CUTOFFS),{"W_BALANCED","W_UNWEIGHTED"})
        self.assertEqual(set(ORIGINAL_CUTOFFS["W_BALANCED"]),set(STOCKS))
        self.assertAlmostEqual(ORIGINAL_CUTOFFS["W_BALANCED"]["000012.SZ"],1.8813401620922308)


class AlertsAndBootstrapTests(unittest.TestCase):
    def test_no_alert_is_abstention_and_cost_is_not_trading_return(self):
        r=labelled_alert_metrics([1,2,3,1],[1,1,None,3])
        self.assertEqual((r["alerts"],r["correct"],r["false"],r["abstain"]), (3,1,2,1))
        self.assertEqual(r["utility_units"],-7)
        self.assertEqual(r["up_recall"],.5)
        self.assertEqual(r["down_recall"],0)
        self.assertIsNone(labelled_alert_metrics([2,2],[None,None])["precision"])
        with self.assertRaises(ValueError):
            labelled_alert_metrics([1],[2])

    def test_cluster_bootstrap_is_deterministic_and_not_per_quote(self):
        days=[(1,4,100)]*5+[(2,0,100)]*5
        a=cluster_bootstrap_day_sums(days)
        b=cluster_bootstrap_day_sums(days)
        self.assertEqual(a,b)
        self.assertEqual(a["replications"],2000)
        self.assertLess(a["utility_units_q025"],a["utility_units_q975"])
        with self.assertRaises(ValueError):
            cluster_bootstrap_day_sums(days[:9])


if __name__=="__main__":
    unittest.main()

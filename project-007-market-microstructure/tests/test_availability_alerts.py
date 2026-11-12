"""D015 pure synthetic tests: source completeness, no peeking, sealed periods."""
from datetime import date,timedelta
import unittest
from microstructure.availability_alerts import (
    freeze_calendar,historical_gate,replay,aggregate_states,matched_outcomes,
    POLICIES,STATUSES
)

def days():
    d=date(2022,7,13);out=[]
    for i in range(90):
        x=d+timedelta(days=i)
        if x.weekday()<5:out.append(x.isoformat())
    return out[:40]

def score_day(v=1.0,n=10):
    return tuple((v,1) for i in range(n))

class AvailabilityTests(unittest.TestCase):
    def test_strict_new_calendar_and_sealed_rejection(self):
        d=days()
        freeze_calendar(d[:20],d[20:30],d[30:])
        with self.assertRaises(ValueError):
            freeze_calendar(["2022-07-12"]+d[1:20],d[20:30],d[30:])
        with self.assertRaises(ValueError):
            freeze_calendar(d[:20],d[20:30],d[29:39])
    def test_health_uses_all_ten_prior_days_not_ten_good_days(self):
        d=days()
        history=[(day,score_day(),10) for day in d[:20]]
        history[13]=(d[13],(None,)*6+score_day(n=4),10)
        healthy,cutoff,meta=historical_gate(history,d[20])
        self.assertFalse(healthy)
        self.assertIsNone(cutoff)
        self.assertEqual(meta["minimum_past_coverage"],.4)
        history[13]=(d[13],(None,)*5+score_day(n=5),10)
        healthy,cutoff,meta=historical_gate(history,d[20])
        self.assertTrue(healthy)
        self.assertEqual(cutoff,1.0)
        with self.assertRaises(ValueError):
            historical_gate(history[1:]+[(d[20],score_day(),10)],d[20])
    def test_states_include_every_source_row_and_precedence(self):
        d=days()
        scores={day:score_day() for day in d[:30]}
        scores[d[15]]=(None,)*10
        scores[d[20]]=(None,(99.0,1),(0.0,3)) + score_day(n=7)
        result=replay(d[:20],d[20:30],d[30:],scores,"000012.SZ","W_BALANCED")
        today=result[d[20]]
        self.assertEqual(today["STATIC_BASELINE"]["statuses"][:3],
                         ("DATA_UNAVAILABLE_CURRENT","ALERT_UP","NO_SIGNAL"))
        self.assertEqual(today["STATIC_HEALTH"]["statuses"][:3],
                         ("DATA_UNAVAILABLE_CURRENT","DATA_UNAVAILABLE_HISTORY",
                          "DATA_UNAVAILABLE_HISTORY"))
        self.assertEqual(today["ROLLING_HEALTH"]["statuses"][:3],
                         ("DATA_UNAVAILABLE_CURRENT","DATA_UNAVAILABLE_HISTORY",
                          "DATA_UNAVAILABLE_HISTORY"))
        counts=aggregate_states(today["STATIC_HEALTH"]["statuses"])
        self.assertEqual(counts["source_n"],10)
        self.assertEqual(counts["capable"],0)
        self.assertIsNone(counts["alert_rate_capable"])
        scores[d[30]]=score_day()
        with self.assertRaisesRegex(ValueError,"sealed"):
            replay(d[:20],d[20:30],d[30:],scores,"000012.SZ","W_BALANCED")
    def test_no_current_day_recalibration(self):
        d=days()
        scores={day:score_day() for day in d[:30]}
        a=replay(d[:20],d[20:30],d[30:],scores,"000012.SZ","W_BALANCED")
        scores[d[29]]=score_day(1e8)
        b=replay(d[:20],d[20:30],d[30:],scores,"000012.SZ","W_BALANCED")
        self.assertEqual(a[d[20]],b[d[20]])
        self.assertEqual(a[d[29]]["ROLLING_HEALTH"]["cutoff"],
                         b[d[29]]["ROLLING_HEALTH"]["cutoff"])
    def test_missing_current_has_priority_and_label_blind_replay(self):
        d=days()
        scores={day:score_day() for day in d[:30]}
        scores[d[20]]=(None,)*10
        result=replay(d[:20],d[20:30],d[30:],scores,"000025.SZ","W_UNWEIGHTED")
        for p in POLICIES:
            self.assertEqual(set(result[d[20]][p]["statuses"]),
                             {"DATA_UNAVAILABLE_CURRENT"})
    def test_future_label_is_not_a_stationary_imputation(self):
        result=matched_outcomes(
            ["ALERT_UP","ALERT_DOWN","DATA_UNAVAILABLE_HISTORY",
             "DATA_UNAVAILABLE_CURRENT","NO_SIGNAL"],
            [1,2,3,None,1])
        self.assertEqual((result["matched_n"],result["correct"],result["wrong"]),(4,1,1))
        self.assertEqual(result["directional_movement_unavailable"],1)
        self.assertEqual(result["future_label_unknown_n"],1)
        self.assertEqual(result["hypothetical_4to1_units"],-3)
        with self.assertRaises(ValueError):
            matched_outcomes(["NO_SIGNAL"],[4])
    def test_ties_never_alert(self):
        d=days()
        scores={day:score_day() for day in d[:30]}
        result=replay(d[:20],d[20:30],d[30:],scores,"000012.SZ","W_BALANCED")
        self.assertEqual(result[d[20]]["ROLLING_HEALTH"]["statuses"],
                         ("NO_SIGNAL",)*10)
        self.assertEqual(sum(aggregate_states(result[d[20]][p]["statuses"])["counts"].values()
                             for p in POLICIES),30)

if __name__=="__main__":unittest.main()

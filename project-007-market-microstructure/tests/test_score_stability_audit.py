"""D013: no-data-leak regression tests, using exclusively synthetic quotes."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
from microstructure.score_stability import (
    higher_quantile,distribution,make_rows,score_distribution,feature_distribution,scope_groups
)
from freeze_fresh_selective_dates_once import load_fresh_manifest
spec=importlib.util.spec_from_file_location(
    "d013_runner",ROOT/"research"/"run_score_stability_audit_once.py"
)
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
DATES=load_fresh_manifest()["dates"]
TZ=timezone(timedelta(hours=8))


def quote(day,number=0):
    stamp=datetime.fromisoformat(day+"T13:00:15").replace(tzinfo=TZ)+timedelta(seconds=15*number)
    r={"symbol":"000012.SZ","available_at":stamp,
       "source_event_time":stamp-timedelta(seconds=1),
       "stale":False,"missing_depth":False}
    for i in range(1,6):
        r[f"bid_price_{i}"]=Decimal("99.99")-Decimal(i-1)/100
        r[f"ask_price_{i}"]=Decimal("100.01")+Decimal(i-1)/100
        r[f"bid_volume_{i}"]=10
        r[f"ask_volume_{i}"]=10
    return r


class AuditSummaryTests(unittest.TestCase):
    def test_strict_frozen_cutoff_never_promoted(self):
        data=make_rows("000012.SZ",["2022-04-21"]*4,
                       [(1.0,0.0,0.0)]*4,[True]*4,
                       ["afternoon"]*4,[True,False,True,False])
        for row,value in zip(data,[1.0,2.0,3.0,4.0]):
            row["score"]=value
        raw=score_distribution(data,2.0)
        historical=score_distribution(data,2.0,matched=True)
        self.assertEqual(raw["denominator"],4)
        self.assertEqual(raw["strict_exceedances"],2)
        self.assertEqual(historical["denominator"],2)
        self.assertEqual(historical["strict_exceedances"],1)
        self.assertEqual(raw["exceedance_rate"],0.5)
        self.assertEqual(historical["exceedance_rate"],0.5)
        self.assertEqual(raw["frozen_cutoff"],2.0)
        self.assertEqual(raw["distribution"]["median"],3.0)

    def test_future_eligibility_cannot_change_decision_gate(self):
        with self.assertRaisesRegex(ValueError,"past and book"):
            make_rows("000012.SZ",["2022-04-21"],[None],[False],
                      ["afternoon"],[True])
        a=make_rows("000012.SZ",["2022-04-21"],
                    [(2.0,0.0,0.0)],[True],["morning"],[False])
        self.assertTrue(a[0]["ready"])
        self.assertFalse(a[0]["matched"])
        a[0]["score"]=0.12
        self.assertEqual(score_distribution(a,.1)["strict_exceedances"],1)
        self.assertEqual(score_distribution(a,.1,matched=True)["denominator"],0)

    def test_higher_quantile_ties_and_features(self):
        self.assertEqual(higher_quantile([1,1,1,10],.98),10)
        self.assertIsNone(higher_quantile([],.98))
        rows=make_rows("000012.SZ",["2022-04-21"]*2,
                      [(1.5,.2,-.2),None],[True,False],
                      ["morning",None])
        stats=feature_distribution(rows)
        self.assertEqual(stats["eligible_rows"],1)
        self.assertEqual(stats["spread_bps"]["median"],1.5)
        self.assertEqual(len(scope_groups(rows)),5)

    def test_frozen_summary_rejects_bad_data(self):
        with self.assertRaises(ValueError):
            distribution([1.0,float("nan")])
        with self.assertRaises(ValueError):
            make_rows("000012.SZ",["2022-04-21"],[(1,0,0)],
                      [True,True],["morning"])


class FakeBatch:
    def __init__(self,raw):self.raw=raw
    schema=types.SimpleNamespace(get_field_index=lambda f:0 if f=="available_at" else -1)
    def column(self,i):
        if i!=0:raise AssertionError("only timestamp list may be used to filter rows")
        return types.SimpleNamespace(to_pylist=lambda:[r["available_at"] for r in self.raw])
    def slice(self,l,n):return FakeBatch(self.raw[l:l+n])
    def to_pylist(self):
        if any(r["available_at"].date().isoformat() in DATES["sealed_final"] for r in self.raw):
            raise AssertionError("SEALED quote converted")
        return self.raw


class AuditSourceIsolationTests(unittest.TestCase):
    def test_new_audit_reads_only_pre_final_and_never_calibration_targets(self):
        input_rows=[quote(day,i)
                    for key in ("fit","calibration","confirmation","sealed_final")
                    for day in DATES[key] for i in range(12)]
        chunks=[FakeBatch(input_rows[i:i+128]) for i in range(0,len(input_rows),128)]
        class FakeParquet:
            schema_arrow=types.SimpleNamespace(
                names=list(dict.fromkeys(runner.REQUIRED_FIELDS+runner.SOURCE_FIELDS)))
            def __init__(self,p):pass
            def iter_batches(self,**kwargs):
                for chunk in chunks:yield chunk
        pyarrow=types.ModuleType("pyarrow")
        pyarrow.__path__=[]
        parquet=types.ModuleType("pyarrow.parquet")
        parquet.ParquetFile=FakeParquet
        pyarrow.parquet=parquet
        original=runner.make_examples
        called=[]
        def gate(quotes):
            called.append(quotes[0].trading_date)
            self.assertNotIn(quotes[0].trading_date,DATES["calibration"])
            self.assertNotIn(quotes[0].trading_date,DATES["sealed_final"])
            return original(quotes)
        with patch.dict(sys.modules,{"pyarrow":pyarrow,"pyarrow.parquet":parquet}):
            with patch.object(runner,"make_examples",side_effect=gate):
                parts,train=runner.read_audit_35_only(
                    "/synthetic","000012.SZ",DATES,
                    {d:12 for k in DATES for d in DATES[k]})
        self.assertEqual(len(called),25)
        self.assertEqual(len(parts["fit"]),240)
        self.assertEqual(len(parts["calibration"]),120)
        self.assertEqual(len(parts["confirmation"]),60)
        self.assertEqual(len(train),20*7)
        self.assertEqual(sum(r["ready"] for r in parts["calibration"]),70)
        self.assertEqual(sum(r["matched"] for r in parts["confirmation"]),10)
        self.assertTrue(all(not r["matched"] for r in parts["calibration"]))
        self.assertTrue(all(r["score"] is None for r in parts["confirmation"]))

    def test_bad_sealed_boundary_rejected_before_parquet_read(self):
        bad={k:list(v) for k,v in DATES.items()}
        bad["sealed_final"][0]=bad["confirmation"][0]
        with self.assertRaisesRegex(Exception,"restricted"):
            runner.read_audit_35_only("/unused","000012.SZ",bad,{})


if __name__=="__main__":
    unittest.main()

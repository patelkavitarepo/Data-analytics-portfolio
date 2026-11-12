"""D014 one-time source reader synthetic-only 2022 date isolation tests."""
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
from freeze_fresh_selective_dates_once import load_fresh_manifest

spec=importlib.util.spec_from_file_location(
    "d014_one_time_reader",ROOT/"research"/"run_adaptive_alerts_once.py")
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ORIGINAL=load_fresh_manifest()["dates"]
TZ=timezone(timedelta(hours=8))


def future_dates():
    dates=[]
    start=date(2022,5,17)
    for i in range(70):
        x=start+timedelta(days=i)
        if x.weekday()<5:
            dates.append(x.isoformat())
    return {
        "warmup":dates[:20],
        "confirmation":dates[20:30],
        "sealed_final":dates[30:40]
    }


NEW=future_dates()


def row(day,i):
    stamp=datetime.fromisoformat(day+"T13:00:15").replace(tzinfo=TZ)+timedelta(seconds=15*i)
    r={"symbol":"000012.SZ","available_at":stamp,
       "source_event_time":stamp-timedelta(seconds=1),
       "stale":False,"missing_depth":False}
    for n in range(1,6):
        r[f"bid_price_{n}"]=Decimal("99.99")-Decimal(n-1)/100
        r[f"ask_price_{n}"]=Decimal("100.01")+Decimal(n-1)/100
        r[f"bid_volume_{n}"]=10
        r[f"ask_volume_{n}"]=10
    return r


class FakeBatch:
    schema=types.SimpleNamespace(get_field_index=lambda key: 0 if key=="available_at" else -1)
    def __init__(self,rows):self.rows=rows
    def column(self,i):
        if i!=0:raise AssertionError("unapproved column selection")
        return types.SimpleNamespace(to_pylist=lambda:[r["available_at"] for r in self.rows])
    def slice(self,l,n):
        return FakeBatch(self.rows[l:l+n])
    def to_pylist(self):
        if any(r["available_at"].date().isoformat() in NEW["sealed_final"] for r in self.rows):
            raise AssertionError("new sealed final quote row converted")
        if any(r["available_at"].date().isoformat() in ORIGINAL["sealed_final"] for r in self.rows):
            raise AssertionError("old sealed final quote row converted")
        return self.rows


class ReaderIntegrityTests(unittest.TestCase):
    def test_never_forms_warmup_target_and_does_not_convert_sealed_final(self):
        original_dates=ORIGINAL["fit"]
        new_dates=NEW["warmup"]+NEW["confirmation"]
        all_days=original_dates+new_dates+NEW["sealed_final"][:2]
        input_rows=[row(d,i) for d in all_days for i in range(12)]
        chunks=[FakeBatch(input_rows[i:i+128]) for i in range(0,len(input_rows),128)]
        class FakeParquet:
            schema_arrow=types.SimpleNamespace(
                names=list(dict.fromkeys(runner.REQUIRED_FIELDS+runner.SOURCE_FIELDS)))
            def __init__(self,path):pass
            def iter_batches(self,**kwargs):
                for chunk in chunks:yield chunk
        pyarrow=types.ModuleType("pyarrow")
        pyarrow.__path__=[]
        parquet=types.ModuleType("pyarrow.parquet")
        parquet.ParquetFile=FakeParquet
        pyarrow.parquet=parquet
        called=[]
        original_fn=runner.make_examples
        def guarded(quotes):
            d=quotes[0].trading_date
            called.append(d)
            self.assertNotIn(d,NEW["warmup"])
            self.assertNotIn(d,NEW["sealed_final"])
            self.assertNotIn(d,ORIGINAL["sealed_final"])
            return original_fn(quotes)
        with patch.dict(sys.modules,{"pyarrow":pyarrow,"pyarrow.parquet":parquet}):
            with patch.object(runner,"make_examples",side_effect=guarded):
                fit,other,qc=runner._read_authorized_days(
                    "/synthetic","000012.SZ",ORIGINAL,NEW,
                    {d:12 for d in ORIGINAL["fit"]},
                    {d:12 for d in new_dates})
        self.assertEqual(len(called),30) # only original fit + new confirmation
        self.assertEqual(len(fit),20*7) # 12 snapshots, 5 future = 7 targets
        self.assertEqual(len(other),30)
        self.assertEqual(qc["source_rows_warmup"],240)
        self.assertFalse(qc["warmup_future_target_labels_computed"])
        self.assertFalse(qc["new_final_row_converted"])
        self.assertTrue(all(r["truth"] is None
                            for d in NEW["warmup"] for r in other[d]))
        self.assertEqual(sum(r["truth"] is not None for d in NEW["confirmation"]
                             for r in other[d]),20) # two label-ready per day

    def test_new_final_overlap_is_rejected_before_reader_import(self):
        changed={k:list(v) for k,v in NEW.items()}
        changed["sealed_final"][0]=changed["confirmation"][0]
        with self.assertRaisesRegex(Exception,"strict authorized"):
            runner._read_authorized_days("/fake","000012.SZ",ORIGINAL,changed,{},{})
        changed2={k:list(v) for k,v in NEW.items()}
        changed2["warmup"][0]="2022-05-16"
        with self.assertRaisesRegex(Exception,"strict authorized"):
            runner._read_authorized_days("/fake","000012.SZ",ORIGINAL,changed2,{},{})


if __name__=="__main__":
    unittest.main()

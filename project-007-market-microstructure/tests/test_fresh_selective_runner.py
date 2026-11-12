"""D012 source-blind final-cohort reader and leakage isolation tests.

Use no provider market records, no scikit-learn, no pyarrow runtime.
"""
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
spec=importlib.util.spec_from_file_location(
    "d012_runner",ROOT/"research"/"run_fresh_selective_alerts_once.py"
)
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
TZ=timezone(timedelta(hours=8))


def dates45():
    start=date(2022,3,8)
    selected=[]
    for i in range(90):
        day=start+timedelta(days=i)
        if day.weekday()<5:selected.append(day.isoformat())
    return {
        "fit":selected[:20],
        "calibration":selected[20:30],
        "confirmation":selected[30:35],
        "sealed_final":selected[35:45]
    }


def row(day):
    stamp=datetime.fromisoformat(day+"T13:00:15").replace(tzinfo=TZ)
    result={
        "symbol":"000012.SZ","available_at":stamp,
        "source_event_time":stamp-timedelta(seconds=1),
        "stale":False,"missing_depth":False
    }
    for n in range(1,6):
        result[f"bid_price_{n}"]=Decimal("99.99")-Decimal(n-1)/100
        result[f"ask_price_{n}"]=Decimal("100.01")+Decimal(n-1)/100
        result[f"bid_volume_{n}"]=10
        result[f"ask_volume_{n}"]=10
    return result


class FakeBatch:
    def __init__(self,rows):
        self.rows=rows
        self.schema=types.SimpleNamespace(get_field_index=lambda n:0 if n=="available_at" else -1)
    def column(self,i):
        if i!=0:raise AssertionError("available_at column must be read first")
        return types.SimpleNamespace(to_pylist=lambda:[r["available_at"] for r in self.rows])
    def slice(self,first,n):
        return FakeBatch(self.rows[first:first+n])
    def to_pylist(self):
        if any(r["available_at"].date().isoformat() in DATES["sealed_final"] for r in self.rows):
            raise AssertionError("SEALED future price row converted")
        return self.rows


DATES=dates45()


class D012IsolationTests(unittest.TestCase):
    def test_never_builds_future_labels_for_calibration_and_does_not_decode_final(self):
        input_rows=[row(day) for label in ("fit","calibration","confirmation","sealed_final")
                    for day in DATES[label]]
        batch1=FakeBatch(input_rows[:22])
        batch2=FakeBatch(input_rows[22:40])
        batch3=FakeBatch(input_rows[40:])
        class FakeParquet:
            schema_arrow=types.SimpleNamespace(
                names=list(runner.REQUIRED_FIELDS+runner.SOURCE_FIELDS)
            )
            def __init__(self,p):pass
            def iter_batches(self,**kwargs):
                yield batch1
                yield batch2
                raise AssertionError("must NOT read a batch after the sealed start")

        pyarrow=types.ModuleType("pyarrow")
        pyarrow.__path__=[]
        parquet=types.ModuleType("pyarrow.parquet")
        parquet.ParquetFile=FakeParquet
        pyarrow.parquet=parquet
        with patch.dict(sys.modules,{"pyarrow":pyarrow,"pyarrow.parquet":parquet}):
            result,report=runner.read_fresh_35_only(
                "/fake","000012.SZ",DATES,
                {day:1 for label in ("fit","calibration","confirmation")
                 for day in DATES[label]}
            )
        self.assertEqual(len(result["fit"][0]),20)
        self.assertIsNone(result["calibration"][0])
        self.assertEqual(len(result["calibration"][2]),10)
        self.assertEqual(len(result["confirmation"][0]),5)
        self.assertFalse(report["calibration_future_labels_computed"])
        self.assertFalse(report["reserved_final_row_admitted"])
        self.assertFalse(report["legacy_sealed_block_row_admitted"])
        self.assertEqual(report["fit_source_rows"],20)
        self.assertEqual(report["calibration_source_rows"],10)
        self.assertEqual(report["confirmation_source_rows"],5)

    def test_rejects_overlapping_or_nonfresh_dates_before_importing_parquet(self):
        changed={k:list(v) for k,v in DATES.items()}
        changed["sealed_final"][0]=changed["confirmation"][0]
        with self.assertRaisesRegex(Exception,"35 fresh source dates"):
            runner.read_fresh_35_only("/fake","S",changed,{})
        changed={k:list(v) for k,v in DATES.items()}
        changed["fit"][0]="2022-02-28"
        with self.assertRaisesRegex(Exception,"35 fresh source dates"):
            runner.read_fresh_35_only("/fake","S",changed,{})

    def test_invalid_target_cannot_enter_confirmation(self):
        from microstructure.chronological_baselines import Example
        good=Example(0,"A","2022-04-01",2,2,None,())
        invalid=Example(1,"A","2022-04-01",None,2,"incomplete_future",())
        source=runner._selection_candidates(
            (good,invalid),((2,0,0),(2,0,0))
        )
        self.assertEqual(len(source),1)
        self.assertEqual(source[0][0],good)


if __name__=="__main__":
    unittest.main()

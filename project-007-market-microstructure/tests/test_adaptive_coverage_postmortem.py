"""D014 postmortem is source-only and must never need target labels."""
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
from freeze_adaptive_dates_once import load_manifest
D=load_manifest()["dates"]
TZ=timezone(timedelta(hours=8))
spec=importlib.util.spec_from_file_location(
    "d014_coverage",ROOT/"research"/"run_adaptive_coverage_postmortem_once.py")
coverage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


def row(day,i):
    t=datetime.fromisoformat(day+"T13:00:15").replace(tzinfo=TZ)+timedelta(seconds=15*i)
    x={"symbol":"000012.SZ","available_at":t,"source_event_time":t,
       "stale":False,"missing_depth":False}
    for level in range(1,6):
        x[f"bid_price_{level}"]=Decimal("99.99")-Decimal(level-1)/100
        x[f"ask_price_{level}"]=Decimal("100.01")+Decimal(level-1)/100
        x[f"bid_volume_{level}"]=10
        x[f"ask_volume_{level}"]=10
    return x


class FakeBatch:
    schema=types.SimpleNamespace(get_field_index=lambda key:0 if key=="available_at" else -1)
    def __init__(self,raw):self.raw=raw
    def column(self,i):
        self_check=i==0
        if not self_check:raise AssertionError("only timestamp selection permitted")
        return types.SimpleNamespace(to_pylist=lambda:[r["available_at"] for r in self.raw])
    def slice(self,left,n):return FakeBatch(self.raw[left:left+n])
    def to_pylist(self):
        if any(r["available_at"].date().isoformat() in D["sealed_final"] for r in self.raw):
            raise AssertionError("SEALED final quote row converted")
        return self.raw


class CoverageAuditIsolationTests(unittest.TestCase):
    def test_current_past_only_without_future_classes(self):
        accepted=D["warmup"]+D["confirmation"]
        source=[row(d,i) for d in accepted+D["sealed_final"][:1] for i in range(12)]
        batches=[FakeBatch(source[i:i+128]) for i in range(0,len(source),128)]
        class FakeParquet:
            schema_arrow=types.SimpleNamespace(names=list(dict.fromkeys(
                coverage.REQUIRED_FIELDS+coverage.SOURCE_FIELDS)))
            def __init__(self,path):pass
            def iter_batches(self,**kwargs):
                for b in batches:yield b
        pyarrow=types.ModuleType("pyarrow")
        pyarrow.__path__=[]
        parquet=types.ModuleType("pyarrow.parquet")
        parquet.ParquetFile=FakeParquet
        pyarrow.parquet=parquet
        with patch.dict(sys.modules,{"pyarrow":pyarrow,"pyarrow.parquet":parquet}):
            output=coverage._read_30_only("/fake","000012.SZ",D,
                                            {d:12 for d in accepted})
        self.assertEqual(len(output),30)
        self.assertEqual(output[D["warmup"][0]]["source_rows"],12)
        self.assertEqual(output[D["warmup"][0]]["decision_ready_intersection"],7)
        self.assertEqual(output[D["confirmation"][0]]["decision_ready_intersection"],7)
        self.assertEqual(output[D["confirmation"][0]]["sessions"]["afternoon"]["source_rows"],12)

    def test_reserve_overlap_rejected_before_importing_pyarrow(self):
        bad={k:list(v) for k,v in D.items()}
        bad["sealed_final"][0]=bad["confirmation"][-1]
        with self.assertRaisesRegex(Exception,"restricted"):
            coverage._read_30_only("/fake","000012.SZ",bad,{})


if __name__=="__main__":
    unittest.main()

"""Synthetic-only D010 snapshot training isolation and matched comparison tests."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
spec=importlib.util.spec_from_file_location(
    "d010_training_liquidity",ROOT/"research"/"run_training_liquidity_once.py")
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

from microstructure.liquidity_features import SOURCE_FIELDS
from microstructure.chronological_baselines import Example

TZ=timezone(timedelta(hours=8))
def record(day):
    t=datetime.fromisoformat(day+"T13:00:15").replace(tzinfo=TZ)
    row={
        "symbol":"000012.SZ","available_at":t,
        "source_event_time":t-timedelta(seconds=1),
        "stale":False,"missing_depth":False,
    }
    for level in range(1,6):
        row[f"bid_price_{level}"]=Decimal("99.99")-Decimal(level-1)/100
        row[f"ask_price_{level}"]=Decimal("100.01")+Decimal(level-1)/100
        row[f"bid_volume_{level}"]=12
        row[f"ask_volume_{level}"]=8
    return row


class _FakeBatch:
    def __init__(self, rows):
        self.rows=list(rows)
        self.schema=types.SimpleNamespace(
            get_field_index=lambda name: 0 if name=="available_at" else -1
        )
    def column(self,index):
        if index!=0: raise AssertionError("source timestamp index mismatch")
        return types.SimpleNamespace(to_pylist=lambda:[r["available_at"] for r in self.rows])
    def slice(self,start,length):
        return _FakeBatch(self.rows[start:start+length])
    def to_pylist(self):
        if any(r["available_at"].date().isoformat() not in TRAIN for r in self.rows):
            raise AssertionError("non-training source pricing rows converted to Python")
        return self.rows


TRAIN=[
    (datetime(2022,1,11)+timedelta(days=i)).date().isoformat()
    for i in range(20)
]


class D010TrainingIsolationTests(unittest.TestCase):
    def test_feature_reader_never_converts_validation_rows(self):
        # synthetic business dates aren't required for this date-cutoff reader;
        # the source-date manifest validation was tested separately.
        source_rows=[record(TRAIN[0])]+[record(d) for d in TRAIN[1:]]
        source_rows += [record("2022-02-15"),record("2022-02-16")]
        batch1=_FakeBatch(source_rows[:6])
        batch2=_FakeBatch(source_rows[6:21])
        batch3=_FakeBatch(source_rows[21:])
        class FakeFile:
            schema_arrow=types.SimpleNamespace(names=list(runner.REQUIRED_FIELDS+SOURCE_FIELDS))
            def __init__(self,path): pass
            def iter_batches(self,**kwargs):
                yield batch1
                yield batch2
                raise AssertionError("must not read later source batches after boundary")
        module=types.ModuleType("pyarrow")
        module.__path__=[]
        parquet=types.ModuleType("pyarrow.parquet")
        parquet.ParquetFile=FakeFile
        module.parquet=parquet
        counts={day:1 for day in TRAIN}
        with patch.dict(sys.modules,{"pyarrow":module,"pyarrow.parquet":parquet}):
            fit,confirmation,metadata=runner.read_training_only(
                "/dummy.parquet","000012.SZ",TRAIN,counts
            )
        self.assertEqual(len(fit[0]),14)
        self.assertEqual(len(confirmation[0]),6)
        self.assertEqual(metadata["source_fit_rows"],14)
        self.assertEqual(metadata["source_internal_confirmation_rows"],6)
        self.assertFalse(metadata["later_date_source_rows_admitted"])
        self.assertEqual(len(fit[1]),14)
        self.assertEqual(len(confirmation[1]),6)

    def test_metrics_require_identical_origin_denominators(self):
        cases=[
            Example(1,"S","2022-01-12",1,3,None,()),
            Example(2,"S","2022-01-12",2,2,None,()),
            Example(3,"S","2022-01-12",3,1,None,()),
        ]
        records=tuple((e,(2.0,0.3,-0.1)) for e in cases)
        metrics=runner._metric_pair(records,2,[1,2,3])
        self.assertEqual(metrics["B0_majority"]["n"],3)
        self.assertEqual(metrics["B1_backward_trend"]["n"],3)
        self.assertEqual(metrics["B2_book_snapshot"]["n"],3)
        self.assertAlmostEqual(metrics["B2_book_snapshot"]["accuracy"],1.0)
        with self.assertRaisesRegex(AssertionError,"shape"):
            runner._metric_pair(records,2,[1,2])

    def test_missing_feature_or_b1_abstention_excluded_from_matched_set(self):
        samples=[
            (Example(1,"S","2022-01-12",1,1,None,()),(2.,0.,0.)),
            (Example(2,"S","2022-01-12",2,None,None,()),(2.,0.,0.)),
            (Example(3,"S","2022-01-12",3,3,None,()),None),
            (Example(4,"S","2022-01-12",None,2,"incomplete_future",()),(2.,0.,0.)),
        ]
        matched=runner._selected_common(samples)
        self.assertEqual(len(matched),1)
        self.assertEqual(matched[0][0].row_index,1)

    def test_prediction_origin_keys_reject_duplicates_and_invalid_class(self):
        e=Example(1,"S","2022-01-12",1,3,None,())
        with self.assertRaisesRegex(AssertionError,"invalid or duplicate"):
            runner._prediction_map([(e,(1,1,1)),(e,(1,1,1))],[1,2])
        with self.assertRaisesRegex(AssertionError,"invalid or duplicate"):
            runner._prediction_map([(e,(1,1,1))],[4])

if __name__=="__main__":
    unittest.main()

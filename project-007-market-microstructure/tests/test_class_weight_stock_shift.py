"""D011 synthetic-only fit-date isolation and class-weight diagnostic tests."""
import importlib.util
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
spec=importlib.util.spec_from_file_location(
    "d011_stock_diagnosis",ROOT/"research"/"run_class_weight_stock_shift_once.py"
)
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

from microstructure.chronological_baselines import Example
from microstructure.liquidity_features import SOURCE_FIELDS

TZ=timezone(timedelta(hours=8))
FIT14=(
    "2022-01-11","2022-01-12","2022-01-13","2022-01-14",
    "2022-01-17","2022-01-18","2022-01-19","2022-01-20",
    "2022-01-21","2022-01-24","2022-01-25","2022-01-26",
    "2022-01-27","2022-01-28",
)

def snapshot(day):
    timestamp=datetime.fromisoformat(day+"T13:00:15").replace(tzinfo=TZ)
    row={
        "symbol":"000012.SZ","available_at":timestamp,
        "source_event_time":timestamp-timedelta(seconds=1),
        "stale":False,"missing_depth":False,
    }
    for level in range(1,6):
        row[f"bid_price_{level}"]=Decimal("99.99")-Decimal(level-1)/100
        row[f"ask_price_{level}"]=Decimal("100.01")+Decimal(level-1)/100
        row[f"bid_volume_{level}"]=20
        row[f"ask_volume_{level}"]=10
    return row


class _QuoteBatch:
    def __init__(self,rows):
        self.rows=list(rows)
        self.schema=types.SimpleNamespace(
            get_field_index=lambda name: 0 if name=="available_at" else -1
        )
    def column(self,index):
        if index!=0:
            raise AssertionError("timestamp column index is not zero")
        return types.SimpleNamespace(
            to_pylist=lambda:[row["available_at"] for row in self.rows]
        )
    def slice(self,start,length):
        return _QuoteBatch(self.rows[start:start+length])
    def to_pylist(self):
        if any(row["available_at"].date().isoformat() not in FIT14 for row in self.rows):
            raise AssertionError("unapproved source price/depth conversion")
        return self.rows


class D011FitOnlyTests(unittest.TestCase):
    def test_truncated_reader_disallows_forming_any_later_quote_objects(self):
        rows=[snapshot(d) for d in FIT14]
        end=[snapshot("2022-02-07"),snapshot("2022-02-08")]
        expected=[_QuoteBatch(rows[:5]),_QuoteBatch(rows[5:]+end)]
        class FakeFile:
            schema_arrow=types.SimpleNamespace(
                names=list(runner.REQUIRED_FIELDS+SOURCE_FIELDS)
            )
            def __init__(self,_):pass
            def iter_batches(self,**kwargs):
                yield expected[0]
                yield expected[1]
                raise AssertionError("reader must not continue after Jan28 boundary")
        pyarrow=types.ModuleType("pyarrow")
        pyarrow.__path__=[]
        pq=types.ModuleType("pyarrow.parquet")
        pq.ParquetFile=FakeFile
        pyarrow.parquet=pq
        counts={d:1 for d in FIT14}
        with patch.dict(sys.modules,{"pyarrow":pyarrow,"pyarrow.parquet":pq}):
            fit,diagnostic,info=runner.read_first_14_dates_only(
                "/fixture.parquet","000012.SZ",FIT14,counts
            )
        self.assertEqual(len(fit),10)
        self.assertEqual(len(diagnostic),4)
        self.assertEqual(info["first10_fit"]["source_rows"],10)
        self.assertEqual(info["last4_internal_diagnostic"]["source_rows"],4)
        self.assertFalse(info["future_date_quotes_admitted"])
        self.assertTrue(all(e.trading_date in FIT14 for e,x in fit+diagnostic))

    def test_reader_rejects_unapproved_date_selection(self):
        with self.assertRaisesRegex(Exception,"fourteen"):
            runner.read_first_14_dates_only("/dummy","000012.SZ",FIT14[:12],{})

    def test_duplicate_prediction_key_rejected(self):
        example=Example(1,"000012.SZ","2022-01-25",2,2,None,())
        rows=[(example,(2.0,0.0,0.0))]*2
        with self.assertRaisesRegex(AssertionError,"duplicate"):
            runner._predict_map(rows,[2,2])

    def test_predicted_precision_and_direction_frequency(self):
        ex=[
            Example(0,"S","2022-01-25",1,1,None,()),
            Example(1,"S","2022-01-25",2,2,None,()),
            Example(2,"S","2022-01-25",3,3,None,()),
            Example(3,"S","2022-01-25",2,2,None,()),
        ]
        rows=[(e,(1.5,0.1,-0.1)) for e in ex]
        maps={
            "B0":runner._predict_map(rows,[2,2,2,2]),
            "weight":runner._predict_map(rows,[1,1,3,3]),
        }
        out=runner._compare_models(rows,maps)
        self.assertEqual(out["B0"]["metrics"]["n"],4)
        self.assertEqual(out["weight"]["metrics"]["n"],4)
        self.assertEqual(out["B0"]["prediction_diagnostics"]["predicted_up_down_precision"],{"1":None,"3":None})
        self.assertEqual(out["weight"]["prediction_diagnostics"]["predicted_up_down_precision"],{"1":0.5,"3":0.5})
        self.assertAlmostEqual(out["weight"]["prediction_diagnostics"]["predicted_direction_rate"],1.0)
        self.assertEqual(out["weight"]["prediction_diagnostics"]["predicted_class_count"],{"1":2,"2":0,"3":2})

    def test_no_data_access_outside_train14_is_registered(self):
        self.assertEqual(runner.FIT_DATES,10)
        self.assertEqual(runner.INTERNAL_DIAG_DATES,4)
        self.assertEqual(runner.MAX_ALLOWED_DATES,14)
        self.assertEqual(runner.EXPECTED_MANIFEST,"50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6")


if __name__=="__main__":
    unittest.main()

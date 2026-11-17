"""All fixture observations in this module are SYNTHETIC, for tests only."""
import io
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analytics import prepare, load_csv, journey, funnel, stage_counts

BASE = 1430000000000

def frame(rows):
    return pd.DataFrame([(BASE+t, v, e, i) for t,v,e,i in rows], columns=['timestamp','visitorid','event','itemid'])

def test_order_duplicates_reversals_repeat_transactions():
    raw = frame([(3,'a','transaction','x'),(1,'a','view','x'),(2,'a','addtocart','x'),(3,'a','transaction','x'),(4,'a','transaction','x'),(1,'b','transaction','x'),(2,'b','addtocart','x'),(3,'b','view','x')])
    clean, audit = prepare(raw)
    assert audit['exact_duplicate_rows'] == 1
    assert audit['visitors_with_input_order_reversals'] == 1
    assert funnel(journey(clean)).visitors.tolist() == [2,1,1]
    assert stage_counts(clean).events.tolist() == [2,2,3]

def test_item_matching_and_ties():
    clean,_ = prepare(frame([(1,'a','view','x'),(2,'a','addtocart','y'),(3,'a','transaction','y'),(1,'b','view','x'),(1,'b','addtocart','x'),(2,'b','transaction','x')]))
    assert funnel(journey(clean)).visitors.tolist() == [2,1,1]
    assert funnel(journey(clean,True)).visitors.tolist() == [2,0,0]

def test_missing_ids_invalid_time_unknown_event():
    raw = frame([(1,None,'view','x'),(2,'a','view',None),(3,'a','other','x')])
    raw['timestamp'] = raw.timestamp.astype('string')
    raw.loc[2,'timestamp'] = 'bad'
    clean,audit = prepare(raw)
    assert audit['missing_visitor_ids'] == 1
    assert audit['invalid_timestamps'] == 1
    assert audit['unknown_or_missing_events'] == 1
    assert len(clean) == 1
    assert len(journey(clean,True)) == 0

@pytest.mark.parametrize('rows', [[], [(1,'a','transaction','x')]])
def test_empty_or_no_views(rows):
    clean,_ = prepare(frame(rows))
    assert funnel(journey(clean)).visitors.tolist() == [0,0,0]
    assert funnel(journey(clean,True)).visitors.tolist() == [0,0,0]

def test_schema_and_csv_ids():
    with pytest.raises(ValueError, match='Missing required'):
        prepare(pd.DataFrame({'timestamp':[]}))
    clean,_ = load_csv(io.StringIO('timestamp,visitorid,event,itemid\n1430000000000,001,view,002\n'))
    assert clean.visitorid.iloc[0] == '001'
    with pytest.raises(ValueError, match='empty'):
        load_csv(io.StringIO(''))

def test_timestamp_seconds_fractional_and_null():
    raw = frame([(1,'a','view','x')]*4)
    raw['timestamp'] = ['1430000000','1430000000000.5',None,'1430000000000']
    clean,audit = prepare(raw)
    assert audit['invalid_timestamps'] == 3
    assert len(clean) == 1

def test_multiple_items_one_visitor():
    clean,_ = prepare(frame([(t,'a',e,i) for i in ['x','y'] for t,e in [(1,'view'),(2,'addtocart'),(3,'transaction')]]))
    assert funnel(journey(clean,True)).visitors.tolist() == [1,1,1]

def test_all_invalid_and_oversize():
    clean,audit = prepare(pd.DataFrame({'timestamp':['bad'], 'visitorid':[None], 'event':['unknown'], 'itemid':[None]}))
    assert audit['analysis_rows'] == 0
    assert funnel(journey(clean)).visitors.tolist() == [0,0,0]
    class Oversize:
        size = 101 * 1024 * 1024
    with pytest.raises(ValueError, match='exceeds'):
        load_csv(Oversize())

"""Date-isolation and vendor-comparison tests use synthetic fixtures only."""
import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from daily_study.source_audit import (read_csv_discovery, read_lean_discovery,
    audit_prices, same_stock_comparison, period_coverage)


def test_csv_discards_protected_rows_before_numeric_parsing(tmp_path):
    path=tmp_path/'prices.csv'
    path.write_text('Date,Open,High,Low,Close,Volume,Name\n2015-12-31,10,12,9,11,100,A\n2016-01-04,POISON,POISON,POISON,POISON,POISON,A\n')
    frame, columns=read_csv_discovery(path)
    assert len(frame)==1 and frame.stock.iloc[0]=='A'
    assert frame.close.iloc[0]==11 and columns[0]=='Date'
    path.write_text('<html>not a dataset</html>')
    with pytest.raises(ValueError):read_csv_discovery(path)


def test_wide_csv_and_raw_lean_zip_have_date_guards(tmp_path):
    path=tmp_path/'wide.csv';path.write_text('MSFT,GSPC,Date\n10,100,2015-12-31\nPOISON,POISON,2016-01-04\n')
    frame,_=read_csv_discovery(path,wide_columns=['MSFT','GSPC'])
    assert sorted(frame.close.tolist())==[10,100]
    path=tmp_path/'a.zip'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('a.csv','20151231 00:00,100000,120000,90000,110000,100\n20160104 00:00,POISON\n')
    frame=read_lean_discovery(path,'A')
    assert len(frame)==1 and frame.close.iloc[0]==11


def test_quality_flags_do_not_mutate_or_treat_extremes_as_errors():
    frame=pd.DataFrame(dict(date=pd.to_datetime(['2015-01-02','2015-01-05']),stock=['A','A'],
        open=[10,20],high=[11,19],low=[9,18],close=[10,20],volume=[0,100]))
    before=frame.copy(deep=True);summary=audit_prices(frame)
    assert summary['gt20pct_absolute_simple_moves_for_review']==1
    assert summary['internally_inconsistent_ohlc']==1
    pd.testing.assert_frame_equal(frame,before)
    assert 'excluded' not in summary


def test_vendor_comparison_ignores_constant_scale_and_requires_matching_intervals():
    frame=pd.DataFrame(dict(date=pd.bdate_range('2015-01-02',periods=5),stock=['A']*5,close=[10,11,9,12,13]))
    other=frame.copy();other['close']*=7
    result=same_stock_comparison(frame,other,'A')
    assert result['matched_return_intervals']==4
    assert result['absolute_log_return_difference_basis_points']['1']<1e-10
    other=other.drop(index=1)
    assert same_stock_comparison(frame,other,'A')['matched_return_intervals']==2


def test_all_audit_entry_points_refuse_protected_observations():
    future=pd.DataFrame(dict(date=pd.to_datetime(['2016-01-04']),stock=['A'],close=[1]))
    with pytest.raises(ValueError):audit_prices(future)
    with pytest.raises(ValueError):same_stock_comparison(future,future,'A')
    with pytest.raises(ValueError):period_coverage(future,[('x','2000-01-01','2015-12-31')])

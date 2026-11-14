"""Invented format mimics only, never copied French observations."""
from datetime import date
import io
import json
import socket
import zipfile
import pytest
from industry_companion.parser import DataError, INDUSTRIES, parse_archive
from industry_companion.audit import audit_dataset, expected_sessions


def text(vw=None,ew=None):
    if vw is None:vw=['20160104,'+','.join(str(i/10) for i in range(10)),'20241231,'+','.join('1.25' for _ in range(10))]
    if ew is None:ew=['20160104,'+','.join('-2.5' for _ in range(10)),'20241231,'+','.join('0.5' for _ in range(10))]
    header=','+','.join(INDUSTRIES)
    return '\n'.join(['SYNTHETIC FORMAT FIXTURE — NOT FRENCH DATA','This file was created using the 202610 CRSP database.',
        'Returns are in percent.','Average Value Weighted Returns -- Daily',header,*vw,'',
        'Average Equal Weighted Returns -- Daily',header,*ew,''])


def zipped(source,member='10_Industry_Portfolios_Daily.csv'):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:archive.writestr(member,source)
    return out.getvalue()


def test_primary_units_vintage_redacted_repr_and_cutoff():
    result=parse_archive(zipped(text()))
    assert result.primary.weighting=='value_weighted' and set(result.panels)=={'value_weighted','equal_weighted'}
    assert result.primary.dates==(date(2016,1,4),date(2024,12,31))
    assert result.primary.returns[0][1]==.001 and result.primary.returns[1][0]==.0125
    assert result.panels['equal_weighted'].returns[0][0]==-.025 and result.publisher_vintage=='202610'
    assert 'values=redacted' in repr(result) and '0.0125' not in repr(result.primary)
    with pytest.raises(DataError,match='WRONG_UNITS'):parse_archive(zipped(text()),units='decimals')
    poison=['20151231,returns in decimals,NaN,PRIVATEPOISON','20250101,returns in decimals,-999,PRIVATEPOISON']
    limited=parse_archive(zipped(text(vw=[poison[0],'20160104,'+','.join(['2']*10),poison[1]])))
    assert limited.primary.dates==(date(2016,1,4),) and limited.excluded_outside_window
    assert all(2016<=d.year<=2024 for p in limited.panels.values() for d in p.dates)


@pytest.mark.parametrize('token,code',[('-99.99','MISSING_SENTINEL'),('-999','MISSING_SENTINEL'),('nan','NONFINITE_RETURN'),('inf','NONFINITE_RETURN'),
    ('1e999','NONFINITE_RETURN'),('-100.01','IMPOSSIBLE_SIMPLE_RETURN'),('','MISSING_RETURN'),('PRIVATEPOISON','INVALID_RETURN_TOKEN')])
def test_anomalies_without_raw_echo(token,code):
    row='20160104,'+','.join([token]+['0']*9)
    with pytest.raises(DataError) as exc:parse_archive(zipped(text(vw=[row])))
    assert str(exc.value)==code and 'PRIVATEPOISON' not in str(exc.value)


@pytest.mark.parametrize('change,code',[('duplicate','DUPLICATE_DATE'),('backward','NONMONOTONE_DATE'),('invalid','INVALID_DATE'),
    ('monthly','NON_DAILY_DATE'),('annual','NON_DAILY_DATE'),('width','ROW_WIDTH'),('empty','EMPTY_DEVELOPMENT_PANEL')])
def test_chronology_frequency_width(change,code):
    a='20160104,'+','.join(['0']*10);b='20241231,'+','.join(['0']*10)
    rows={'duplicate':[a,a],'backward':[b,a],'invalid':[a.replace('20160104','20160230')],
        'monthly':[a.replace('20160104','201601')],'annual':[a.replace('20160104','2016')],
        'width':['20160104,0'],'empty':['20250101,POISON']}[change]
    with pytest.raises(DataError,match=code):parse_archive(zipped(text(vw=rows)))


def test_sections_schema_units_no_ew_fallback():
    source=text()
    for bad in [source.replace('Average Value Weighted Returns -- Daily','Ignored section'),source.replace('Average Value Weighted Returns -- Daily','Average Value Weighted Returns -- Monthly')]:
        with pytest.raises(DataError):parse_archive(zipped(bad))
    for columns in ('Durbl,NoDur','NoDur,NoDur'):
        with pytest.raises(DataError,match='INDUSTRY_HEADER_MISMATCH'):parse_archive(zipped(source.replace('NoDur,Durbl',columns)))
    with pytest.raises(DataError,match='DUPLICATE_RETURN_SECTION'):parse_archive(zipped(source+'\nAverage Value Weighted Returns -- Daily\n'))
    with pytest.raises(DataError,match='CONFLICTING_UNITS'):parse_archive(zipped(source.replace('Returns are in percent.','Returns are in decimals.')))


@pytest.mark.parametrize('member',['../10_Industry_Portfolios_Daily.csv','/10_Industry_Portfolios_Daily.csv','folder/10_Industry_Portfolios_Daily.csv','folder\\10_Industry_Portfolios_Daily.csv','10_Industry_Portfolios.csv','10_Momentum_Portfolios_Daily.csv'])
def test_archive_names(member):
    with pytest.raises(DataError):parse_archive(zipped(text(),member))


def test_archive_limits_members():
    with pytest.raises(DataError,match='INVALID_ZIP'):parse_archive(b'not a zip')
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('10_Industry_Portfolios_Daily.csv',text());z.writestr('extra.txt','unapproved')
    with pytest.raises(DataError,match='ARCHIVE_MEMBER_COUNT'):parse_archive(out.getvalue())
    with pytest.raises(DataError,match='ARCHIVE_EXPANSION_LIMIT'):parse_archive(zipped('0'*100000))


def test_audit_no_rows_pit_claims_or_network(monkeypatch):
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:(_ for _ in ()).throw(AssertionError('No network')))
    dataset=parse_archive(zipped(text()))
    metadata=dict(source_url='SYNTHETIC fixture metadata',retrieved_at_utc='2026-11-14T00:00:00+00:00',acquisition_method='owner_recorded_local_file')
    report=audit_dataset(dataset,metadata,sessions=(date(2016,1,4),date(2016,1,5),date(2024,12,31)))
    assert report['panels']['value_weighted']['missing_sessions']==report['panels']['equal_weighted']['missing_sessions']==1
    assert not report['coverage_complete'] and not report['point_in_time_verified'] and not report['performance_cleared']
    assert not report['raw_observations_in_output'] and all(k not in report for k in ('returns','rows','values','weights','CAGR','Sharpe'))
    assert '0.0125' not in json.dumps(report) and '-0.025' not in json.dumps(report)
    assert report['acquisition_method']=='owner_recorded_local_file'
    direct_report=audit_dataset(dataset,dict(metadata,acquisition_method='bounded_direct_https'),sessions=dataset.primary.dates)
    assert direct_report['acquisition_method']=='bounded_direct_https'


def test_calendar_local_holiday_aware():
    sessions=expected_sessions()
    assert date(2016,1,1) not in sessions and date(2024,12,31) in sessions
    assert date(2018,12,5) not in sessions and date(2022,6,20) not in sessions
    assert all(date(2016,1,1)<=d<=date(2024,12,31) for d in sessions)

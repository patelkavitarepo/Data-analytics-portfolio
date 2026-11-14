"""Coverage/quality metadata only. Never return row values, paths or performance."""
import hashlib
from importlib.metadata import version
import json
import platform
from pathlib import Path

from .parser import START, END, INDUSTRIES, PRIMARY, PANELS, parse_archive


def expected_sessions():
    try:import exchange_calendars as calendars
    except ImportError:
        from .parser import DataError
        raise DataError('CALENDAR_DEPENDENCY_UNAVAILABLE') from None
    return tuple(d.date() for d in calendars.get_calendar('XNYS',start='2015-12-01',end=END.isoformat()).sessions_in_range(START.isoformat(),END.isoformat()))


def audit_dataset(dataset,manifest,*,sessions=None):
    expected=tuple(expected_sessions() if sessions is None else sessions)
    expected_set=set(expected)
    panels={}
    for name in PANELS:
        panel=dataset.panels[name];observed=set(panel.dates)
        panels[name]=dict(development_rows=len(panel.dates),industry_count=len(INDUSTRIES),
            first_development_date=panel.dates[0].isoformat(),last_development_date=panel.dates[-1].isoformat(),
            expected_sessions=len(expected),missing_sessions=len(expected_set-observed),non_session_dates=len(observed-expected_set),
            duplicate_dates=0,missing_sentinels=0,nonfinite_values=0,impossible_simple_returns=0,
            valid_return_cells=len(panel.dates)*len(INDUSTRIES),strict_parse_passed=True)
    mismatch=len(set(dataset.panels[PANELS[0]].dates)^set(dataset.panels[PANELS[1]].dates))
    complete=all(p['missing_sessions']==p['non_session_dates']==0 for p in panels.values()) and mismatch==0
    return dict(checkpoint='industry-ingestion-v1',source='Kenneth French daily 10 Industry Portfolios',
        source_url=manifest['source_url'],retrieved_at_utc=manifest['retrieved_at_utc'],acquisition_method=manifest['acquisition_method'],archive_sha256=dataset.archive_sha256,
        member_sha256=dataset.member_sha256,publisher_crsp_vintage=dataset.publisher_vintage,
        provenance_manifest_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        parser_sha256=hashlib.sha256((Path(__file__).parent/'parser.py').read_bytes()).hexdigest(),
        versions=dict(python=platform.python_version(),exchange_calendars=version('exchange-calendars'),pandas=version('pandas'),numpy=version('numpy')),
        panel_date_alignment_mismatches=mismatch,
        scope=dict(start=START.isoformat(),end=END.isoformat(),primary=PRIMARY,equal_weighted='separate optional future sensitivity; audited separately'),
        calendar_basis='XNYS sessions; calendar cross-check, not proof of historical portfolio availability',
        out_of_scope_rows_excluded=dataset.excluded_outside_window,panels=panels,coverage_complete=complete,
        point_in_time_verified=False,performance_cleared=False,raw_observations_in_output=False,
        limitations=['Current/revised snapshot is not historical as-of data.',
            'SIC-assigned US equity industry portfolios, not individual stocks, ETFs or executable prices.',
            '2025 FIZ-to-CIZ processing change may affect historical revisions; vintage comparison not completed.',
            'Calendar coverage and syntactic quality do not establish economic accuracy or independent-source verification.',
            'Permission is limited and rescindable; no SPY or other external benchmark rights are granted.'])

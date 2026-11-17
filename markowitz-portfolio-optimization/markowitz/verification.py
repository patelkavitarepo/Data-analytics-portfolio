"""Require documented human source checks before computing market performance.

This verifies a review's consistency, not the truth of an uploader's assertions.
Reference observations and entitlement must be independently obtained by reviewer.
"""
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from .data import TICKERS
from .source_policy import require_approved_source

# Known reference publishers. Yahoo cannot independently corroborate itself.
REFERENCE_DOMAINS = ('nasdaq.com', 'ssga.com', 'invesco.com', 'ishares.com',
                     'spdrgoldshares.com', 'vanguard.com', 'alphavantage.co')


def verify_source(prices, audit, record):
    if audit['lost_price_rows']:
        raise ValueError('Source verification requires complete session coverage')
    if not isinstance(record, dict):
        raise ValueError('Source review JSON required before performance analysis')
    for field in ('reviewer', 'retrieved_utc', 'source_url', 'adjustment_evidence', 'analysis_permission_evidence'):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f'Source review needs {field}')
    source_host = urlparse(record['source_url']).hostname or ''
    if source_host == 'yahoo.com' or source_host.endswith('.yahoo.com'):
        raise ValueError('Yahoo-based performance is blocked: express collection permission and intended-use rights have not been established; a checkbox is not a grant')
    require_approved_source(record, audit)
    retrieved = pd.Timestamp(record['retrieved_utc'])
    if retrieved.tzinfo is None:
        raise ValueError('Source retrieval timestamp must include timezone')
    if retrieved > pd.Timestamp.now(tz='UTC'):
        raise ValueError('Source retrieval timestamp cannot be in the future')
    if retrieved.date() < pd.Timestamp(audit['as_of']).date():
        raise ValueError('Retrieval timestamp predates as_of')
    if record.get('as_of') != audit['as_of'] or record.get('snapshot_sha256') != audit['sha256_canonical_prices']:
        raise ValueError('Source review does not match this as_of and audited snapshot hash')
    if record.get('adjustment_convention') != 'split_and_dividend_adjusted_close':
        raise ValueError('Split/dividend adjustment convention must be independently documented')
    if record.get('analysis_use_authorized') is not True:
        raise ValueError('Permission to analyze these inputs must be established separately from redistribution')
    checks = record.get('spot_checks', {})
    if set(checks) != set(TICKERS) or not set(TICKERS).issubset(prices.columns):
        raise ValueError('Independent spot checks required for all eight prespecified ETFs')
    summaries = {}
    for ticker in TICKERS:
        check = checks[ticker]
        host = urlparse(check.get('reference_url', '')).hostname or ''
        if not any(host == domain or host.endswith('.' + domain) for domain in REFERENCE_DOMAINS):
            raise ValueError(f'{ticker}: use a documented independent publisher reference')
        date = pd.Timestamp(check.get('date'))
        if pd.isna(date) or date.tzinfo is not None or date != date.normalize() or date > pd.Timestamp('2024-12-31') or date < pd.Timestamp('2016-01-01'):
            raise ValueError(f'{ticker}: reference date must be a training/validation session; do not inspect holdout')
        if date > pd.Timestamp(audit['as_of']) or date not in prices.index:
            raise ValueError(f'{ticker}: reference date outside the audited snapshot')
        if check.get('adjustment_basis') != 'split_and_dividend_adjusted_close':
            raise ValueError(f'{ticker}: reference must use the same documented adjustment basis')
        try:
            reference = float(check.get('reference_price', float('nan')))
        except (ValueError, TypeError):
            raise ValueError(f'{ticker}: reference price must be an independently observed number') from None
        if not np.isfinite(reference) or reference <= 0:
            raise ValueError(f'{ticker}: invalid independently observed reference price')
        error = abs(float(prices.loc[date, ticker]) / reference - 1)
        # Fixed data verification tolerance; never tune using performance.
        if error > .005:
            raise ValueError(f'{ticker}: independent spot check differs by more than 0.5%; investigate adjustments')
        summaries[ticker] = {'date': str(date.date()), 'reference_url': check['reference_url'],
            'relative_difference': error, 'passed': True}
    return {'reviewer': record['reviewer'], 'retrieved_utc': record['retrieved_utc'],
        'source_url': record['source_url'], 'as_of': audit['as_of'],
        'snapshot_sha256': record['snapshot_sha256'], 'adjustment_evidence': record['adjustment_evidence'],
        'analysis_permission_evidence': record['analysis_permission_evidence'],
        'analysis_use_authorized': True, 'redistribution_permission': 'not established by this review',
        'spot_checks': summaries, 'limitation': 'Human source/entitlement assertions; application checks consistency, not authenticity.'}


def source_review_template(audit):
    """Unverified checklist tied to this snapshot; no price observations invented."""
    return {'reviewer': '', 'retrieved_utc': '', 'source_url': '',
        'as_of': audit['as_of'], 'snapshot_sha256': audit['sha256_canonical_prices'],
        'adjustment_convention': 'split_and_dividend_adjusted_close',
        'adjustment_evidence': '', 'analysis_use_authorized': False,
        'analysis_permission_evidence': '',
        'spot_checks': {ticker: {'date': min(audit['as_of'], '2024-12-31'),
            'reference_url': '', 'reference_price': None,
            'adjustment_basis': 'split_and_dividend_adjusted_close'} for ticker in TICKERS}}

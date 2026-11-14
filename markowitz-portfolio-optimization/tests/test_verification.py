from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from markowitz.data import TICKERS, audit_prices, sessions
from markowitz.verification import verify_source


@pytest.fixture
def reviewed(source_review, monkeypatch):
    # These tests isolate numerical review consistency, not a real provider grant.
    monkeypatch.setattr('markowitz.verification.require_approved_source', lambda record, audit: None)
    idx = sessions('2016-01-01', '2024-12-31')
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    _, _, _, audit = audit_prices(p, as_of='2024-12-31')
    return p, audit, source_review(p, audit)


def test_review_binds_all_eight_to_snapshot_and_analysis_only_rights(reviewed):
    p, audit, record = reviewed
    result = verify_source(p, audit, record)
    assert len(result['spot_checks']) == 8
    assert result['analysis_use_authorized']
    assert result['redistribution_permission'] == 'not established by this review'
    assert 'reference_price' not in str(result)


@pytest.mark.parametrize('field,value', [
    ('as_of', '2024-12-30'), ('snapshot_sha256', 'wrong'),
    ('analysis_use_authorized', False), ('analysis_permission_evidence', ''),
    ('adjustment_convention', 'unadjusted'), ('retrieved_utc', '2024-01-01T00:00:00Z'),
    ('retrieved_utc', '2026-11-11'), ('retrieved_utc', '2099-01-01T00:00:00Z')])
def test_unverified_or_mismatched_source_rejected(reviewed, field, value):
    p, audit, record = reviewed
    record[field] = value
    with pytest.raises(ValueError):
        verify_source(p, audit, record)


@pytest.mark.parametrize('field,value', [
    ('reference_url', 'https://finance.yahoo.com/'), ('reference_price', 80.),
    ('reference_price', np.nan), ('adjustment_basis', 'unadjusted'), ('date', '2025-01-02')])
def test_independent_reference_basis_price_and_no_holdout_checks(reviewed, field, value):
    p, audit, record = reviewed
    record['spot_checks']['SPY'][field] = value
    with pytest.raises(ValueError):
        verify_source(p, audit, record)


def test_missing_ticker_or_incomplete_audit_cannot_pass(reviewed):
    p, audit, record = reviewed
    missing = deepcopy(record)
    missing['spot_checks'].pop('GLD')
    with pytest.raises(ValueError, match='all eight'):
        verify_source(p, audit, missing)
    audit['lost_price_rows'] = 1
    with pytest.raises(ValueError, match='complete session'):
        verify_source(p, audit, record)


def test_supplied_json_and_user_checkbox_cannot_approve_a_source(source_review):
    idx = sessions('2016-01-01', '2024-12-31')
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    _, _, _, audit = audit_prices(p, as_of='2024-12-31')
    record = source_review(p, audit)
    with pytest.raises(ValueError, match='SOURCE EVIDENCE BLOCKED'):
        verify_source(p, audit, record)
    record['source_url'] = 'https://finance.yahoo.com/'
    with pytest.raises(ValueError, match='Yahoo-based performance is blocked'):
        verify_source(p, audit, record)

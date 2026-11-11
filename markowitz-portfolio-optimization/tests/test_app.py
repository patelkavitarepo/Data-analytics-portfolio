"""Streamlit smoke checks use conspicuously synthetic fixtures only."""
from pathlib import Path
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from markowitz.data import TICKERS, completed_session, sessions, audit_prices, read_csv

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_empty_state_and_upload_mode():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    assert any('NO HISTORICAL DATA' in e.value for e in at.warning)
    at.sidebar.radio[0].set_value('Upload adjusted-price CSV').run()
    assert not at.exception
    assert any('real historical' in c.label for c in at.checkbox)


def test_live_collection_is_disabled_and_old_cache_cannot_bypass(monkeypatch):
    def forbidden():
        raise AssertionError('No live request without express provider permission')
    monkeypatch.setattr('markowitz.data.download_prices', forbidden)
    at = AppTest.from_file(str(APP))
    at.session_state['live_dataset'] = (pd.DataFrame(), {'vendor': 'previous Yahoo cache'})
    at.run()
    assert not at.exception
    assert at.button[0].disabled
    assert any('YAHOO RIGHTS BLOCKED' in e.value for e in at.warning)
    assert any('NO HISTORICAL DATA' in e.value for e in at.warning)


def uploaded_fixture(prices, monkeypatch, source_review=None):
    """Drive the CSV flow with SYNTHETIC fixtures, never bypass via a live cache."""
    import io
    import json
    import streamlit
    raw = prices.to_csv(index_label='Date').encode()
    prices = read_csv(raw)  # Review binds to the actual parsed upload, not pre-serialization floats.
    _, _, _, summary = audit_prices(prices, as_of=str(prices.index[-1].date()))
    record = source_review(prices, summary) if source_review else None
    def uploader(label, **kwargs):
        if label.startswith('CSV:'):
            return io.BytesIO(raw)
        if record:
            return io.BytesIO(json.dumps(record).encode())
        return None
    monkeypatch.setattr(streamlit, 'file_uploader', uploader)
    if record:
        # Isolate analytical UI with test-only authorization stub; no real licence granted.
        monkeypatch.setattr('markowitz.verification.require_approved_source', lambda record, audit: None)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.sidebar.radio[0].set_value('Upload adjusted-price CSV').run()
    at.text_input[0].set_value('SYNTHETIC TEST ONLY')
    at.text_input[1].set_value(summary['as_of'])
    at.checkbox[0].check().run()
    return at


def test_full_dashboard_validation_then_holdout(source_review, monkeypatch):
    idx = sessions('2016-01-01', completed_session())
    rng = np.random.default_rng(606)
    p = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(.0002, .01, (len(idx), 8)), axis=0)), index=idx, columns=TICKERS)
    at = uploaded_fixture(p, monkeypatch, source_review)
    assert not at.exception
    assert not at.error
    assert any(s.value == 'Validation' for s in at.subheader), [w.value for w in at.warning]
    assert not any(s.value == 'Holdout' for s in at.subheader)
    at.sidebar.checkbox[0].check().run()
    assert not at.exception and not at.error
    assert any(s.value == 'Holdout' for s in at.subheader)


def test_incomplete_data_blocks_financial_results(monkeypatch):
    idx = sessions('2016-01-01', '2016-01-12')
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    p.iloc[3, 0] = np.nan
    at = uploaded_fixture(p, monkeypatch)
    assert not at.exception
    assert any('INCOMPLETE HISTORY' in e.value for e in at.error)
    assert not at.subheader


def test_unverified_source_blocks_performance(monkeypatch):
    idx = sessions('2016-01-01', completed_session())
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    at = uploaded_fixture(p, monkeypatch)
    assert not at.exception and not at.error
    assert any('SOURCE UNVERIFIED' in e.value for e in at.warning)
    assert not at.subheader


def test_uploaded_csv_cutoff_and_analysis_rights_wording():
    at = AppTest.from_file(str(APP)).run()
    at.sidebar.radio[0].set_value('Upload adjusted-price CSV').run()
    assert any('Historical as_of' in t.label for t in at.text_input)
    assert any('authorized to analyze' in c.label for c in at.checkbox)
    assert any('does not establish permission to redistribute' in c.value for c in at.caption)


def test_archived_csv_discloses_staleness_before_review(monkeypatch):
    import io
    import streamlit
    idx = sessions('2016-01-01', '2024-12-31')
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    raw = p.to_csv(index_label='Date').encode()
    monkeypatch.setattr(streamlit, 'file_uploader', lambda label, **kwargs: io.BytesIO(raw) if label.startswith('CSV:') else None)
    at = AppTest.from_file(str(APP)).run()
    at.sidebar.radio[0].set_value('Upload adjusted-price CSV').run()
    at.text_input[0].set_value('SYNTHETIC TEST ONLY')
    at.text_input[1].set_value('2024-12-31')
    at.checkbox[0].check().run()
    assert not at.exception and not at.error
    assert any('HISTORICAL SNAPSHOT' in w.value for w in at.warning)
    assert any('SOURCE UNVERIFIED' in w.value for w in at.warning)
    assert not at.subheader


def test_reveal_disabled_before_sixty_audited_holdout_sessions(monkeypatch, source_review):
    cutoff = sessions('2025-01-01', '2025-04-30')[58]
    monkeypatch.setattr('markowitz.data.completed_session', lambda now=None: cutoff)
    idx = sessions('2016-01-01', cutoff)
    rng = np.random.default_rng(606)
    p = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(.0002, .01, (len(idx), 8)), axis=0)), index=idx, columns=TICKERS)
    _, _, _, audit = audit_prices(p)
    at = uploaded_fixture(p, monkeypatch, source_review)
    assert not at.exception and not at.error
    assert at.sidebar.checkbox[0].disabled
    assert not at.sidebar.checkbox[0].value
    assert not any(s.value == 'Holdout' for s in at.subheader)

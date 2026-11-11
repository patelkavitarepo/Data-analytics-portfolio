"""Streamlit smoke checks use conspicuously synthetic fixtures only."""
from pathlib import Path
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from markowitz.data import TICKERS, completed_session, sessions, audit_prices

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_empty_state_and_upload_mode():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    assert any('NO HISTORICAL DATA' in e.value for e in at.warning)
    at.sidebar.radio[0].set_value('Upload adjusted-price CSV').run()
    assert not at.exception
    assert any('real historical' in c.label for c in at.checkbox)


def test_failed_live_download_warning(monkeypatch):
    monkeypatch.setattr('markowitz.data.download_prices', lambda: (_ for _ in ()).throw(RuntimeError('SYNTHETIC offline failure')))
    at = AppTest.from_file(str(APP)).run()
    at.button[0].click().run()
    assert not at.exception
    assert any('LIVE DATA UNAVAILABLE' in e.value for e in at.error)
    assert any('NO HISTORICAL DATA' in e.value for e in at.warning)


def test_full_dashboard_validation_then_holdout(source_review):
    idx = sessions('2016-01-01', completed_session())
    rng = np.random.default_rng(606)
    p = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(.0002, .01, (len(idx), 8)), axis=0)), index=idx, columns=TICKERS)
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.session_state['live_dataset'] = (p, {'vendor': 'SYNTHETIC TEST FIXTURE — NOT REAL EVIDENCE'})
    _, _, _, summary = audit_prices(p)
    at.session_state['source_review'] = source_review(p, summary)
    at.run()
    assert not at.exception
    assert not at.error
    assert any(s.value == 'Validation' for s in at.subheader)
    assert not any(s.value == 'Holdout' for s in at.subheader)
    at.sidebar.checkbox[0].check().run()
    assert not at.exception and not at.error
    assert any(s.value == 'Holdout' for s in at.subheader)


def test_incomplete_data_blocks_financial_results():
    idx = sessions('2016-01-01', '2016-01-12')
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    at = AppTest.from_file(str(APP))
    at.session_state['live_dataset'] = (p, {'vendor': 'SYNTHETIC TEST FIXTURE'})
    at.run()
    assert not at.exception
    assert any('INCOMPLETE HISTORY' in e.value for e in at.error)
    assert not at.subheader


def test_unverified_source_blocks_performance():
    idx = sessions('2016-01-01', completed_session())
    p = pd.DataFrame(100., index=idx, columns=TICKERS)
    at = AppTest.from_file(str(APP))
    at.session_state['live_dataset'] = (p, {'vendor': 'SYNTHETIC TEST ONLY'})
    at.run()
    assert not at.exception and not at.error
    assert any('SOURCE UNVERIFIED' in e.value for e in at.warning)
    assert not at.subheader


def test_uploaded_csv_cutoff_and_analysis_rights_wording():
    at = AppTest.from_file(str(APP)).run()
    at.sidebar.radio[0].set_value('Upload adjusted-price CSV').run()
    assert any('Historical as_of' in t.label for t in at.text_input)
    assert any('authorized to analyze' in c.label for c in at.checkbox)
    assert any('does not establish permission to redistribute' in c.value for c in at.caption)

"""Streamlit runtime smoke checks; synthetic records used only during tests."""
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def test_empty_start():
    app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert any('Awaiting evidence' in message.value for message in app.info)

def test_loaded_and_empty_filters(monkeypatch):
    from src import analytics
    import pandas as pd
    original = analytics.load_csv
    def synthetic(_):
        return analytics.prepare(pd.DataFrame({'timestamp':[1430000000000,1430000000001,1430000000002], 'visitorid':['test']*3, 'event':['view','addtocart','transaction'],'itemid':['fixture']*3}))
    monkeypatch.setattr(analytics,'load_csv',synthetic)
    # Simulate an uploaded buffer without storing synthetic data in the app.
    import streamlit as st
    class Upload:
        size=10
        def getvalue(self): return b'synthetic-test-only'
    monkeypatch.setattr(st.sidebar,'file_uploader',lambda *a,**k: Upload())
    app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert len(app.dataframe) >= 5
    app.multiselect[0].set_value([]).run()
    assert not app.exception

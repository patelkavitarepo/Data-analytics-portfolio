from pathlib import Path
import json
import socket

from streamlit.testing.v1 import AppTest
from markowitz import synthetic as lab
from markowitz import synthetic_serial as study

PAGE = Path(__file__).resolve().parents[1]/'pages'/'3_Synthetic_serial_dependence.py'


def test_readonly_serial_page_offline_labels(monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('No app-time fit/generation/network')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(lab, 'fit', forbidden)
    monkeypatch.setattr(study, 'run_grid', forbidden)
    monkeypatch.setattr(study, 'training_sample', forbidden)
    at = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not at.exception and at.dataframe
    for frame in at.dataframe:
        assert frame.value.Evidence.eq(lab.WARNING).all()
    for chart in at.get('plotly_chart'):
        assert lab.WARNING in json.loads(chart.proto.spec)['layout']['title']['text']
    assert not at.selectbox and not at.number_input and not at.checkbox and not at.slider
    assert not at.get('file_uploader')


def test_missing_serial_report_no_fallback(monkeypatch):
    def missing(): raise FileNotFoundError('Report absent')
    monkeypatch.setattr(study, 'load_report', missing)
    at = AppTest.from_file(str(PAGE)).run()
    assert not at.exception and not at.dataframe
    assert any('No empirical fallback' in w.value for w in at.warning)

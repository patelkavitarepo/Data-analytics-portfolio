from pathlib import Path
import json
from streamlit.testing.v1 import AppTest
from markowitz.synthetic import WARNING

PAGE = Path(__file__).resolve().parents[1] / 'pages' / '2_Synthetic_robustness_check.py'


def test_read_only_report_offline_labels_and_no_fit_controls(monkeypatch):
    import socket
    from markowitz import synthetic_robustness as study
    from markowitz import synthetic as lab
    def forbidden(*args, **kwargs):
        raise AssertionError('Report page must not fit, bootstrap, run grid or contact providers')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(study, 'run_grid', forbidden)
    monkeypatch.setattr(lab, 'fit', forbidden)
    monkeypatch.setattr(lab, 'bootstrap', forbidden)
    at = AppTest.from_file(str(PAGE), default_timeout=30).run()
    assert not at.exception
    assert at.dataframe
    for table in at.dataframe:
        assert table.value['Evidence'].eq(WARNING).all()
    for chart in at.get('plotly_chart'):
        assert WARNING in json.loads(chart.proto.spec)['layout']['title']['text']
    assert not at.selectbox and not at.slider and not at.checkbox and not at.number_input
    assert not at.get('file_uploader')


def test_missing_report_is_explicit_no_fallback(monkeypatch):
    from markowitz import synthetic_robustness as study
    def missing():
        raise FileNotFoundError('SYNTHETIC report missing')
    monkeypatch.setattr(study, 'load_report', missing)
    at = AppTest.from_file(str(PAGE)).run()
    assert not at.exception
    assert not at.dataframe
    assert any('No empirical fallback' in warning.value for warning in at.warning)

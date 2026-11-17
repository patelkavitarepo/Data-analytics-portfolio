from pathlib import Path
import json

from streamlit.testing.v1 import AppTest
from markowitz.synthetic import WARNING

PAGE = Path(__file__).resolve().parents[1] / 'pages' / '1_Synthetic_scenario_lab.py'


def test_synthetic_page_works_offline_and_every_chart_table_is_labeled(monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError('No network permitted in synthetic page')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    assert any(WARNING in e.value for e in at.error)
    assert not at.dataframe  # No fabricated market fallback or unsolicited run.
    at.slider[0].set_value(2)
    at.button[0].click().run()
    assert not at.exception
    assert at.dataframe
    for table in at.dataframe:
        assert table.value['Evidence'].eq(WARNING).all()
    for chart in at.get('plotly_chart'):
        spec = json.loads(chart.proto.spec)
        assert WARNING in spec['layout']['title']['text']
    assert at.session_state['synthetic_result'][2]['manifest']['bootstrap']['draws'] == 2
    assert not at.get('file_uploader') and not at.checkbox  # No source upload or real holdout control.


def test_synthetic_solver_failure_visible_in_page(monkeypatch):
    from markowitz import synthetic
    original = synthetic.optimize
    def fail(mu, cov, cap, objective, annual_rf):
        if objective == 'max_sharpe':
            raise ValueError('SYNTHETIC forced failure')
        return original(mu, cov, cap, objective, annual_rf)
    monkeypatch.setattr(synthetic, 'optimize', fail)
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    # Different seed avoids reusing the successful cached experiment in the other test.
    at.number_input[0].set_value(60607)
    at.slider[0].set_value(2)
    at.button[0].click().run()
    assert not at.exception
    assert any('Failed fitted candidates omitted' in w.value for w in at.warning)
    assert 'max_sharpe' not in at.session_state['synthetic_result'][2]['weights']

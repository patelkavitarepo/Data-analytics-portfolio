import json
import pytest
from markowitz import run


def test_archived_csv_requires_explicit_cutoff(monkeypatch):
    monkeypatch.setattr('sys.argv', ['run', '--csv', 'unused.csv', '--source', 'SYNTHETIC'])
    with pytest.raises(SystemExit, match='2'):
        run.main()


def test_cli_audits_archived_snapshot_but_cannot_evaluate_unverified_source(historical_returns, tmp_path, monkeypatch):
    p = 100 * (1 + historical_returns.loc[:'2024']).cumprod()
    source = tmp_path / 'SYNTHETIC.csv'
    p.to_csv(source, index_label='Date')
    out = tmp_path / 'audit'
    monkeypatch.setattr('sys.argv', ['run', '--csv', str(source), '--source', 'SYNTHETIC TEST ONLY',
                                  '--as-of', '2024-12-31', '--output', str(out)])
    def forbidden(*args, **kwargs):
        pytest.fail('No performance before independent review')
    monkeypatch.setattr(run, 'evaluate_validation', forbidden)
    with pytest.raises(SystemExit, match='SOURCE UNVERIFIED'):
        run.main()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['as_of'] == '2024-12-31'
    assert manifest['quality']['lost_price_rows'] == 0
    assert not manifest['holdout_revealed']
    assert (out / 'source_review_template.json').exists()
    assert not list(out.glob('*metrics*'))

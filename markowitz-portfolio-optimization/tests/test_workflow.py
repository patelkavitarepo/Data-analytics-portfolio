import io
import json
import urllib.error
from scripts import network_probe, source_audit
from markowitz.data import audit_prices


class StatusOnlyResponse:
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, *args):
        raise AssertionError('Probe must never read vendor body')


class Opener:
    def __init__(self, failure=None):
        self.failure = failure
    def open(self, request, timeout):
        assert timeout == 15
        assert request.get_header('Authorization') is None
        if self.failure:
            raise self.failure
        return StatusOnlyResponse()


def test_connectivity_probe_logs_only_status_and_sanitizes_failures():
    assert network_probe.probe('example', 'https://example.com', Opener()) == {
        'host': 'example', 'http_status': 200, 'transport': 'http_response'}
    error = urllib.error.HTTPError('https://example.com', 429, 'do not print', {}, io.BytesIO(b'VENDOR BODY'))
    result = network_probe.probe('example', 'https://example.com', Opener(error))
    assert result['http_status'] == 429 and 'VENDOR' not in str(result)
    result = network_probe.probe('example', 'https://example.com', Opener(TimeoutError('SECRET')))
    assert result['transport'] == 'TimeoutError' and 'SECRET' not in str(result)


def test_source_audit_reports_coverage_not_prices_or_performance(historical_returns, monkeypatch, capsys):
    p = 100 * (1 + historical_returns).cumprod()
    _, _, _, summary = audit_prices(p, as_of=str(p.index[-1].date()))
    monkeypatch.setattr(source_audit, 'download_prices', lambda: (p, {'vendor': 'SYNTHETIC TEST', 'adjustment': 'TEST ONLY'}))
    monkeypatch.setattr(source_audit, 'audit_prices', lambda data: audit_prices(data, as_of=str(data.index[-1].date())))
    assert source_audit.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result['all_eight_etfs_present']
    assert result['audit']['common_prices'] == len(p)
    assert result['validation_performance'] == result['holdout_performance'] == 'NOT COMPUTED'
    assert 'reference_price' not in str(result)


def test_source_audit_failure_is_not_green_or_raw_vendor_output(monkeypatch, capsys):
    def fail():
        print('VENDOR BODY')
        raise RuntimeError('SECRET vendor diagnostic')
    monkeypatch.setattr(source_audit, 'download_prices', fail)
    assert source_audit.main() == 1
    result = capsys.readouterr().out
    assert 'VENDOR BODY' not in result and 'SECRET' not in result
    assert json.loads(result)['failure_stage'] == 'acquisition'

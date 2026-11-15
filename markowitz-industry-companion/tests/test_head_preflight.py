"""HEAD-only checks use fake responses and handlers, never a source connection."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import urllib.error
import urllib.request

import pytest

from industry_companion import actions_audit as actions
from industry_companion import head_preflight as head
from industry_companion.parser import DataError
from industry_companion.safeguards import SOURCE_URL
from test_actions_audit import context as live_context


class HostileResponse:
    """Any access to source content/headers fails the test immediately."""
    def __init__(self, status):
        self.status = status
        self.closed = False
    @property
    def headers(self):
        raise AssertionError('PRIVATEPOISON headers/cookies must not be inspected')
    def read(self, *args, **kwargs):
        raise AssertionError('No HEAD response body may be consumed')
    def readline(self, *args, **kwargs):
        raise AssertionError('No HEAD response body may be consumed')
    def getheader(self, *args, **kwargs):
        raise AssertionError('No header dump or cookie inspection')
    def info(self):
        raise AssertionError('No header dump or cookie inspection')
    def close(self):
        self.closed = True
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def assert_coarse(report, expected):
    assert set(report) == {'result', 'checked_at_utc'}
    assert report['result'] == expected
    checked = datetime.fromisoformat(report['checked_at_utc'].replace('Z', '+00:00'))
    assert checked.utcoffset() == timedelta(0)
    serialized = json.dumps(report)
    assert all(token not in serialized for token in (
        'PRIVATEPOISON', 'sender@', '127.0.0.1', '/private/', 'cookie', 'archive_sha256',
        'coverage_complete', 'point_in_time_verified', 'performance_cleared'))


def mock_opener(monkeypatch, *, status=200, error=None):
    calls = []
    response = HostileResponse(status)
    class Opener:
        def open(self, request, timeout):
            calls.append((request.get_method(), request.full_url, request.data, timeout))
            if error is not None:
                raise error
            return response
    def build(*handlers):
        assert any(isinstance(handler, head._HeadStatusOnly) for handler in handlers)
        return Opener()
    monkeypatch.setattr(urllib.request, 'build_opener', build)
    return calls, response


@pytest.mark.parametrize('status', [200, 204, 206, 299])
def test_head_2xx_has_no_body_headers_or_files(monkeypatch, tmp_path, capsys, status):
    monkeypatch.chdir(tmp_path)
    calls, response = mock_opener(monkeypatch, status=status)
    assert_coarse(head.check_connectivity(), 'REACHABLE_HEAD_2XX')
    assert calls == [('HEAD', SOURCE_URL, None, 20)]
    assert response.closed and list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ('', '')


@pytest.mark.parametrize('status', [301, 302, 303, 307, 308, 403, 404, 405, 500])
def test_non_2xx_is_inconclusive_without_redirect_retry_or_get(monkeypatch, status):
    calls, response = mock_opener(monkeypatch, status=status)
    assert_coarse(head.check_connectivity(), 'HEAD_UNSUPPORTED_OR_NON_2XX')
    assert calls == [('HEAD', SOURCE_URL, None, 20)]
    assert response.closed


@pytest.mark.parametrize('error', [
    TimeoutError('PRIVATEPOISON timeout /private/data'),
    OSError('PRIVATEPOISON proxy=http://sender@example.invalid:secret 127.0.0.1'),
    urllib.error.URLError('PRIVATEPOISON private network diagnostic'),
])
def test_network_failures_are_coarse_and_redacted(monkeypatch, capsys, error):
    calls, _response = mock_opener(monkeypatch, error=error)
    assert_coarse(head.check_connectivity(), 'BLOCKED_OR_UNAVAILABLE')
    assert calls == [('HEAD', SOURCE_URL, None, 20)]
    assert capsys.readouterr() == ('', '')


@pytest.mark.parametrize('status', [301, 403, 405])
def test_http_errors_do_not_echo_or_read_body(monkeypatch, status):
    body = HostileResponse(status)
    error = urllib.error.HTTPError(SOURCE_URL, status, 'PRIVATEPOISON response message', {}, body)
    calls, _response = mock_opener(monkeypatch, error=error)
    assert_coarse(head.check_connectivity(), 'HEAD_UNSUPPORTED_OR_NON_2XX')
    assert calls == [('HEAD', SOURCE_URL, None, 20)]
    assert body.closed


@pytest.mark.parametrize('mutation', ['get', 'wrong_url', 'request_body'])
def test_changed_request_is_rejected_before_preparing_connection(monkeypatch, mutation):
    original_request = urllib.request.Request
    calls = []
    def changed_request(url, *, method):
        assert url == SOURCE_URL and method == 'HEAD'
        if mutation == 'get':
            return original_request(url, method='GET')
        if mutation == 'wrong_url':
            return original_request('https://example.invalid/mirror.zip', method=method)
        return original_request(url, data=b'INVENTED REQUEST BODY', method=method)
    monkeypatch.setattr(urllib.request, 'Request', changed_request)
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: calls.append(args))
    assert_coarse(head.check_connectivity(), 'BLOCKED_OR_UNAVAILABLE')
    assert calls == []


@pytest.mark.parametrize('status', [301, 302, 303, 307, 308, 403, 405])
def test_real_urllib_processing_never_follows_or_drains_fake_response(monkeypatch, status):
    original_build = urllib.request.build_opener
    calls = []
    response = HostileResponse(status)
    class SyntheticHTTPS(urllib.request.HTTPSHandler):
        def https_open(self, request):
            calls.append((request.get_method(), request.full_url, request.timeout))
            return response
    class NoRedirectInspection(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise AssertionError('Redirect processing must never run')
        def http_error_302(self, *args, **kwargs):
            raise AssertionError('Redirect processing must never inspect headers or drain body')
        http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302
    def build(*handlers):
        return original_build(urllib.request.ProxyHandler({}), SyntheticHTTPS(), NoRedirectInspection(), *handlers)
    monkeypatch.setattr(urllib.request, 'build_opener', build)
    assert_coarse(head.check_connectivity(), 'HEAD_UNSUPPORTED_OR_NON_2XX')
    assert calls == [('HEAD', SOURCE_URL, 20)]
    assert response.closed


@pytest.mark.parametrize('processor', ['http_response', 'https_response'])
def test_status_processor_refuses_an_accidental_get(processor):
    request = urllib.request.Request(SOURCE_URL, method='GET')
    response = HostileResponse(200)
    with pytest.raises(DataError):
        getattr(head._HeadStatusOnly(), processor)(request, response)


def head_context():
    values = live_context()
    values.update(HEAD_ONLY_ACK='true', PERMISSION_ACTIVE_ACK='',
                  EPHEMERAL_PROCESSING_ACK='', HOSTED_PROCESSING_ENABLED='')
    return values


@pytest.fixture
def authorized_context(monkeypatch):
    monkeypatch.setattr(actions, '_verify_running_revision', lambda context: None)
    monkeypatch.setattr(actions.faulthandler, 'is_enabled', lambda: False)
    return head_context()


def test_head_requires_no_raw_scope_approval(monkeypatch, authorized_context):
    calls, _response = mock_opener(monkeypatch)
    def forbidden(*args, **kwargs):
        raise AssertionError('HEAD cannot invoke source parsing or raw processing')
    monkeypatch.setattr(actions, 'parse_archive', forbidden)
    monkeypatch.setattr(actions, 'execute_live', forbidden)
    assert_coarse(actions.execute_head(authorized_context), 'REACHABLE_HEAD_2XX')
    assert calls == [('HEAD', SOURCE_URL, None, 20)]
    policy = json.loads((Path(actions.__file__).resolve().parents[1] / 'github_actions_scope.json').read_text())
    assert policy['status'] == 'pending_owner_rights_review' and policy['live_enabled'] is False


@pytest.mark.parametrize('key,value', [
    ('GITHUB_ACTIONS', 'false'), ('GITHUB_EVENT_NAME', 'pull_request'),
    ('GITHUB_EVENT_NAME', 'push'), ('GITHUB_EVENT_NAME', 'schedule'),
    ('GITHUB_REPOSITORY', 'elsewhere/project'), ('GITHUB_REF', 'refs/heads/main'),
    ('GITHUB_ACTOR', 'someone'), ('GITHUB_TRIGGERING_ACTOR', 'someone'),
    ('GITHUB_RUN_ATTEMPT', '2'), ('RUNNER_ENVIRONMENT', 'self-hosted'),
    ('REVIEWED_CODE_SHA', 'main'), ('AUDIT_CODE_SHA_INPUT', 'b' * 40),
    ('HEAD_ONLY_ACK', 'false'), ('HEAD_ONLY_ACK', ''), ('HEAD_ONLY_ACK', True),
    ('ACTIONS_STEP_DEBUG', 'true'), ('ACTIONS_RUNNER_DEBUG', 'true'), ('RUNNER_DEBUG', '1'),
])
def test_invalid_head_context_never_prepares_network(monkeypatch, authorized_context, key, value):
    calls = []
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: calls.append(args))
    with pytest.raises(DataError):
        actions.execute_head(dict(authorized_context, **{key: value}))
    assert calls == []


def test_head_revision_failure_precedes_network(monkeypatch, authorized_context):
    def reject(_context):
        raise DataError('CODE_REVISION_UNVERIFIED')
    monkeypatch.setattr(actions, '_verify_running_revision', reject)
    calls = []
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: calls.append(args))
    with pytest.raises(DataError, match='CODE_REVISION_UNVERIFIED'):
        actions.execute_head(authorized_context)
    assert calls == []


def test_enabled_fault_handler_blocks_head_before_network(monkeypatch, authorized_context):
    calls = []
    monkeypatch.setattr(actions.faulthandler, 'is_enabled', lambda: True)
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: calls.append(args))
    with pytest.raises(DataError, match='DEBUG_LOGGING_FORBIDDEN'):
        actions.execute_head(authorized_context)
    assert calls == []


def test_cli_head_is_coarse_only_with_raw_gate_still_closed(monkeypatch, authorized_context, capsys):
    for key, value in authorized_context.items():
        monkeypatch.setenv(key, value)
    calls, _response = mock_opener(monkeypatch, status=405)
    def forbidden(*args, **kwargs):
        raise AssertionError('HEAD must not load a raw scope policy, parse or acquire')
    monkeypatch.setattr(actions, 'parse_archive', forbidden)
    monkeypatch.setattr(actions, 'execute_live', forbidden)
    monkeypatch.setattr(Path, 'read_text', forbidden)
    assert actions.main(['--mode', 'head']) == 0
    captured = capsys.readouterr()
    assert captured.err == ''
    assert_coarse(json.loads(captured.out), 'HEAD_UNSUPPORTED_OR_NON_2XX')
    assert calls == [('HEAD', SOURCE_URL, None, 20)]

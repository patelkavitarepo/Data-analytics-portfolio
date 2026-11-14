"""Hosted-workflow controls tested with invented format bytes only; no live HTTP."""
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
import urllib.request

import pytest

from industry_companion import actions_audit as actions
from industry_companion.parser import DataError, MAX_ARCHIVE
from industry_companion.safeguards import SCOPE, SOURCE_URL
from test_parser import text, zipped


SHA = 'a' * 40
VERIFY_REVISION = actions._verify_running_revision


def context():
    return dict(GITHUB_ACTIONS='true', GITHUB_EVENT_NAME='workflow_dispatch',
        GITHUB_REPOSITORY='patelkavitarepo/Data-analytics-portfolio',
        GITHUB_REF='refs/heads/project-006-french-industry-ingestion',
        GITHUB_ACTOR='patelkavitarepo', GITHUB_TRIGGERING_ACTOR='patelkavitarepo',
        GITHUB_RUN_ATTEMPT='1', RUNNER_ENVIRONMENT='github-hosted',
        REVIEWED_CODE_SHA=SHA, AUDIT_CODE_SHA_INPUT=SHA,
        PERMISSION_ACTIVE_ACK='true', EPHEMERAL_PROCESSING_ACK='true',
        HOSTED_PROCESSING_ENABLED='true')


def policy():
    # Invented approval metadata solely for negative/positive unit tests.
    # The committed real hosted-processing policy remains pending, not approved.
    return dict(schema_version=1, dataset_scope=SCOPE, source_url=SOURCE_URL,
        status='approved_github_hosted_ephemeral_processing', live_enabled=True,
        github_hosted_ephemeral_processing=True, raw_redistribution=False,
        rescission_possible=True,
        evidence_reference='https://github.com/patelkavitarepo/Data-analytics-portfolio/issues/11#issuecomment-123')


@pytest.fixture(autouse=True)
def synthetic_revision_only(monkeypatch):
    monkeypatch.setattr(actions, '_verify_running_revision', lambda context: None)
    # pytest enables its own fault handler; a real live worker rejects that mode.
    monkeypatch.setattr(actions.faulthandler, 'is_enabled', lambda: False)


def assert_safe_code(exc):
    assert re.fullmatch(r'[A-Z][A-Z0-9_]+', str(exc.value))
    assert all(token not in str(exc.value) for token in ('PRIVATEPOISON', 'sender@', 'https://', '/private/'))


def test_explicit_reviewed_context_is_accepted():
    actions.validate_live_context(context(), policy())


@pytest.mark.parametrize('key,value', [
    ('GITHUB_ACTIONS', 'false'), ('GITHUB_EVENT_NAME', 'push'),
    ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_EVENT_NAME', 'schedule'),
    ('GITHUB_REPOSITORY', 'elsewhere/project'),
    ('GITHUB_REF', 'refs/heads/main'), ('GITHUB_REF', 'refs/tags/release'),
    ('GITHUB_ACTOR', 'someone-else'), ('GITHUB_TRIGGERING_ACTOR', 'someone-else'),
    ('GITHUB_RUN_ATTEMPT', '2'), ('RUNNER_ENVIRONMENT', 'self-hosted'),
    ('REVIEWED_CODE_SHA', 'main'), ('AUDIT_CODE_SHA_INPUT', 'b' * 40),
    ('PERMISSION_ACTIVE_ACK', 'false'), ('EPHEMERAL_PROCESSING_ACK', 'false'),
    ('HOSTED_PROCESSING_ENABLED', 'false'), ('HOSTED_PROCESSING_ENABLED', ''),
    ('HOSTED_PROCESSING_ENABLED', 'true\nPRIVATEPOISON'),
    ('HOSTED_PROCESSING_ENABLED', True),
    ('ACTIONS_STEP_DEBUG', 'true'), ('ACTIONS_RUNNER_DEBUG', 'true'),
    ('RUNNER_DEBUG', '1'),
])
def test_context_failures_precede_http(monkeypatch, key, value):
    called = []
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: called.append(args))
    invalid = dict(context(), **{key: value})
    with pytest.raises(DataError) as exc:
        actions.execute_live(invalid, policy())
    assert_safe_code(exc)
    assert called == []


@pytest.mark.parametrize('key,value', [
    ('schema_version', 2), ('dataset_scope', 'all finance data'),
    ('source_url', 'https://example.invalid/mirror.zip'),
    ('status', 'pending_owner_rights_review'), ('status', 'revoked'),
    ('live_enabled', False), ('live_enabled', 1),
    ('github_hosted_ephemeral_processing', False),
    ('github_hosted_ephemeral_processing', 1),
    ('raw_redistribution', True), ('rescission_possible', False),
    ('evidence_reference', None), ('evidence_reference', ''),
])
def test_permission_scope_failures_precede_http(monkeypatch, key, value):
    called = []
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: called.append(args))
    invalid = dict(policy(), **{key: value})
    with pytest.raises(DataError) as exc:
        actions.execute_live(context(), invalid)
    assert_safe_code(exc)
    assert called == []


def test_revision_verification_is_not_replaced_by_acknowledgement(monkeypatch):
    def fail_revision(_context):
        raise DataError('CODE_REVISION_UNVERIFIED')
    monkeypatch.setattr(actions, '_verify_running_revision', fail_revision)
    with pytest.raises(DataError, match='CODE_REVISION_UNVERIFIED'):
        actions.validate_live_context(context(), policy())


def test_fault_handler_blocks_before_http(monkeypatch):
    called = []
    monkeypatch.setattr(actions.faulthandler, 'is_enabled', lambda: True)
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: called.append(args))
    with pytest.raises(DataError, match='DEBUG_LOGGING_FORBIDDEN'):
        actions.execute_live(context(), policy())
    assert called == []


@pytest.mark.parametrize('head,dirty', [(SHA, 0), ('b' * 40, 0), (SHA, 1), (SHA, 128)])
def test_actual_revision_verifier_checks_head_and_tracked_scope(monkeypatch, head, dirty):
    calls = []
    def fake_run(command, **kwargs):
        assert kwargs['capture_output'] is True
        calls.append(command)
        if 'rev-parse' in command: return SimpleNamespace(stdout=head + '\n')
        return SimpleNamespace(returncode=dirty)
    monkeypatch.setattr(actions.subprocess, 'run', fake_run)
    if head == SHA and dirty == 0:
        VERIFY_REVISION(context())
    else:
        with pytest.raises(DataError, match='CODE_REVISION_UNVERIFIED'):
            VERIFY_REVISION(context())
    assert calls[0][-2:] == ['rev-parse', 'HEAD']
    assert calls[1][-3:] == ['industry_companion', 'github_actions_scope.json', 'requirements-lock.txt']


def test_actual_revision_verifier_redacts_git_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('PRIVATEPOISON /private/file sender@example.invalid')
    monkeypatch.setattr(actions.subprocess, 'run', fail)
    with pytest.raises(DataError) as exc:
        VERIFY_REVISION(context())
    assert str(exc.value) == 'CODE_REVISION_UNVERIFIED'


def test_ephemeral_buffer_fingerprint_no_files_and_close(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = zipped(text())
    store = actions.EphemeralStore(context(), policy())
    with pytest.raises(DataError):
        store.snapshot(data, retrieved_at_utc='2026-11-14T00:00:00Z')
    digest = store.snapshot(data, retrieved_at_utc='2026-11-14T00:00:00Z', permission_active=True)
    restored, manifest = store.load_snapshot(digest, permission_active=True)
    assert digest == hashlib.sha256(data).hexdigest() and restored == data
    assert manifest['source_url'] == SOURCE_URL
    assert manifest['acquisition_method'] == 'bounded_direct_https'
    assert manifest['performance_cleared'] is False
    assert list(tmp_path.iterdir()) == []
    assert '0.0125' not in repr(store) and 'PRIVATEPOISON' not in repr(store)
    with pytest.raises(DataError):
        store.load_snapshot('b' * 64, permission_active=True)
    store.close()
    def retains_payload(value):
        if isinstance(value, bytes): return value == data
        if isinstance(value, dict): return any(retains_payload(item) for item in value.values())
        if isinstance(value, (tuple, list)): return any(retains_payload(item) for item in value)
        return False
    assert not retains_payload(vars(store))
    with pytest.raises(DataError):
        store.load_snapshot(digest, permission_active=True)
    assert list(tmp_path.iterdir()) == []


def install_fake_opener(monkeypatch, *, on_read=None, payload=None):
    payload = zipped(text()) if payload is None else payload
    calls = []
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size):
            calls.append(('read', size))
            if on_read: on_read()
            return payload
    class Opener:
        def open(self, request, timeout):
            calls.append(('request', request.full_url, timeout))
            return Response()
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: Opener())
    return calls


def test_mocked_live_single_request_metadata_only_and_no_disk(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    poison = '20250101,returns in decimals,NaN,PRIVATEPOISON'
    payload = zipped(text(vw=['20160104,' + ','.join(['1.25'] * 10), poison]))
    calls = install_fake_opener(monkeypatch, payload=payload)
    report = actions.execute_live(context(), policy())
    assert calls == [('request', SOURCE_URL, 20), ('read', MAX_ARCHIVE + 1)]
    assert report['evidence_kind'] == 'authorized_live_coverage_audit'
    assert report['archive_sha256'] == hashlib.sha256(payload).hexdigest()
    assert report['point_in_time_verified'] is False and report['performance_cleared'] is False
    assert report['out_of_scope_rows_excluded'] is True
    assert report['panels']['value_weighted']['development_rows'] == 1
    assert report['panels']['equal_weighted']['development_rows'] == 2
    output = json.dumps(report)
    assert all(token not in output for token in ('PRIVATEPOISON', '0.0125', '-0.025', '2025-01-01'))
    assert all(key not in report for key in ('returns', 'weights', 'wealth', 'CAGR', 'Sharpe'))
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr().out == ''


def test_in_flight_permission_change_prevents_snapshot(monkeypatch):
    scope = policy()
    install_fake_opener(monkeypatch, on_read=lambda: scope.update(status='revoked'))
    created = []
    original = actions.EphemeralStore
    class Tracked(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created.append(self)
    monkeypatch.setattr(actions, 'EphemeralStore', Tracked)
    with pytest.raises(DataError):
        actions.execute_live(context(), scope)
    assert created
    for store in created:
        with pytest.raises(DataError):
            store.load_snapshot('a' * 64, permission_active=True)


def test_network_failure_never_echoes_underlying_exception(monkeypatch, capsys):
    class Opener:
        def open(self, *args, **kwargs):
            raise OSError('PRIVATEPOISON sender@example.invalid /private/file.zip HTTP body')
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: Opener())
    with pytest.raises(DataError) as exc:
        actions.execute_live(context(), policy())
    assert str(exc.value) == 'SOURCE_CONNECTION_BLOCKED_OR_UNAVAILABLE'
    assert capsys.readouterr().out == ''


def test_synthetic_mode_is_deterministic_metadata_only(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError('Synthetic mode must never prepare HTTP')
    monkeypatch.setattr(urllib.request, 'build_opener', forbidden)
    first, second = actions.execute_synthetic(), actions.execute_synthetic()
    assert first['evidence_kind'] == second['evidence_kind'] == 'synthetic_format_fixture'
    assert first['archive_sha256'] == second['archive_sha256']
    assert first['member_sha256'] == second['member_sha256']
    assert first['coverage_complete'] is False
    assert first['point_in_time_verified'] is False and first['performance_cleared'] is False
    assert set(first['panels']) == {'value_weighted', 'equal_weighted'}
    assert first['scope']['start'] == '2016-01-01' and first['scope']['end'] == '2024-12-31'
    assert all(key not in first for key in ('returns', 'weights', 'wealth', 'CAGR', 'Sharpe'))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('mode', ['synthetic', 'live'])
@pytest.mark.parametrize('location', ['top', 'panel'])
def test_unexpected_output_fields_fail_before_publication(monkeypatch, capsys, mode, location):
    original_audit = actions.audit_dataset
    def unsafe_audit(*args, **kwargs):
        report = original_audit(*args, **kwargs)
        if location == 'top': report['returns'] = ['PRIVATEPOISON']
        else: report['panels']['value_weighted']['returns'] = ['PRIVATEPOISON']
        return report
    monkeypatch.setattr(actions, 'audit_dataset', unsafe_audit)
    if mode == 'live':
        install_fake_opener(monkeypatch)
        run = lambda: actions.execute_live(context(), policy())
    else:
        run = actions.execute_synthetic
    with pytest.raises(DataError, match='UNSAFE_AUDIT_OUTPUT'):
        run()
    output = capsys.readouterr()
    assert output.out == output.err == ''


def test_cli_output_schema_failure_redacts_injected_values(monkeypatch, capsys):
    original_audit = actions.audit_dataset
    def unsafe_audit(*args, **kwargs):
        report = original_audit(*args, **kwargs)
        report['returns'] = ['PRIVATEPOISON']
        return report
    monkeypatch.setattr(actions, 'audit_dataset', unsafe_audit)
    assert actions.main([]) == 1
    output = capsys.readouterr()
    assert output.err == '' and 'PRIVATEPOISON' not in output.out
    assert json.loads(output.out)['code'] == 'UNSAFE_AUDIT_OUTPUT'


def test_cli_defaults_to_synthetic_not_live(capsys, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Default mode must never prepare HTTP')
    monkeypatch.setattr(urllib.request, 'build_opener', forbidden)
    assert actions.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['evidence_kind'] == 'synthetic_format_fixture'


def test_committed_policy_keeps_cli_live_closed(monkeypatch, capsys):
    for key, value in context().items(): monkeypatch.setenv(key, value)
    called = []
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: called.append(args))
    assert actions.main(['--mode', 'live']) == 1
    report = json.loads(capsys.readouterr().out)
    assert report['status'] == 'blocked' and report['performance_cleared'] is False
    assert called == []
    source = Path(actions.__file__).resolve().parents[1] / 'github_actions_scope.json'
    committed = json.loads(source.read_text())
    assert committed['status'] == 'pending_owner_rights_review'
    assert committed['live_enabled'] is False


def test_cli_arbitrary_failures_and_arguments_are_redacted(monkeypatch, capsys):
    def fail():
        raise RuntimeError('PRIVATEPOISON /private/file sender@example.invalid raw 1.25')
    monkeypatch.setattr(actions, 'execute_synthetic', fail)
    assert actions.main([]) == 1
    output = capsys.readouterr()
    assert output.err == ''
    assert all(token not in output.out for token in ('PRIVATEPOISON', '/private/', 'sender@', '1.25', 'Traceback'))
    assert json.loads(output.out)['status'] == 'blocked'
    assert actions.main(['--not-allowed', 'PRIVATEPOISON']) == 1
    output = capsys.readouterr()
    assert 'PRIVATEPOISON' not in output.out + output.err

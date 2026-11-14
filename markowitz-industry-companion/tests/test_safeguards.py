"""Synthetic metadata/container fixtures only; no provider or permission inquiry calls."""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import urllib.request
import zipfile

import pytest

from industry_companion import acquire, safeguards
from industry_companion.parser import DataError, MAX_ARCHIVE
from industry_companion.safeguards import PrivateStore, SCOPE, SOURCE_URL


UTC_STAMP = '2001-01-02T03:04:05+00:00'


def git(project, *args):
    return subprocess.run(['git', '-C', str(project), *args], capture_output=True, text=True, check=True)


@pytest.fixture
def store(tmp_path):
    project = tmp_path/'invented-project'
    project.mkdir(mode=0o700)
    git(project, 'init', '-q')
    (project/'.gitignore').write_text('private/\n*.zip\n')
    return PrivateStore(project)


def receipt(**changes):
    value = dict(status='active', scope=SCOPE, recorded_at_utc=UTC_STAMP,
        limited_automation=True, private_retention=True, educational_analysis=True,
        aggregate_publication=True, raw_redistribution=False, rescission_possible=True,
        evidence_reference='SYNTHETIC OWNER METADATA ONLY; not an actual permission')
    value.update(changes)
    return value


def activate(store, **changes):
    store.write_json('permission-receipt.json', receipt(**changes))


def archive_bytes():
    data = io.BytesIO()
    member = zipfile.ZipInfo('10_Industry_Portfolios_Daily.csv', date_time=(2000,1,1,0,0,0))
    with zipfile.ZipFile(data, 'w', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(member, b'SYNTHETIC FORMAT CONTAINER ONLY; no real observations\n')
    return data.getvalue()


def test_private_path_requires_git_ignore_and_excludes_tracked_files(store):
    path = store.write('fixture.txt', b'SYNTHETIC PRIVATE FIXTURE')
    assert git(store.project, 'check-ignore', '--', str(path)).returncode == 0
    assert git(store.project, 'ls-files', '--', 'private').stdout == ''
    # A forced tracked file must be rejected even when its directory is ignored.
    git(store.project, 'add', '-f', '--', str(path))
    with pytest.raises(DataError, match='PRIVATE_(PATH_NOT_IGNORED|FILE_TRACKED)'):
        store.read(path.name)
    git(store.project, 'reset', '-q', '--', str(path))
    (store.project/'.gitignore').write_text('')
    with pytest.raises(DataError, match='PRIVATE_PATH_NOT_IGNORED'):
        store.path('new.txt')


def test_private_permissions_and_immutable_writes(store):
    path = store.write('fixture.txt', b'SYNTHETIC BYTES')
    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert store.read(path.name) == b'SYNTHETIC BYTES'
    with pytest.raises(DataError, match='IMMUTABLE_FILE_EXISTS'):
        store.write(path.name, b'DIFFERENT SYNTHETIC BYTES')
    assert path.read_bytes() == b'SYNTHETIC BYTES'
    path.chmod(0o644)
    with pytest.raises(DataError, match='PRIVATE_FILE_PERMISSIONS'):
        store.read(path.name)
    path.chmod(0o600)
    store.root.chmod(0o755)
    with pytest.raises(DataError, match='PRIVATE_DIRECTORY_PERMISSIONS'):
        store.path(path.name)


@pytest.mark.parametrize('name', ['../outside.zip','/tmp/outside.zip','nested/file.zip',
    '..', '.', 'UPPER.zip', 'with space.zip', 'x\\y.zip', '', None])
def test_private_names_block_traversal_and_unsafe_forms(store, name):
    with pytest.raises(DataError, match='PRIVATE_NAME_REQUIRED|PRIVATE_SYMLINK'):
        store.path(name, create=True)


def test_private_root_project_and_file_symlinks_are_rejected(store, tmp_path):
    outside = tmp_path/'outside'
    outside.mkdir(mode=0o700)
    store.root.symlink_to(outside, target_is_directory=True)
    with pytest.raises(DataError, match='PRIVATE_SYMLINK'):
        store.path('fixture.txt')
    store.root.unlink()
    store.write('normal.txt', b'SYNTHETIC')
    other = outside/'other.txt'
    other.write_text('SYNTHETIC EXTERNAL FILE')
    (store.root/'link.txt').symlink_to(other)
    with pytest.raises(DataError, match='PRIVATE_SYMLINK'):
        store.read('link.txt')
    alias = tmp_path/'alias'
    alias.symlink_to(store.project, target_is_directory=True)
    with pytest.raises(DataError, match='PRIVATE_SYMLINK'):
        PrivateStore(alias).path('normal.txt')


def test_non_git_project_is_not_accepted(tmp_path):
    project = tmp_path/'not-git'
    project.mkdir(mode=0o700)
    with pytest.raises(DataError, match='PRIVATE_PATH_NOT_IGNORED'):
        PrivateStore(project).write('fixture.txt', b'SYNTHETIC')


@pytest.mark.parametrize('value', [None, '', '2001-01-02T03:04:05',
    '2001-01-02T03:04:05+01:00', 'PRIVATE RAW HEADER/ROW MUST NOT APPEAR'])
def test_utc_errors_are_safe_and_reject_non_utc(value):
    with pytest.raises(DataError) as error:
        safeguards.utc(value)
    assert str(error.value) == 'UTC_TIMESTAMP_REQUIRED'
    assert safeguards.utc(UTC_STAMP).utcoffset().total_seconds() == 0


def test_permission_requires_explicit_current_attestation_and_local_receipt(store):
    with pytest.raises(DataError, match='CURRENT_PERMISSION_ATTESTATION_REQUIRED'):
        store.gate()
    activate(store)
    with pytest.raises(DataError, match='CURRENT_PERMISSION_ATTESTATION_REQUIRED'):
        store.gate(permission_active=False)
    assert store.gate(permission_active=True)['scope'] == SCOPE


@pytest.mark.parametrize('changes', [dict(status='revoked'), dict(status='unknown'),
    dict(scope='ETF prices'), dict(limited_automation=False), dict(private_retention=False),
    dict(educational_analysis=False), dict(aggregate_publication=False),
    dict(raw_redistribution=True), dict(rescission_possible=False)])
def test_permission_unknown_revoked_wrong_scope_or_missing_rights_fail_closed(store, changes):
    activate(store, **changes)
    with pytest.raises(DataError, match='PERMISSION_NOT_ACTIVE_FOR_SCOPE|PERMISSION_SCOPE_INCOMPLETE'):
        store.gate(permission_active=True)


@pytest.mark.parametrize('marker', ['revoked.json', 'permission-unknown.json'])
def test_suspension_blocks_reads_snapshots_and_acquisition_before_http(store, marker, monkeypatch):
    activate(store)
    digest = store.snapshot(archive_bytes(), retrieved_at_utc=UTC_STAMP, permission_active=True)
    store.write_json(marker, {'status':'SYNTHETIC SUSPENSION'})
    def forbidden(*args, **kwargs): raise AssertionError('HTTP must not be constructed after suspension')
    monkeypatch.setattr(urllib.request, 'build_opener', forbidden)
    for call in (lambda: store.gate(permission_active=True),
        lambda: store.load_snapshot(digest, permission_active=True),
        lambda: store.snapshot(archive_bytes(), retrieved_at_utc=UTC_STAMP, permission_active=True),
        lambda: acquire.acquire_private(store, permission_active=True)):
        with pytest.raises(DataError, match='PERMISSION_SUSPENDED'):
            call()


def test_permission_marker_symlink_is_a_stop_not_a_bypass(store, tmp_path):
    activate(store)
    (store.root/'revoked.json').symlink_to(tmp_path/'does-not-exist')
    with pytest.raises(DataError, match='PERMISSION_SUSPENDED'):
        store.gate(permission_active=True)


def test_private_json_rejects_invalid_or_non_object_metadata_without_echo(store):
    raw = b'PRIVATE HEADER AND RETURN ROW MUST NOT BE ECHOED'
    store.write('bad.json', raw)
    store.write_json('list.json', ['SYNTHETIC'])
    for name in ('bad.json', 'list.json'):
        with pytest.raises(DataError) as error:
            store.read_json(name)
        assert str(error.value) == 'INVALID_PRIVATE_METADATA'
        assert raw.decode() not in str(error.value)


def test_snapshot_fingerprints_and_provenance_are_immutable(store):
    activate(store)
    data = archive_bytes()
    digest = store.snapshot(data, retrieved_at_utc=UTC_STAMP, permission_active=True)
    assert digest == hashlib.sha256(data).hexdigest()
    restored, manifest = store.load_snapshot(digest, permission_active=True)
    assert restored == data and manifest['source_url'] == SOURCE_URL
    assert manifest['retrieved_at_utc'] == UTC_STAMP
    assert manifest['historical_release_availability_verified'] is False
    assert manifest['performance_cleared'] is False and manifest['raw_redistribution'] is False
    with pytest.raises(DataError, match='IMMUTABLE_FILE_EXISTS'):
        store.snapshot(data, retrieved_at_utc=UTC_STAMP, permission_active=True)
    # Synthetic tampering in an isolated test repo must not produce trusted input.
    snapshot = store.root/('snapshot_'+digest+'.zip')
    snapshot.write_bytes(data+b'SYNTHETIC REVISION')
    with pytest.raises(DataError, match='SNAPSHOT_FINGERPRINT_MISMATCH'):
        store.load_snapshot(digest, permission_active=True)
    snapshot.write_bytes(data)
    metadata_path = store.root/('manifest_'+digest+'.json')
    metadata_path.write_text(json.dumps(dict(manifest, source_url='https://example.invalid/not-approved')))
    with pytest.raises(DataError, match='SNAPSHOT_PROVENANCE_MISMATCH'):
        store.load_snapshot(digest, permission_active=True)
    with pytest.raises(DataError, match='SNAPSHOT_ID_REQUIRED'):
        store.load_snapshot('../private-name', permission_active=True)


def test_acquisition_attestation_gate_precedes_any_http(store, monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('No HTTP before active scope gate')
    monkeypatch.setattr(urllib.request, 'build_opener', forbidden)
    with pytest.raises(DataError, match='CURRENT_PERMISSION_ATTESTATION_REQUIRED'):
        acquire.acquire_private(store)
    activate(store, status='revoked')
    with pytest.raises(DataError, match='PERMISSION_NOT_ACTIVE_FOR_SCOPE'):
        acquire.acquire_private(store, permission_active=True)


def test_synthetic_acquisition_is_bounded_official_and_rechecks_revocation(store, monkeypatch, capsys):
    activate(store)
    payload = archive_bytes()
    calls = []
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size):
            calls.append(('read', size))
            return payload
    class Opener:
        def open(self, request, timeout):
            calls.append(('request', request.full_url, timeout))
            return Response()
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: Opener())
    digest = acquire.acquire_private(store, permission_active=True)
    assert digest == hashlib.sha256(payload).hexdigest()
    assert calls == [('request',SOURCE_URL,20),('read',MAX_ARCHIVE+1)]
    assert capsys.readouterr().out == ''
    # A revocation arriving while a request is in flight prevents persistence.
    class RevokedResponse(Response):
        def read(self, size):
            store.write_json('revoked.json', {'status':'SYNTHETIC REVOCATION'})
            return payload+b'new synthetic zip suffix'
    class RevokedOpener:
        def open(self, request, timeout): return RevokedResponse()
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: RevokedOpener())
    before = sorted(p.name for p in store.root.glob('snapshot_*'))
    with pytest.raises(DataError, match='PERMISSION_SUSPENDED'):
        acquire.acquire_private(store, permission_active=True)
    assert sorted(p.name for p in store.root.glob('snapshot_*')) == before


def test_no_redirect_or_private_source_details_are_exposed():
    with pytest.raises(DataError) as error:
        acquire.NoRedirect().redirect_request(None,None,302,'PRIVATE SECRET MESSAGE',{},'https://example.invalid/private')
    assert str(error.value) == 'UNAPPROVED_SOURCE_REDIRECT'


def test_imports_do_not_call_network_or_create_private_state(tmp_path):
    project = Path(__file__).resolve().parents[1]
    code = '''
import socket, urllib.request
from unittest.mock import patch

def forbidden(*args, **kwargs):
    raise AssertionError('Network on import')
with patch.object(socket, 'create_connection', forbidden), patch.object(urllib.request, 'build_opener', forbidden):
    import industry_companion.parser
    import industry_companion.safeguards
    import industry_companion.audit
    import industry_companion.acquire
    import industry_companion.__main__
print('IMPORTS_OFFLINE')
'''
    env = dict(os.environ, PYTHONPATH=str(project))
    result = subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env=env,capture_output=True,text=True)
    assert result.returncode == 0 and result.stdout == 'IMPORTS_OFFLINE\n' and result.stderr == ''
    assert not (tmp_path/'private').exists()


def test_owner_receipt_and_suspension_are_non_sensitive_immutable_metadata(store, monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2001,1,2,3,4,5,tzinfo=timezone.utc)
    monkeypatch.setattr(safeguards, 'datetime', Clock)
    store.record_owner_permission()
    value = store.read_json('permission-receipt.json')
    assert value['recorded_at_utc'] == UTC_STAMP
    assert value['raw_redistribution'] is False and value['rescission_possible'] is True
    assert value['evidence_reference'] == 'https://github.com/patelkavitarepo/Data-analytics-portfolio/issues/11'
    assert not ({'sender','sender_address','email','correspondence','message','private_headers'} & value.keys())
    with pytest.raises(DataError, match='IMMUTABLE_FILE_EXISTS'):
        store.record_owner_permission()
    store.suspend()
    suspended = store.read_json('revoked.json')
    assert suspended['recorded_at_utc'] == UTC_STAMP
    assert 'do not automatically delete' in suspended['action']
    assert (store.root/'permission-receipt.json').exists()
    with pytest.raises(DataError, match='PERMISSION_SUSPENDED'):
        store.gate(permission_active=True)


@pytest.mark.parametrize('attestation', ['false', 'true', 1, 2, [], {}, object()])
def test_truthy_and_nonboolean_attestations_never_clear_permission_gate(store, attestation, monkeypatch):
    activate(store)
    def forbidden(*args, **kwargs): raise AssertionError('HTTP must remain blocked for nonbool attestation')
    monkeypatch.setattr(urllib.request, 'build_opener', forbidden)
    for call in (lambda: store.gate(permission_active=attestation),
        lambda: store.snapshot(archive_bytes(), retrieved_at_utc=UTC_STAMP, permission_active=attestation),
        lambda: store.load_snapshot('0'*64, permission_active=attestation),
        lambda: acquire.acquire_private(store, permission_active=attestation)):
        with pytest.raises(DataError, match='CURRENT_PERMISSION_ATTESTATION_REQUIRED'):
            call()


def test_private_project_ancestor_symlink_is_rejected(store, tmp_path):
    store.write('fixture.txt', b'SYNTHETIC BYTES')
    alias = tmp_path/'ancestor-alias'
    alias.symlink_to(store.project.parent, target_is_directory=True)
    project_via_alias = alias/store.project.name
    assert not project_via_alias.is_symlink()
    with pytest.raises(DataError, match='PRIVATE_SYMLINK'):
        PrivateStore(project_via_alias).read('fixture.txt')


@pytest.mark.parametrize('kind', ['fifo', 'directory'])
def test_private_nonregular_objects_rejected_before_opening(store, kind, monkeypatch):
    store.write('fixture.txt', b'SYNTHETIC')
    target = store.root/'nonregular.json'
    if kind == 'fifo':
        os.mkfifo(target, 0o600)
    else:
        target.mkdir(mode=0o700)
    original_open = os.open
    def protected_open(path, flags, *args, **kwargs):
        if Path(path) == target:
            raise AssertionError('Must reject nonregular object before attempting open')
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(safeguards.os, 'open', protected_open)
    with pytest.raises(DataError, match='PRIVATE_REGULAR_FILE_REQUIRED'):
        store.read(target.name)


def test_regular_to_fifo_race_uses_nonblocking_open_and_fstat_rejection(store, monkeypatch):
    target = store.write('raced.json', b'SYNTHETIC BEFORE RACE')
    original_open = os.open
    seen = []
    def swap_on_open(path, flags, *args, **kwargs):
        if Path(path) == target:
            assert flags & os.O_NONBLOCK, 'Race-safe read must not block on an unexpected FIFO'
            seen.append(flags)
            target.unlink()
            os.mkfifo(target, 0o600)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(safeguards.os, 'open', swap_on_open)
    with pytest.raises(DataError, match='PRIVATE_REGULAR_FILE_REQUIRED'):
        store.read(target.name)
    assert len(seen) == 1

"""New review probes: cross-file contention, retained history and rule upgrades."""

from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading

import pytest

from sentinel.ingestion import read_csv_bytes
from sentinel.repository import Repository, RulesetMismatchError
from sentinel.schema import RULESET_VERSION


TABLES = ('sources', 'runs', 'accepted_rows', 'rejected_rows', 'findings')


def counts(path):
    with sqlite3.connect(path) as connection:
        return {name: connection.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                for name in TABLES}


@pytest.mark.parametrize('initialize_first', [True, False])
def test_different_files_competing_for_one_id_are_serialized(
    tmp_path, make_row, csv_bytes, initialize_first,
):
    path = tmp_path / 'shared.sqlite'
    if initialize_first:
        Repository(path)
    start = threading.Barrier(4)

    def submit(number):
        batch = read_csv_bytes(csv_bytes([make_row('shared'), make_row(f'unique-{number}')]))
        start.wait(timeout=10)
        return Repository(path).ingest(batch)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(4)))
    assert sum(run['input_count'] for run in results) == 8
    assert sum(run['accepted_count'] for run in results) == 5
    assert sum(run['rejected_count'] for run in results) == 3
    assert sum(f['code'] == 'duplicate_existing' for r in results for f in r['findings']) == 3
    assert counts(path) == dict(sources=4, runs=4, accepted_rows=5, rejected_rows=3, findings=3)
    with sqlite3.connect(path) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []


def test_rollback_after_existing_history_preserves_old_run(tmp_path, make_row, csv_bytes):
    path = tmp_path / 'audit.sqlite'
    repo = Repository(path)
    old = repo.ingest(read_csv_bytes(csv_bytes([make_row('retained')])))
    baseline = counts(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TRIGGER abort_later BEFORE INSERT ON rejected_rows "
                     "BEGIN SELECT RAISE(ABORT, 'review-injected failure'); END")
    next_batch = read_csv_bytes(csv_bytes([make_row('new'), make_row('bad', quantity='-1')]))
    with pytest.raises(sqlite3.DatabaseError):
        repo.ingest(next_batch)
    assert counts(path) == baseline
    assert repo.get_run(old['run_id']) == old
    with sqlite3.connect(path) as conn:
        conn.execute('DROP TRIGGER abort_later')
    recovered = repo.ingest(next_batch)
    assert (recovered['accepted_count'], recovered['rejected_count']) == (1, 1)


def test_changed_interpretation_never_reuses_a_previous_ruleset(
    tmp_path, make_row, csv_bytes,
):
    path = tmp_path / 'audit.sqlite'
    repo = Repository(path)
    batch = read_csv_bytes(csv_bytes([make_row('already-audited')]))
    old = repo.ingest(batch)
    with sqlite3.connect(path) as conn:
        conn.execute('UPDATE runs SET ruleset_version = ?', ('1',))
    assert RULESET_VERSION != '1'
    baseline = counts(path)
    with pytest.raises(RulesetMismatchError, match='fresh database'):
        repo.ingest(batch)
    assert counts(path) == baseline
    assert repo.get_run(old['run_id'])['ruleset_version'] == '1'

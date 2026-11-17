"""Transactional local audit store. Exact-byte replay returns the original run."""

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from .ingestion import Batch
from .schema import COLUMNS, RULESET_VERSION
from .validation import validate


DDL = """
CREATE TABLE IF NOT EXISTS sources (
    content_hash TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    byte_count INTEGER NOT NULL CHECK(byte_count >= 0)
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL REFERENCES sources(content_hash),
    ruleset_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    input_count INTEGER NOT NULL CHECK(input_count > 0),
    accepted_count INTEGER NOT NULL CHECK(accepted_count >= 0),
    rejected_count INTEGER NOT NULL CHECK(rejected_count >= 0),
    advisory_count INTEGER NOT NULL CHECK(advisory_count BETWEEN 0 AND accepted_count),
    CHECK(input_count = accepted_count + rejected_count),
    UNIQUE(content_hash, ruleset_version)
);
CREATE TABLE IF NOT EXISTS accepted_rows (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    row_number INTEGER NOT NULL,
    record_id TEXT NOT NULL UNIQUE,
    event_timestamp_utc TEXT NOT NULL,
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity BETWEEN 0 AND 10000),
    status TEXT NOT NULL,
    PRIMARY KEY(run_id, row_number)
);
CREATE TABLE IF NOT EXISTS rejected_rows (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    row_number INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY(run_id, row_number)
);
CREATE TABLE IF NOT EXISTS findings (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    row_number INTEGER NOT NULL,
    record_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('error', 'advisory')),
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    PRIMARY KEY(run_id, row_number, code, message)
);
"""


class RulesetMismatchError(ValueError):
    """An audit made under different interpretation rules needs a fresh store."""


class Repository:
    """A file-backed SQLite store; no live connection is held between calls.

    Validation and all writes run under BEGIN IMMEDIATE so overlapping submissions
    cannot both accept the same business ID. Unreadable files fail before this seam.
    Use a new database when changing rules: accepted IDs belong to this audit store.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(path) == ':memory:':
            raise ValueError('Use a file path; connections close after every operation.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(DDL)

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def ingest(self, batch: Batch) -> dict:
        with closing(self._connect()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute(
                'SELECT 1 FROM runs WHERE ruleset_version <> ? LIMIT 1', (RULESET_VERSION,),
            ).fetchone():
                raise RulesetMismatchError(
                    'This database contains audits under older or different rules. '
                    'Use a fresh database (or clear the Streamlit session audit); '
                    'existing audits are preserved for inspection.'
                )
            previous = conn.execute(
                'SELECT run_id FROM runs WHERE content_hash = ? AND ruleset_version = ?',
                (batch.content_hash, RULESET_VERSION),
            ).fetchone()
            if previous:
                result = self._get_run(conn, previous['run_id'])
                result['reused'] = True
                return result
            existing = {r[0] for r in conn.execute('SELECT record_id FROM accepted_rows')}
            checked = validate(batch.frame, existing_ids=existing)
            run_id = uuid4().hex
            advisory_count = len({f.row_number for f in checked.findings if f.severity == 'advisory'})
            conn.execute(
                'INSERT OR IGNORE INTO sources VALUES (?, ?, ?, ?)',
                (batch.content_hash, batch.source_name, batch.source_kind, batch.byte_count),
            )
            conn.execute(
                'INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (run_id, batch.content_hash, RULESET_VERSION,
                 datetime.now(timezone.utc).isoformat(), len(batch.frame),
                 len(checked.accepted), len(checked.rejected), advisory_count),
            )
            conn.executemany(
                'INSERT INTO accepted_rows VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                [(run_id, r['row_number'], *(r[c] for c in COLUMNS)) for r in checked.accepted],
            )
            conn.executemany(
                'INSERT INTO rejected_rows VALUES (?, ?, ?)',
                [(run_id, r['row_number'], json.dumps(r, allow_nan=False)) for r in checked.rejected],
            )
            conn.executemany(
                'INSERT INTO findings VALUES (?, ?, ?, ?, ?, ?)',
                [(run_id, f.row_number, f.record_id, f.severity, f.code, f.message)
                 for f in checked.findings],
            )
            return self._get_run(conn, run_id)

    def _get_run(self, conn, run_id: str) -> dict:
        row = conn.execute(
            'SELECT r.*, s.source_name, s.source_kind, s.byte_count FROM runs r '
            'JOIN sources s USING(content_hash) WHERE run_id = ?', (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f'No audit run {run_id!r}')
        result = dict(row)
        result['accepted'] = [dict(r) for r in conn.execute(
            'SELECT row_number, record_id, event_timestamp_utc, location, category, quantity, '
            'status FROM accepted_rows WHERE run_id = ? ORDER BY row_number', (run_id,),
        )]
        result['rejected'] = [json.loads(r[0]) for r in conn.execute(
            'SELECT payload_json FROM rejected_rows WHERE run_id = ? ORDER BY row_number', (run_id,),
        )]
        result['findings'] = [dict(r) for r in conn.execute(
            'SELECT row_number, record_id, severity, code, message FROM findings '
            'WHERE run_id = ? ORDER BY row_number, code', (run_id,),
        )]
        result['reused'] = False
        return result

    def get_run(self, run_id: str) -> dict:
        with closing(self._connect()) as conn:
            return self._get_run(conn, run_id)

    def list_runs(self) -> list[dict]:
        """Return summary metadata, newest first. This MVP has no audit retention job."""
        with closing(self._connect()) as conn:
            return [dict(r) for r in conn.execute(
                'SELECT r.*, s.source_name, s.source_kind, s.byte_count FROM runs r '
                'JOIN sources s USING(content_hash) ORDER BY created_at DESC, run_id DESC'
            )]

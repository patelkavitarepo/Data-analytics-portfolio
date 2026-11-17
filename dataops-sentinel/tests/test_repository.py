from concurrent.futures import ThreadPoolExecutor
import sqlite3
from threading import Barrier

import pytest

from sentinel.ingestion import read_csv_bytes
from sentinel.repository import Repository


def test_mixed_run_reconciles_and_survives_reopen(tmp_path, make_row, csv_bytes):
    path = tmp_path / "audit.sqlite"
    repo = Repository(path)
    raw = csv_bytes([make_row("good"), make_row("bad", quantity="-1")])
    run = repo.ingest(read_csv_bytes(raw, "fictional.csv"))
    assert (run["input_count"], run["accepted_count"], run["rejected_count"]) == (2, 1, 1)
    assert run["input_count"] == run["accepted_count"] + run["rejected_count"]
    assert run["advisory_count"] == 0
    saved = Repository(path).get_run(run["run_id"])
    assert saved["content_hash"] == run["content_hash"]
    assert saved["accepted"] == run["accepted"]
    assert saved["rejected"] == run["rejected"]
    assert saved["findings"] == run["findings"]


def test_exact_replay_adds_no_runs_sources_rows_or_findings(tmp_path, example_path):
    path = tmp_path / "audit.sqlite"
    repo = Repository(path)
    batch = read_csv_bytes(example_path.read_bytes(), "synthetic.csv")
    first = repo.ingest(batch)
    with sqlite3.connect(path) as conn:
        before = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("runs", "sources", "accepted_rows", "rejected_rows", "findings")}
    second = repo.ingest(batch)
    assert second["reused"] is True
    assert first["run_id"] == second["run_id"]
    assert second["accepted_count"] == 41
    assert second["rejected_count"] == 9
    assert len(repo.list_runs()) == 1
    with sqlite3.connect(path) as conn:
        after = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in before}
    assert before == after


def test_different_content_with_prior_business_id_is_explicit_rejection(tmp_path, make_row, csv_bytes):
    repo = Repository(tmp_path / "audit.sqlite")
    first = repo.ingest(read_csv_bytes(csv_bytes([make_row("old")])))
    second = repo.ingest(read_csv_bytes(csv_bytes([make_row("old"), make_row("fresh")])))
    assert first["run_id"] != second["run_id"]
    assert (second["input_count"], second["accepted_count"], second["rejected_count"]) == (2, 1, 1)
    assert any(f["code"] == "duplicate_existing" and f["row_number"] == 1 for f in second["findings"])


def test_transaction_rolls_back_entire_run_on_sql_failure(tmp_path, make_row, csv_bytes):
    path = tmp_path / "audit.sqlite"
    repo = Repository(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TRIGGER fail_findings BEFORE INSERT ON findings "
                     "BEGIN SELECT RAISE(ABORT, 'injected audit failure'); END")
    raw = csv_bytes([make_row("good"), make_row("bad", event_timestamp_utc="bad-date")])
    with pytest.raises(sqlite3.DatabaseError):
        repo.ingest(read_csv_bytes(raw))
    with sqlite3.connect(path) as conn:
        for table in ("runs", "sources", "accepted_rows", "rejected_rows", "findings"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        conn.execute("DROP TRIGGER fail_findings")
    assert repo.ingest(read_csv_bytes(raw))["input_count"] == 2


def test_untrusted_sql_strings_are_values(tmp_path, make_row, csv_bytes):
    repo = Repository(tmp_path / "audit.sqlite")
    hostile = "Robert'); DROP TABLE runs;--"
    run = repo.ingest(read_csv_bytes(csv_bytes([make_row(hostile, location=hostile)])))
    assert run["accepted_count"] == 1
    assert run["accepted"][0]["record_id"] == hostile
    assert len(repo.list_runs()) == 1


def test_multiple_missing_fields_retain_every_explanation(tmp_path, make_row, csv_bytes):
    repo = Repository(tmp_path / "audit.sqlite")
    blank = {column: "" for column in make_row()}
    run = repo.ingest(read_csv_bytes(csv_bytes([blank])))
    assert (run["input_count"], run["accepted_count"], run["rejected_count"]) == (1, 0, 1)
    assert len(run["findings"]) == 6
    assert {finding["code"] for finding in run["findings"]} == {"missing_value"}
    assert len({finding["message"] for finding in run["findings"]}) == 6
    assert repo.get_run(run["run_id"])["findings"] == run["findings"]


def test_concurrent_exact_replay_writes_only_one_run(tmp_path, example_path):
    path = tmp_path / "audit.sqlite"
    repo = Repository(path)
    batch = read_csv_bytes(example_path.read_bytes())
    ready = Barrier(2)

    def ingest_at_once():
        ready.wait(timeout=10)
        return repo.ingest(batch)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(ingest_at_once) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert results[0]["run_id"] == results[1]["run_id"]
    assert sorted(result["reused"] for result in results) == [False, True]
    assert len(repo.list_runs()) == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM accepted_rows").fetchone()[0] == 41
        assert conn.execute("SELECT COUNT(*) FROM rejected_rows").fetchone()[0] == 9

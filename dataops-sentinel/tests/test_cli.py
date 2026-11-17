"""Run the actual offline module entry point in a separate process."""

import csv
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from sentinel.schema import MAX_BYTES


PROJECT = Path(__file__).resolve().parents[1]


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "sentinel", *(str(arg) for arg in arguments)],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_cli_fixture_exports_and_exact_replay(tmp_path, example_path, manifest_path):
    database = tmp_path / "audit.sqlite"
    report_path = tmp_path / "quality.json"
    clean_path = tmp_path / "accepted.csv"
    arguments = (example_path, "--db", database, "--truth", manifest_path,
                 "--report", report_path, "--clean", clean_path)
    first = run_cli(*arguments)
    assert first.returncode == 0, first.stderr
    summary = json.loads(first.stdout)
    assert summary["input_count"] == 50
    assert summary["accepted_count"] == 41
    assert summary["rejected_count"] == 9
    assert summary["advisory_count"] == 1
    assert summary["reused"] is False
    report = json.loads(report_path.read_text())
    assert report["summary"]["input_count"] == 50
    assert report["truth_evaluation"]["hard_errors"]["fn"] == 0
    assert len(list(csv.DictReader(io.StringIO(clean_path.read_text())))) == 41
    with sqlite3.connect(database) as connection:
        before = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in ("runs", "sources", "accepted_rows", "rejected_rows", "findings")}
    second = run_cli(*arguments)
    assert second.returncode == 0, second.stderr
    replay = json.loads(second.stdout)
    assert replay["run_id"] == summary["run_id"]
    assert replay["reused"] is True
    assert replay["accepted_count"] == 41
    with sqlite3.connect(database) as connection:
        after = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                 for table in before}
    assert before == after


def test_cli_invalid_schema_exits_two_without_writing_audit(tmp_path):
    source = tmp_path / "invalid.csv"
    source.write_text("record_id,quantity\nSYN-1,2\n")
    database = tmp_path / "audit.sqlite"
    report = tmp_path / "quality.json"
    result = run_cli(source, "--db", database, "--report", report)
    assert result.returncode == 2
    assert "missing columns" in result.stderr
    assert not database.exists()
    assert not report.exists()


@pytest.mark.parametrize("collision", ["source_report", "source_database", "report_clean", "truth_report"])
def test_cli_path_collisions_rejected_before_mutation(collision, tmp_path, example_path, manifest_path):
    source = tmp_path / "source.csv"
    original = example_path.read_bytes()
    source.write_bytes(original)
    truth = tmp_path / "truth.json"
    original_truth = manifest_path.read_bytes()
    truth.write_bytes(original_truth)
    database = tmp_path / "audit.sqlite"
    export = tmp_path / "export.txt"
    if collision == "source_report":
        options = ("--db", database, "--report", source)
    elif collision == "source_database":
        options = ("--db", source)
    elif collision == "report_clean":
        options = ("--db", database, "--report", export, "--clean", export)
    else:
        options = ("--db", database, "--truth", truth, "--report", truth)
    result = run_cli(source, *options)
    assert result.returncode == 2
    assert "paths must be different" in result.stderr
    assert source.read_bytes() == original
    assert truth.read_bytes() == original_truth
    assert not database.exists()
    assert not export.exists()


@pytest.mark.parametrize("link_kind", ["hardlink", "symlink"])
@pytest.mark.parametrize("collision", ["source", "truth", "database", "export"])
def test_cli_file_aliases_rejected_before_mutation(
    collision, link_kind, tmp_path, example_path, manifest_path,
):
    source = tmp_path / "source.csv"
    source.write_bytes(example_path.read_bytes())
    truth = tmp_path / "truth.json"
    truth.write_bytes(manifest_path.read_bytes())
    database = tmp_path / "audit.sqlite"
    export = tmp_path / "existing-export.txt"
    alias = tmp_path / "alias.txt"
    options = ["--db", database]
    if collision == "database":
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE preserved (value TEXT)")
        protected = database
    elif collision == "truth":
        protected = truth
        options.extend(("--truth", truth))
    elif collision == "export":
        export.write_text("Preserve this existing export.\n")
        protected = export
        options.extend(("--clean", export))
    else:
        protected = source
    if link_kind == "hardlink":
        alias.hardlink_to(protected)
    else:
        alias.symlink_to(protected)
    options.extend(("--report", alias))
    before = {path: path.read_bytes() for path in (source, truth, protected)}

    result = run_cli(source, *options)

    assert result.returncode == 2
    assert "paths must be different" in result.stderr
    assert all(path.read_bytes() == original for path, original in before.items())
    if collision != "database":
        assert not database.exists()


@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"])
@pytest.mark.parametrize("role", ["input", "truth", "report", "clean"])
def test_cli_reserves_database_companion_paths(
    suffix, role, tmp_path, example_path, manifest_path,
):
    database = tmp_path / "audit.sqlite"
    companion = Path(str(database) + suffix)
    source = companion if role == "input" else tmp_path / "source.csv"
    source.write_bytes(example_path.read_bytes())
    options = ["--db", database]
    if role == "truth":
        companion.write_bytes(manifest_path.read_bytes())
        options.extend(("--truth", companion))
    elif role in ("report", "clean"):
        companion.write_text("Preserve this existing export.\n")
        options.extend(("--" + role, companion))
    before = {path: path.read_bytes() for path in (source, companion)}

    result = run_cli(source, *options)

    assert result.returncode == 2
    assert "SQLite database companion files" in result.stderr
    assert all(path.read_bytes() == original for path, original in before.items())
    assert not database.exists()


@pytest.mark.parametrize("link_kind", ["hardlink", "symlink"])
def test_cli_reserves_database_companion_aliases(link_kind, tmp_path, example_path):
    source = tmp_path / "source.csv"
    source.write_bytes(example_path.read_bytes())
    database = tmp_path / "audit.sqlite"
    companion = Path(str(database) + "-wal")
    original = b"Preserve this existing companion file.\n"
    companion.write_bytes(original)
    alias = tmp_path / "report.json"
    if link_kind == "hardlink":
        alias.hardlink_to(companion)
    else:
        alias.symlink_to(companion)

    result = run_cli(source, "--db", database, "--report", alias)

    assert result.returncode == 2
    assert "SQLite database companion files" in result.stderr
    assert companion.read_bytes() == original
    assert not database.exists()


@pytest.mark.parametrize("invalid", ["deep", "oversize", "missing", "directory"])
def test_cli_invalid_truth_fails_without_creating_audit(invalid, tmp_path, example_path):
    truth = tmp_path / "truth.json"
    database = tmp_path / "audit.sqlite"
    report = tmp_path / "report.json"
    if invalid == "deep":
        truth.write_text("[" * 20_000 + "]" * 20_000)
    elif invalid == "oversize":
        truth.write_bytes(b" " * MAX_BYTES + b"{}")
    elif invalid == "directory":
        truth.mkdir()

    result = run_cli(example_path, "--db", database, "--truth", truth, "--report", report)

    assert result.returncode == 2
    assert "Cannot complete audit/export" in result.stderr
    assert "Traceback" not in result.stderr
    if invalid == "deep":
        assert "nesting is too deep" in result.stderr
    elif invalid == "oversize":
        assert "Truth manifest exceeds" in result.stderr
    assert not database.exists()
    assert not report.exists()

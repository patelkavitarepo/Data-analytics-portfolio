"""Exercise the real Streamlit script and its session-private audit state."""

from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

from streamlit.testing.v1 import AppTest

from sentinel.ingestion import read_csv_bytes
from sentinel.repository import Repository, RulesetMismatchError


APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_demo_replay_and_new_session_are_isolated():
    first = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not first.exception
    first.button(key="load_demo").click().run()
    assert not first.exception
    run = first.session_state["sentinel_run"]
    assert run["input_count"] == run["accepted_count"] + run["rejected_count"]
    assert run["rejected_count"] > 0
    assert run["advisory_count"] > 0

    first.button(key="load_demo").click().run()
    assert not first.exception
    assert first.session_state["sentinel_run"]["reused"] is True
    assert first.session_state["sentinel_run"]["run_id"] == run["run_id"]
    first_database = first.session_state["sentinel_database"]
    with sqlite3.connect(first_database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1

    second = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not second.exception
    assert "sentinel_run" not in second.session_state
    assert second.session_state["sentinel_database"] != first_database
    second.button(key="load_demo").click().run()
    assert not second.exception
    assert second.session_state["sentinel_run"].get("reused") is not True
    assert second.session_state["sentinel_run"]["accepted_count"] == run["accepted_count"]

    second_database = second.session_state["sentinel_database"]
    first.button(key="clear_audit").click().run()
    assert not first.exception
    assert "sentinel_run" not in first.session_state
    assert not Path(first_database).exists()
    assert Path(second_database).exists()


def test_demo_truth_evaluation_requires_fresh_audit():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    lines = (APP.parent / "data" / "synthetic_operations.csv").read_bytes().splitlines()
    previous_input = b"\n".join(lines[:2]) + b"\n"
    Repository(app.session_state["sentinel_database"]).ingest(
        read_csv_bytes(previous_input, source_name="previous.csv")
    )
    app.button(key="load_demo").click().run()
    assert not app.exception
    assert any(
        finding["code"] == "duplicate_existing"
        for finding in app.session_state["sentinel_run"]["findings"]
    )
    assert any("Synthetic truth labels assume a fresh audit" in caption.value for caption in app.caption)
    assert not any(
        "Evaluation against the synthetic truth manifest" in markdown.value
        for markdown in app.markdown
    )


@pytest.mark.parametrize("failure", ["invalid_csv", "database", "demo_read", "ruleset"])
def test_failed_submission_clears_displayed_result_until_next_success(failure):
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.button(key="load_demo").click().run()
    saved_run = app.session_state["sentinel_run"]
    database = app.session_state["sentinel_database"]
    assert len(app.metric) == 4
    assert len(app.get("download_button")) == 3
    assert any(text.value == "Source: synthetic_operations.csv" for text in app.text)

    if failure == "invalid_csv":
        failing_source = patch.object(Path, "read_bytes", return_value=b"record_id\nbad\n")
    elif failure == "database":
        failing_source = patch.object(Repository, "ingest", side_effect=sqlite3.OperationalError("test failure"))
    elif failure == "ruleset":
        failing_source = patch.object(Repository, "ingest", side_effect=RulesetMismatchError("start a fresh database"))
    else:
        failing_source = patch.object(Path, "read_bytes", side_effect=OSError("test demo read failure"))
    with failing_source:
        app.button(key="load_demo").click().run()

    assert not app.exception
    assert "sentinel_run" not in app.session_state
    assert len(app.error) == 1
    first_error = app.error[0].value
    first_error_detail = app.session_state["sentinel_error"]
    assert first_error_detail in [text.value for text in app.text]
    assert not app.metric
    assert not app.get("download_button")
    # A later widget/download-triggered rerun must not resurrect the old success.
    app.run()
    assert not app.exception
    assert [error.value for error in app.error] == [first_error]
    assert first_error_detail in [text.value for text in app.text]
    assert "sentinel_run" not in app.session_state
    assert not app.metric
    assert not app.get("download_button")
    assert Repository(database).get_run(saved_run["run_id"])["accepted_count"] == 41

    app.button(key="load_demo").click().run()
    assert not app.exception
    assert not app.error
    assert "sentinel_error" not in app.session_state
    assert app.session_state["sentinel_run"]["run_id"] == saved_run["run_id"]
    assert len(app.metric) == 4
    assert len(app.get("download_button")) == 3


def test_clear_session_audit_resets_error_and_upload_widget_identity():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    initial_upload_id = app.get("file_uploader")[0].proto.id
    with patch.object(Path, "read_bytes", return_value=b"record_id\nbad\n"):
        app.button(key="load_demo").click().run()
    assert app.error
    old_database = app.session_state["sentinel_database"]

    app.button(key="clear_audit").click().run()
    assert not app.exception
    assert not app.error
    assert "sentinel_error" not in app.session_state
    assert "sentinel_run" not in app.session_state
    assert app.get("file_uploader")[0].proto.id != initial_upload_id
    assert app.button(key="run_upload").disabled
    assert not Path(old_database).exists()


def test_session_database_open_failure_has_actionable_feedback():
    app = AppTest.from_file(str(APP), default_timeout=20)
    with patch.object(Repository, "__init__", side_effect=sqlite3.OperationalError("test unavailable store")):
        app.run()
    assert not app.exception
    assert len(app.error) == 1
    assert app.error[0].value == "The session audit could not be opened."
    assert any(text.value == "test unavailable store" for text in app.text)
    assert not app.metric
    app.run()
    assert not app.exception
    assert not app.error


def test_source_names_and_schema_errors_are_displayed_as_literal_text():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.button(key="load_demo").click().run()
    source = "![source](https://review-probe.invalid/source).csv"
    app.session_state["sentinel_run"]["source_name"] = source
    app.run()
    assert not app.exception
    assert f"Source: {source}" in [text.value for text in app.text]
    assert not any(source in caption.value for caption in app.caption)

    header = "![header](https://review-probe.invalid/header)"
    raw = (
        "record_id,event_timestamp_utc,location,category,quantity,status," + header + "\n"
        "SYN-MARKDOWN,2026-01-15T12:00:00Z,X,delivery,10,completed,x\n"
    ).encode()
    with patch.object(Path, "read_bytes", return_value=raw):
        app.button(key="load_demo").click().run()
    assert not app.exception
    assert any(header in text.value for text in app.text)
    assert not any(header in error.value for error in app.error)

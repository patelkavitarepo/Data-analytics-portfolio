"""Exercise the real Streamlit script and its session-private audit state."""

from pathlib import Path
import sqlite3

from streamlit.testing.v1 import AppTest

from sentinel.ingestion import read_csv_bytes
from sentinel.repository import Repository


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

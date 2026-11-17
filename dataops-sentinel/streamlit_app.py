"""Offline, session-isolated interface for the synthetic DataOps Sentinel MVP."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile

import pandas as pd
import streamlit as st

from sentinel.ingestion import IngestionError, read_csv_bytes
from sentinel.reporting import clean_csv, evaluate_truth, findings_csv, quality_report
from sentinel.repository import Repository, RulesetMismatchError
from sentinel.schema import MAX_BYTES


ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="DataOps Sentinel", page_icon="🛡️", layout="wide")


def session_repository() -> Repository:
    """Never share uploaded records or a database through a global Streamlit cache."""
    if "sentinel_directory" not in st.session_state:
        st.session_state.sentinel_directory = tempfile.TemporaryDirectory(
            prefix="dataops-sentinel-"
        )
        st.session_state.sentinel_database = str(
            Path(st.session_state.sentinel_directory.name) / "audit.sqlite3"
        )
    return Repository(st.session_state.sentinel_database)


def clear_current_result() -> None:
    st.session_state.pop("sentinel_run", None)
    st.session_state.pop("sentinel_error", None)


def ingest(raw: bytes, name: str, repository: Repository) -> None:
    clear_current_result()
    try:
        batch = read_csv_bytes(raw, source_name=name)
        st.session_state.sentinel_run = repository.ingest(batch)
    except (IngestionError, RulesetMismatchError, sqlite3.Error, OSError) as exc:
        st.session_state.sentinel_error = f"The input could not be processed: {exc}"


try:
    repository = session_repository()
except (sqlite3.Error, OSError) as exc:
    st.error("The session audit could not be opened.")
    st.text(str(exc))
    st.stop()

with st.sidebar:
    st.title("DataOps Sentinel")
    st.caption("Python · pandas · SQLite")
    st.markdown("A portfolio demo for checking small operations feeds.")
    st.info("The bundled feed is entirely synthetic. Its findings are fictional.")
    st.markdown("**Your session audit**")
    st.caption(
        "Uploads and audit records live in a private temporary SQLite database for "
        "this browser session. They are not shared through an application cache. "
        "A server restart or session cleanup can erase them."
    )
    if st.button("Clear session audit", key="clear_audit", width="stretch"):
        st.session_state.sentinel_directory.cleanup()
        upload_generation = st.session_state.get("sentinel_upload_generation", 0)
        st.session_state.pop(f"operations_upload_{upload_generation}", None)
        st.session_state.sentinel_upload_generation = upload_generation + 1
        for key in ("sentinel_directory", "sentinel_database", "sentinel_run", "sentinel_error"):
            st.session_state.pop(key, None)
        st.rerun()

st.title("Check a feed. Understand every finding.")
st.markdown(
    "Validate operations records, review row-level explanations, and export an "
    "auditable result. **This MVP works completely offline.**"
)

with st.container(border=True):
    st.subheader("1. Choose an input")
    demo_column, upload_column = st.columns(2, gap="large")
    with demo_column:
        st.markdown("**Explore the fictional demo**")
        st.write(
            "A fixed-seed feed includes deliberate errors and one suspicious, "
            "valid quantity. A separate truth manifest lets you inspect detection results."
        )
        if st.button("Load synthetic demo", type="primary", key="load_demo"):
            clear_current_result()
            try:
                ingest(
                    (ROOT / "data" / "synthetic_operations.csv").read_bytes(),
                    "synthetic_operations.csv",
                    repository,
                )
            except OSError as exc:
                st.session_state.sentinel_error = f"The bundled demo could not be read: {exc}"
    with upload_column:
        st.markdown("**Check a CSV**")
        uploaded = st.file_uploader(
            "Operations CSV (UTF-8)", type=["csv"],
            key=f"operations_upload_{st.session_state.get('sentinel_upload_generation', 0)}",
        )
        st.caption(
            "Maximum 2 MiB and 10,000 rows. Required columns: record_id, "
            "event_timestamp_utc, location, category, quantity, status. "
            "Timestamps without an offset are assumed UTC."
        )
        st.caption("Use fictional, non-sensitive inputs only.")
        if st.button("Validate uploaded CSV", disabled=uploaded is None, key="run_upload"):
            clear_current_result()
            try:
                uploaded.seek(0)
                ingest(uploaded.read(MAX_BYTES + 1), uploaded.name, repository)
            except OSError as exc:
                st.session_state.sentinel_error = f"The upload could not be read: {exc}"

if st.session_state.get("sentinel_error"):
    st.error("The input could not be processed. See the details below.")
    st.text(st.session_state.sentinel_error)
run = st.session_state.get("sentinel_run")
if run is None:
    st.info("Load the synthetic demo or upload a CSV to see a quality report.")
    st.stop()

st.subheader("2. Review the result")
st.text(f"Source: {run['source_name']}")
if run.get("reused"):
    st.info("This exact input was already audited. Showing its saved result; no rows were added.")

metric_columns = st.columns(4)
for column, title, key in zip(
    metric_columns,
    ("Input rows", "Accepted", "Rejected", "Advisory rows"),
    ("input_count", "accepted_count", "rejected_count", "advisory_count"),
):
    column.metric(title, run[key])

total = run["input_count"]
st.caption(
    f"Reconciliation: {total} input = {run['accepted_count']} accepted + "
    f"{run['rejected_count']} rejected. Advisory rows are part of the accepted cohort. "
    "A flag requests review; it does not establish an error."
)

manifest = json.loads((ROOT / "data" / "truth_manifest.json").read_text(encoding="utf-8"))
is_demo = manifest["source_sha256"] == run["content_hash"]
has_previous_ids = any(finding["code"] == "duplicate_existing" for finding in run["findings"])
truth = manifest if is_demo and not has_previous_ids else None
overview, records, audit = st.tabs(["Quality overview", "Records and findings", "Audit trail"])

with overview:
    st.markdown("**Validation rates**")
    st.write(
        f"Rejected: {run['rejected_count'] / total:.1%} of input rows. "
        f"Advisory: {run['advisory_count'] / total:.1%} of input rows."
    )
    findings = pd.DataFrame(run["findings"])
    if findings.empty:
        st.success("No validation errors or advisory findings in this input.")
    else:
        breakdown = (
            findings.groupby(["severity", "code"], sort=True)
            .size()
            .rename("finding_count")
            .reset_index()
        )
        st.dataframe(breakdown, hide_index=True, width="stretch")
        st.caption("Counts here are findings. One row can have several reasons.")
    if truth is not None:
        st.markdown("**Evaluation against the synthetic truth manifest**")
        st.caption(
            "This evaluation applies only to the exact committed demo bytes. "
            "It measures this fixture, not real-world accuracy."
        )
        st.json(evaluate_truth(run, truth))
    elif is_demo and has_previous_ids:
        st.caption(
            "Synthetic truth labels assume a fresh audit. Clear this session audit "
            "and reload the demo to evaluate them."
        )
    else:
        st.caption("No truth labels are available for this input; detection accuracy is unknown.")
    st.markdown("**Download this result**")
    report_column, clean_column, findings_column = st.columns(3)
    report_column.download_button(
        "Quality report (JSON)",
        quality_report(run, truth=truth),
        file_name="dataops_quality_report.json",
        mime="application/json",
        width="stretch",
    )
    clean_column.download_button(
        "Accepted records (CSV)",
        clean_csv(run),
        file_name="dataops_accepted.csv",
        mime="text/csv",
        width="stretch",
    )
    findings_column.download_button(
        "Findings (CSV)",
        findings_csv(run),
        file_name="dataops_findings.csv",
        mime="text/csv",
        width="stretch",
    )
    st.caption("CSV exports escape formula-like text for safer spreadsheet viewing.")
    st.caption(
        "Streamlit download links can be opened by anyone with the link while the result is available. "
        "Use fictional, non-sensitive inputs only."
    )

with records:
    st.markdown("**Accepted records**")
    st.caption("UTC timestamps and validated quantities. Advisory rows remain accepted.")
    st.dataframe(pd.DataFrame(run["accepted"]), hide_index=True, width="stretch")
    st.markdown("**Rejected records**")
    st.dataframe(pd.DataFrame(run["rejected"]), hide_index=True, width="stretch")
    st.markdown("**Row-level findings**")
    st.caption("Row numbers start at 1 for the first data row after the CSV header.")
    st.dataframe(findings, hide_index=True, width="stretch")

with audit:
    st.markdown("**Source provenance**")
    st.json(
        {
            key: run[key]
            for key in (
                "run_id", "source_name", "source_kind", "content_hash", "byte_count",
                "created_at", "ruleset_version",
            )
        }
    )
    st.markdown("**Runs in this session**")
    st.dataframe(pd.DataFrame(repository.list_runs()), hide_index=True, width="stretch")
    st.caption(
        "An exact-file replay reuses its saved run. A different file containing "
        "an ID accepted earlier in this session is rejected as an existing duplicate. "
        "Download results before leaving; this temporary database is not durable hosting."
    )

# Project 009 — DataOps Sentinel owner acceptance

**Status: human acceptance pending.** This walkthrough prepares the owner to
review the working application. Automated verification does not complete human
review, authorize a merge, or authorize a release/deployment.

Application candidate: `a7b801f36a3078aaabcdf7c1057245f453bc5687`, branch
`feat/dataops-sentinel-issue-15`, [draft PR #16](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/16).
Checkpoint 3 adds documentation and an intentionally malformed demonstration
file; application code, tests, dependencies and workflow are unchanged.
See [actual checkpoint results](CHECKPOINT_3_RESULTS.md).

## Prepare once

Use Python 3.12 (3.11 is also supported). Open the checked-out feature branch at
the repository root, then run these Linux/macOS commands:

```bash
python3.12 -m venv dataops-sentinel/.venv
source dataops-sentinel/.venv/bin/activate
python -m pip install -r dataops-sentinel/requirements-dev.txt
python -m pytest -q dataops-sentinel/tests
python -m ruff check dataops-sentinel
cd dataops-sentinel
streamlit run streamlit_app.py
```

If the environment already exists, activate it and continue. In Windows
PowerShell, create it with `py -3.12 -m venv dataops-sentinel/.venv` and activate
`dataops-sentinel\.venv\Scripts\Activate.ps1` before the pip/test commands.
Installation needs internet access; the application demo then works offline.
Open the local URL printed by Streamlit. Running from `dataops-sentinel/` loads
the project's 2 MiB upload setting and disables usage telemetry.

Use fictional, non-sensitive data only. Keep the seven steps below in the same
browser session. Click **Clear session audit** before beginning if this session
already has results, so prior accepted IDs cannot change the demo context.

## Seven-step acceptance walkthrough

### 1. Load the fictional dataset

**Action:** click **Load synthetic demo**.

**Expected:** the source is `synthetic_operations.csv`; the four metrics are
**50 input, 41 accepted, 9 rejected, 1 advisory**. The reconciliation caption says
50 = 41 + 9 and that the advisory is part of accepted rows.

**What it proves:** the bundled offline input passes through the real ingestion,
validation and SQLite path; advisories are not a separate row cohort.

**Owner verification:** read all four metrics. In **Audit trail**, note the run ID,
rule version **2**, and source hash
`2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21`.
The session's runs table should contain one run. Record the ID for step 4.

### 2. Review accepted and rejected records

**Action:** open **Records and findings**; inspect the accepted, rejected and
row-level findings tables. Scroll within the tables if needed.

**Expected:** accepted IDs are `SYN-0001`–`SYN-0040` plus `SYN-0050`.
Rejected data-row numbers are **41–49**. Rows **43 and 44** share
`SYN-DUPLICATE`; both have a duplicate-ID explanation. Row 45 has an impossible
date; rows 46/47 have invalid quantities. Rejected rows retain their original
values for inspection. Row numbers exclude the CSV header.

**What it proves:** hard failures have traceable explanations, rather than being
silently dropped or arbitrarily resolving conflicting IDs.

**Owner verification:** compare these rows with the committed
[CSV](../data/synthetic_operations.csv) and
[truth manifest](../data/truth_manifest.json). The
[provenance table](DATA_PROVENANCE.md) enumerates every injected change.

### 3. Investigate the accepted advisory

**Action:** locate `SYN-0050`, data row **50**, quantity **500**, in accepted rows
and its `quantity_outlier` finding.

**Expected:** severity is **advisory**, not error; the row remains accepted.
Quantity 500 is an integer within 0–10,000 and its completed status is consistent.

**What it proves:** an unusual value is not automatically a proven data error.
The heuristic compares otherwise accepted quantities using a median/MAD score.

**Owner verification:** explain aloud why this row passes hard rules while still
deserving review. In **Quality overview**, inspect the separate synthetic truth
evaluation: hard-error TP=9/FP=0/FN=0/TN=41; advisory TP=1/FP=0/FN=0/TN=49.
These describe this constructed fixture only; they do not establish real-world
accuracy or prove that the large quantity is wrong.

### 4. Reprocess identical input

**Action:** click **Load synthetic demo** again.

**Expected:** an already-audited/saved-result message appears; metrics remain
50/41/9/1. **Audit trail** shows the same run ID, timestamp and hash, with still
only one run. Reloading the same file under another name also reuses exact bytes.

**What it proves:** exact-input replay is idempotent: it returns the stored result
instead of adding records or falsely rejecting the demo's IDs as new duplicates.

**Owner verification:** compare the ID noted in step 1 and count the runs table.
Automated SQL verification separately confirms stored totals remain one source,
one run, 41 accepted rows, nine rejected rows and ten findings. A different file
containing an already accepted ID follows the separate cross-file rejection rule.

### 5. Submit a malformed schema and check for stale results

**Action:** use **Browse files** to select the committed demonstration file
`dataops-sentinel/docs/owner_malformed.csv` (or `docs/owner_malformed.csv` relative
to the app folder), then click **Validate uploaded CSV**. Its entire content is:

```csv
record_id,quantity
SYN-OWNER-BAD,10
```

**Expected:** actionable schema feedback identifies missing columns such as
`event_timestamp_utc`, `location`, `category` and `status`. The former successful
metrics, records and download buttons disappear. The old successful audit is
retained in storage; this schema-invalid input creates no new run.

**What it proves:** schema validation fails before auditing, and a failed input
cannot masquerade as the previous successful result.

**Owner verification:** confirm there are **no result metrics or download buttons**.
For a rerun check, choose the valid `data/synthetic_operations.csv` in the uploader
but **do not click Validate yet**. The failure must remain visible with no stale
success. Selecting a file alone does not validate it. Step 6 explicitly runs the
demo again to recover the saved result.

### 6. Recover and download a report

**Action:** click **Load synthetic demo** again. In **Quality overview**, click
**Quality report (JSON)** and **Accepted records (CSV)**.

**Expected:** the error clears and the saved 50/41/9/1 result returns. The JSON
report contains `summary`, `provenance`, `reason_breakdown`, `findings` and
`truth_evaluation`. Its source hash and run ID match steps 1/4. The accepted CSV
has **41 data rows** (42 lines for this fixture, including its header) and retains
`SYN-0050` quantity 500.

**What it proves:** downloads come from the recovered current result, preserve
provenance, and retain advisory rows in the accepted cohort.

**Owner verification:** open JSON in a text editor and check
`summary.input_count=50`, `accepted_count=41`, `rejected_count=9`,
`advisory_count=1`, and `provenance.ruleset_version="2"`. Inspect the CSV for
`SYN-0050` and absence of rejected `SYN-0041`. Downloaded JSON includes real audit
metadata for your run; a fresh session will have a different ID/timestamp.

### 7. Reset the session

**Action:** click **Clear session audit** in the sidebar; expand the sidebar
first on a narrow screen.

**Expected:** result metrics/downloads disappear, the uploader has no selected
filename, Validate is disabled, and the choose-input guidance returns.

**What it proves:** the app clears its current session's audit, result/error state
and uploader. It does not reuse another visitor's database.

**Owner verification:** optionally load the demo again and confirm a new run ID
with fresh 50/41/9/1 counts. Existing files already downloaded to your computer
are not deleted. Reset is **not** a guaranteed immediate revocation of old
Streamlit media URLs; see the limits below.

## Understand the implementation before accepting it

| Module | Responsibility to explain |
| --- | --- |
| `sentinel/schema.py` | Six required columns, allowed categories/statuses, 2 MiB/10,000-row/131,072-character field bounds, rule version 2. |
| `sentinel/ingestion.py` | Parse bounded UTF-8 CSV or flat JSON, normalize headers, reject malformed/schema/decoded-text errors, hash original bytes. JSON number tokens stay exact before validation. The API adapter uses an injected/mock response; no live client is built in. |
| `sentinel/validation.py` | Required values, duplicates, UTC timestamps, finite integer/range rules and status consistency. Partition each row once; attach error or advisory explanations. |
| `sentinel/repository.py` | Persist sources, runs, accepted/rejected rows and findings in SQLite with parameterized SQL, constraints and atomic transactions. |
| `sentinel/reporting.py` | Derive counts/rates, export JSON and spreadsheet-safe CSV, and evaluate separate synthetic truth labels. The detector does not read those labels. |
| `streamlit_app.py` | Collect input, show current results and persistent literal errors, manage each session's temporary database, and offer downloads. |
| `sentinel/synthetic.py` / `__main__.py` | Fixed-seed fixture generation / offline CLI using the same application seams. |

**Transactions:** ingestion opens an immediate SQLite transaction before checking
prior accepted IDs. A source/run, its two row cohorts, and findings commit together.
A write failure rolls the whole new run back; earlier committed runs remain.
The lock and unique business-ID constraint prevent overlapping submissions from
both accepting the same ID. Connections close after each operation.

**Two kinds of duplicate detection:** every member of a duplicate-ID group within
one input is rejected. An ID accepted in a prior different-content file is also
rejected in that database. Exact bytes plus the current rule version instead reuse
the saved run. Renaming identical bytes does not make a new source; reformatting
changes their hash. There is no record-update/overwrite workflow. Older-rule audit
stores are preserved but refused for new ingestion; use a fresh store.

**Hard rules and advisory:** timestamps need an ISO date/time with seconds; naive
values explicitly assume UTC, offsets normalize to UTC. Quantity must be a finite
integer from 0 through 10,000. Cancelled status requires zero; pending/completed
require positive quantity. With at least eight otherwise accepted rows, the
quantity advisory uses `0.6745 * abs(q - median) / max(MAD, 1) > 3.5`.
It can flag legitimate cancellations or miss values in mixed/bimodal batches.
It never removes a row from accepted data or estimates empirical accuracy.

**Audit counts:** input = accepted + rejected. Advisory is an accepted subset.
One row can have several findings, so finding counts need not equal row counts.
Reports name their denominators; advisory/accepted is JSON `null` when no row was
accepted, rather than dividing by zero.

## Limits and publication boundary

Only fictional, non-sensitive inputs are appropriate. SQLite is temporary, local
and single-instance; server restarts or cleanup can erase it. There is no durable
shared store, authentication, aggregate quota, migration tool or retention guarantee.
Anyone who knows an active Streamlit download URL may retrieve it from another
browser; links can remain during framework cleanup. Session isolation is separate
from download authentication. Download needed results before leaving.

[Deployment readiness](DEPLOYMENT_READINESS.md) describes the exact future setup
and hosted smoke tests. Community Cloud itself has **not** been deployed or tested
by this checkpoint. Its configuration and upload transport must be checked after
owner authorization. The [portfolio brief](PORTFOLIO_BRIEF.md) provides short demo
scripts and attribution-safe résumé wording.

## Owner decision — leave blank until personally completed

These boxes are intentionally unchecked. Automated/browser checks do not mark them.

- [ ] I personally completed steps 1–7 and recorded the run/source evidence.
- [ ] I can explain the module seams, transaction/replay policy and advisory limits.
- [ ] I reviewed the known limitations and outstanding questions.
- [ ] I recorded my actual contributions separately from AI-assisted implementation.

| Owner | Date | Source/PR commit reviewed | Results or evidence | Remaining questions | Acceptance decision |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

Acceptance, merge authorization, release authorization and deployment/publication
authorization are separate decisions. None has been recorded here. Keep PR #16 in
draft until the owner explicitly directs the next step; this document grants none
of those permissions.

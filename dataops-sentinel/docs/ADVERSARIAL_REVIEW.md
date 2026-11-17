# DataOps Sentinel adversarial review

**Recommendation: READY FOR HUMAN REVIEW** of the synthetic, offline portfolio MVP,
after the fixes in this branch. This is not approval to merge, deploy, process
sensitive data, or claim production security. No unresolved material defect was
reproduced in the supported synthetic-input flows after the fixes. The remaining
download-transport and hosting limits below are explicit conditions of this recommendation.

The reviewed baseline was draft PR #16 at `49e3fd146f7023ab9318ad74f336db6a55f8e7a9`.
Issue #15 and its complete acceptance criteria were reread; there were no issue
comments. Separate agent reviewers without the implementation conversation inspected
ingestion, storage/CLI, and UI/security, while the coordinating agent independently
reproduced baseline failures and fixture calculations. This is AI-assisted software
review, not a certification of independent human review.

The original **94 passing tests did not establish correctness**. Nine findings
were reproduced below, including source/database destruction through CLI hardlinks.
All nine were fixed on the existing feature branch. Existing tests were retained;
the final suite has **214 cases**, including **120 additional cases**.

## Findings, evidence, impact and smallest fixes

Line numbers in this section refer to the **baseline commit**, not shifted current
lines. All paths are relative to `dataops-sentinel/`. Payloads and data were synthetic.

### R1 — High / P1: hardlinks bypass CLI overwrite protection — fixed

**Affected:** `sentinel/__main__.py:23`, `:24`, `:39`.
`Path.resolve()` compared names but did not recognize two hardlinks to one inode.

**Executed reproduction:** create a normal synthetic input and `report.json` as
a hardlink to it; run `python -m sentinel input.csv --db audit.sqlite --report
report.json`. The CLI returned **0** and replaced the input bytes with report JSON.
Repeating with the report hardlinked to an existing audit database also returned
**0**; reopening SQLite then failed with **`file is not a database`**.

**Impact:** an apparently protected export could destroy the source or audit.
**Smallest fix applied:** compare canonical paths and existing inodes using
`Path.samefile()` before creating/writing anything. Tests cover source, truth,
database, and existing exports with both hardlinks and symlinks; protected bytes
remain unchanged. This does not claim protection against a hostile local process
changing the filesystem concurrently between validation and writing.

### R2 — Medium / P2: JSON float rounding changes validation and identity — fixed

**Affected:** `sentinel/ingestion.py:152`, `:170`.
Default JSON binary-float parsing preceded the Decimal business rule.

**Executed reproduction:** unquoted JSON quantity `1.0000000000000001` became
`"1.0"`; `10000.0000000000001` became `"10000.0"`; cancelled quantity `-1e-10000`
became `"-0.0"`. Each was **accepted=1/rejected=0**, though the original value
violated the integer/range rule. Numeric IDs `9007199254740992.0` and
`9007199254740993.0` also collapsed to one binary-float representation.

**Impact:** invalid data could enter accepted storage; distinct IDs could be
falsely rejected as duplicates. **Smallest fix applied:** preserve JSON number
tokens as strings through `parse_int=str` and `parse_float=str`, then validate exact
values with Decimal. Regression tests check rejected raw lexemes, extreme exponents,
large integers and distinct IDs. Interpretation version is now **2**; ingestion
refuses a database containing runs under another version instead of replaying an
old result. Existing audit history remains readable; use a fresh database.

### R3 — Medium / P2: decoded JSON text bypasses encoding checks — fixed

**Affected:** `sentinel/ingestion.py:150`, `:165`, `:170`.
The raw source check could not see characters introduced by JSON escapes.

**Executed reproduction:** `location="Synthetic\u0000Hub"` had no literal NUL in
the source bytes but was accepted and stored with an actual NUL. An unexpected
column name containing escaped `\ud800` produced an exception message with an
unpaired surrogate; sending that message to Streamlit raised `UnicodeEncodeError`.

**Impact:** inconsistent CSV/JSON text rules and a malformed input crashing error
feedback. **Smallest fix applied:** check decoded JSON keys and values for NUL and
UTF-8 encodability. Invalid-key errors identify row/key position without echoing
the invalid key. Tests cover all six fields and key/value escape paths.

### R4 — Medium / P2: schema errors render untrusted Markdown images — fixed

**Affected:** `streamlit_app.py:40`, fed by `sentinel/ingestion.py:63`.

**Executed reproduction:** add an extra CSV header
`![header](https://review-probe.invalid/header)`. The schema-error alert rendered
an image and the browser attempted that URL. Playwright intercepted and aborted
the request; no external collection occurred. A source-caption variant was caught
during the fix, before publication.

**Impact:** an invalid input could trigger a browser request outside the offline
app and misleading visual content. No script execution was demonstrated.
**Smallest fix applied:** keep alerts generic and render exception details and
source names with literal `st.text`, without a custom Markdown sanitizer. AppTest
and browser regressions show **zero images and zero attempted probe requests**.

### R5 — Medium / P2: a failed upload leaves stale successful results — fixed

**Affected:** `streamlit_app.py:35`, `:40`, `:102`.

**Executed reproduction:** accept a clean one-row file, submit malformed `bad.csv`,
then click the still-visible report download. The click-triggered rerun removed
the error and previous-run notice while `bad.csv` remained selected. The screen
showed accepted=1 and no validation errors; the download described the older source.

**Impact:** users could associate another file's success or export with a failed
submission. **Smallest fix applied:** invalidate the displayed result at submission,
persist error details across reruns, and display the successful result's source.
Post-fix browser checks show **0 metrics / 0 downloads** after failure and subsequent
rerun; a valid retry restores its saved audit. Added error-path tests also exercise
demo-read failure, database-write/open failure and rule-version mismatch.

### R6 — Medium / P2: SQLite companion filenames are unsafe export paths — fixed

**Affected:** `sentinel/__main__.py:23`, `:39`, `:41`.

**Executed reproduction:** use `--report audit.sqlite-journal` or
`--report audit.sqlite-wal`. The command returned **0** and wrote the report;
the next successful exact-input CLI replay silently removed that file as a SQLite
companion. The `-shm` path is also reserved by SQLite.

**Impact:** successful exports could disappear or conflict with database artifacts.
**Smallest fix applied:** reserve database `-journal`, `-wal` and `-shm` paths,
including existing aliases, for every input/truth/export role. Twelve role/suffix
cases and alias regressions reject these paths before mutation.

### R7 — Medium / P2: truth-file reads are unbounded and nesting escapes handling — fixed

**Affected:** `sentinel/__main__.py:33`.

**Executed reproduction:** a 40,000-byte truth file containing 20,000 opening and
closing brackets raised an uncaught `RecursionError`: **exit 1**, traceback, no
database created. The previous `read_text()` also imposed no truth-file size bound.

**Impact:** inconsistent error behavior and avoidable resource use on external CLI
input. **Smallest fix applied:** read at most 2 MiB+1, reject oversize truth files,
and convert excessive nesting to actionable **exit 2** before audit creation.
Tests include missing files and directory inputs. A semantic truth/report failure
after a successful audit still leaves that audit committed, as documented.

### R8 — Low / P3: field limits differ silently between CSV and JSON — fixed

**Affected:** `sentinel/ingestion.py:114`, `:152`, and the documented size contract.

**Executed reproduction:** an otherwise valid 140,116-byte CSV with a
140,000-character location failed as "Malformed CSV" because of Python's inherited
131,072-character field limit; equivalent JSON was accepted.

**Impact:** inconsistent format behavior and misleading guidance below the whole-file
bound. **Smallest fix applied:** explicitly cap CSV/JSON decoded keys and values at
**131,072 characters**, document the contract, and make CSV parser-limit feedback
actionable. Boundary/Unicode/header/concurrent tests verify the cap and that
ingestion never mutates the process-global CSV limit. Another library can set a
lower CSV parser limit; the actual inherited limit is then reported.

### R9 — Low / P3: reset leaves a misleading selected filename — fixed

**Affected:** `streamlit_app.py:58`, `:60`, uploader key at `:91`.

**Executed reproduction:** upload `reset-case.csv`, clear the session audit, and
wait for rerun. The old filename remained visible while Validate was disabled.
The database had been deleted; this was stale widget presentation, not a retained
audit. **Smallest fix applied:** rotate uploader identity and clear error/result
state during reset. Post-fix browser checks show no selected file, no results,
and Validate disabled; another session's database is unaffected.

## Independent verification and negative results

The baseline was extracted with `git archive` into an isolated scratch directory;
it was not checked out over the user's branch. Direct coordinator reproductions
are saved in [baseline results](review_baseline_reproductions.json). Regression tests
are in `test_adversarial_ingestion.py`, `test_adversarial_integrity.py`,
`test_adversarial_validation.py`, and the expanded CLI/UI tests.

The generator was executed into a new scratch directory. Both CSV bytes and parsed
manifest equaled the committed artifacts, SHA-256
`2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21`.
A separate standard-library calculation using `csv`, `Counter`, `datetime`, `int`
and `statistics` found **50 input, 41 accepted, 9 rejected, 1 advisory**. Rejected
rows were 41–49; advisory row 50; median=11/MAD=1. It did not call the detector.
Poisoning the separate truth labels did not change validation results. Code search
and import inspection found no truth-manifest access in ingestion, validation or
repository decision logic; labels enter reporting only.

Additional executed probes support these narrower conclusions:

- Four trials of twelve concurrent first-use constructors and different files
  sharing one ID each produced 13 accepted, 11 rejected and 12 reconciled runs.
  Committed tests add four-way fresh/existing-database contention. No duplicate
  accepted ID, partial run, foreign-key violation or failed integrity check occurred.
- Forced write failures at each of the five audit tables rolled back the whole
  new run; retries succeeded. A new regression also preserves earlier committed
  history through a later failed run. Exact replay still adds no rows/findings.
- SQL-shaped ID/location values remain parameter values; input names are metadata,
  not filesystem destinations. A quoted embedded-CR export round-tripped as one
  record. Formula-like text was apostrophe-prefixed in an actual browser CSV
  download. No spreadsheet application was used to certify every CSV consumer.
- Score-boundary batches `[10]*7+[15]` produced no advisory; replacing 15 with 16
  flagged only the last row. A lawful cancellation in `[10]*7+[0]` was flagged but
  stayed accepted. Balanced `[10]*5+[500]*5` produced no flags. These are demonstrated
  heuristic false-positive/masking limitations, not model-accuracy claims.
- A row with six missing fields still counts as one rejected row and one
  `missing_value` row in reason rates. With no accepted rows, the advisory/accepted
  rate serializes as JSON `null`, not an invented zero or division error.
- Browser checks rejected 2 MiB+1 uploads; a synthetic 10,000-row input processed
  in one observed run of about 3 seconds. No memory profile or load benchmark was run.
  Fresh sessions used different temporary databases; clear removed its directory.

## Exact checks after fixes

On Linux / Python **3.12.14**, using the existing isolated environment:

```text
$ python -m pytest -q dataops-sentinel/tests
........................................................................ [ 33%]
........................................................................ [ 67%]
......................................................................   [100%]
214 passed in 23.08s

$ python -m ruff check dataops-sentinel
All checks passed!

$ python -m compileall -q dataops-sentinel
# exit 0

$ python -m pip check
No broken requirements found.
```

[Unedited pytest output](review_pytest_output.txt) and the
[current version-2 report](review_quality_report.json) are committed. Fresh CLI run
`40e415f3556e46c18b800687e277cf7f` returned 50/41/9/1, then the same ID with
`reused: true`. SQL totals were sources=1, runs=1, accepted_rows=41,
rejected_rows=9, findings=10; `integrity_check=ok`, no foreign-key violations.
The accepted CSV had 41 rows including `SYN-0050` quantity 500.

The patched Streamlit server was started on a fresh local port to avoid stale
import caches. The suite includes **9 AppTest cases**. Headless Chromium exercised
failure/rerun/recovery/reset, independent browser contexts and downloads, literal
Markdown handling, and **390×844** rendering. Mobile page/main widths were both
390 with metrics 50/41/9/1; its CSV had 41 accepted rows and retained the advisory.
[Browser evidence](review_browser_results.json) separates baseline and post-fix runs.
Remote CI results for this review commit are recorded separately in PR #16;
the previous build's green status is not evidence for this revision.

## Requirements, missing functionality and unresolved limits

| Issue #15 requirement | Reviewed disposition |
| --- | --- |
| Modular Python/pandas/SQLite/Streamlit/pytest | Present; no unnecessary service or model. |
| Deterministic synthetic feed and separate truth | Regenerated and independently reconciled; no PII or empirical claims. |
| Bounded CSV/CLI and mocked JSON/API adapter | Present; precision/decoded-text/field and truth-file bounds repaired. Live API is optional and absent. |
| Hard errors vs advisories, explanations and rates | Present; denominator/extreme/threshold/masking probes executed. General accuracy remains unknown. |
| Transactions, duplicates, provenance and replay | Present; new cross-file contention/history rollback/version-change checks passed. |
| UI, demo, upload, reports and session handling | Present; stale failures, Markdown and reset issues repaired. Download transport limit below remains. |
| Scoped CI, tests, documentation, interview guide | Present; earlier evidence retained as historical, current evidence added. No other projects/workflows changed. |
| Draft PR and no merge/deploy/release | Preserved. Human review/ownership remains to be recorded. |
| Optional manually triggered sample pipeline | Not implemented; explicitly deferred, separate from a defect. CLI exists. |

**Download transport / medium deployment limitation:** a known active Streamlit
media URL returned HTTP 200 from an independent browser context. After failed
submission it remained readable during one cleanup pass, then returned 404 after
the next rerun; a unique-content reset probe returned 404. Identical content still
referenced by another live session can keep a media URL alive. There is no claim
of immediate revocation or authenticated per-session media access. Database/UI
isolation does not change this framework property. UI and README now say to use
fictional, non-sensitive inputs. Sensitive-data hosting needs authenticated access
and a verified download/retention design; it is outside this MVP recommendation.

Other unresolved limits are not silently treated as tested features: Community
Cloud deployment, transport configuration from repository root, abrupt-process
temporary-file cleanup, cumulative storage/session quotas, hostile local filesystem
races, representative empirical evaluation, full dependency locking/security audit,
and a formal accessibility audit. The input caps are not a multi-user DoS guarantee.
The internal `Batch` has a mutable pandas frame; trusted code must pass it unchanged
from ingestion. Arbitrary programmatic mutation can invalidate provenance, but is
not reachable from the reviewed upload/CLI input paths.

No real private data, reserved research holdouts, unrelated project files, merge,
deployment or release was accessed or performed. The recommendation is based on
reproductions and executed checks, with the above boundaries, rather than on an
absence of reported failures in the original suite.

# Browser-only owner acceptance

**Status: pending. No preview URL is available yet. No hosted smoke test or human
acceptance is recorded by this document.** This walkthrough uses the existing UI
at branch `feat/dataops-sentinel-issue-15`, checkpoint `fd15c5b`. It supplements
[OWNER_ACCEPTANCE.md](OWNER_ACCEPTANCE.md) for an owner using a desktop browser or
iPad, without a local terminal, Python installation, or repository checkout.

Actual HTTPS preview URL, to record after the feature-branch preview is deployed:

```text
<FUTURE_HTTPS_PREVIEW_URL>
```

The placeholder is not a working address. If no preview URL has been supplied,
follow [PREVIEW_IPAD.md](PREVIEW_IPAD.md) to deploy from your own account without
a terminal. Wait for the actual HTTPS URL before starting, then record its address
and source-revision evidence in the blank log. Record an access/sign-in failure
instead of assuming the app was tested. The browser needs connectivity to the
preview; the demo itself uses no external data API or credentials.

Use only the bundled fictional data and the fictional malformed fixture below.
The synthetic-only feature-branch preview is authorized. Automated verification
does not complete the owner's personal review or authorize merge, release, or
production deployment/publication.

## Walkthrough

### 1. Open the preview

Open the supplied HTTPS URL in a desktop browser or iPad Safari. Expect the title
**Check a feed. Understand every finding.**, **Load synthetic demo**, and an
**Operations CSV (UTF-8)** uploader. On iPad, expand the sidebar if it is collapsed;
it contains **Clear session audit**. If this session already has results, clear
the audit before beginning so previous accepted IDs cannot alter the demo context.

### 2. Load the fictional feed and note provenance

Click **Load synthetic demo**. Expect source `synthetic_operations.csv` and:

| Input rows | Accepted | Rejected | Advisory rows |
| ---: | ---: | ---: | ---: |
| 50 | 41 | 9 | 1 |

Read the reconciliation: **50 = 41 + 9**. The advisory is one of the 41 accepted
rows. In **Audit trail**, note `run_id`, `created_at`, rule version **2**, and hash:

```text
2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21
```

**Runs in this session** should contain one run. Keep the ID for the replay check.
Fresh sessions have different run IDs/timestamps; those differences are expected.

### 3. Inspect all nine rejected rows

Open **Records and findings**. Inspect **Rejected records** and **Row-level
findings**, scrolling within the tables if necessary. Row numbers start at one
after the CSV header. Expect these rejected data rows, with original values and
explanations retained:

| Data row | ID | Reason |
| --- | --- | --- |
| 41 | `SYN-0041` | Missing required location |
| 42 | blank | Missing required business ID |
| 43 | `SYN-DUPLICATE` | Duplicate ID paired with row 44 |
| 44 | `SYN-DUPLICATE` | Duplicate ID paired with row 43 |
| 45 | `SYN-0045` | Impossible February 30 timestamp |
| 46 | `SYN-0046` | Negative quantity `-3` |
| 47 | `SYN-0047` | Quantity `10001` exceeds the maximum |
| 48 | `SYN-0048` | Cancelled status with positive quantity `10` |
| 49 | `SYN-0049` | Unsupported status `mystery` |

Both rows in the duplicate pair are rejected; the app does not arbitrarily pick
one as correct. One rejected row can have several findings, so finding totals
need not equal row totals. The [truth manifest](../data/truth_manifest.json) and
[provenance table](DATA_PROVENANCE.md) independently describe the injected changes.

### 4. Explain the accepted advisory

Find `SYN-0050`, data row **50**, quantity **500**, in **Accepted records**. Find
its `quantity_outlier` entry with severity **advisory** in **Row-level findings**.
It passes the hard rules: 500 is an integer within 0–10,000, and the completed
status permits a positive quantity. The median/MAD heuristic flags it as unusual
among otherwise accepted values. A flag requests review; it does not prove an
error or remove the row from accepted data.

In **Quality overview**, any truth evaluation applies only to these committed
synthetic bytes. Agreement with deliberately constructed labels is not evidence
of accuracy on real operations data.

### 5. Replay the exact input

Click **Load synthetic demo** again. Expect the message that this exact input
was already audited and its saved result is being shown with no rows added.
Metrics remain **50/41/9/1**. In **Audit trail**, compare the run ID, timestamp,
and hash with step 2: they should be unchanged, with **one run** in the table.

This checks exact-input replay. It does not exercise the separate policy that
rejects an already accepted business ID in a different-content file.

### 6. Upload a fictional malformed CSV and check persistent failure feedback

The existing fixture is available on GitHub at checkpoint `fd15c5b`:

- [GitHub file view: owner_malformed.csv](https://github.com/patelkavitarepo/Data-analytics-portfolio/blob/fd15c5b867920a0ac76e37de10e56bfb36843533/dataops-sentinel/docs/owner_malformed.csv)
- [GitHub file view: valid synthetic_operations.csv](https://github.com/patelkavitarepo/Data-analytics-portfolio/blob/fd15c5b867920a0ac76e37de10e56bfb36843533/dataops-sentinel/data/synthetic_operations.csv), for the rerun check below.

Open each GitHub file view and use **Download raw file** (it may appear as a
download icon or in the file's overflow menu). On a desktop, use the browser's
download/save action. On iPad Safari, use the download indicator and find the file
in **Files → Downloads**. If raw text opens instead, use the browser's download or
share controls to save that raw file to Files. Keep the `.csv` extension; do not save the GitHub
HTML page as the fixture. Its entire CSV content should be:

```csv
record_id,quantity
SYN-OWNER-BAD,10
```

Download the valid synthetic CSV to Files as well. Return to the preview. In
**Operations CSV (UTF-8)**, choose **Browse files**. On iPad, use **Choose File**
or **Browse**, whichever the system picker offers, and select `owner_malformed.csv`
from Files. Selecting a file alone does not validate it. Click **Validate uploaded
CSV**.

Expect a generic processing error with literal details naming missing columns
such as `event_timestamp_utc`, `location`, `category`, and `status`. There must be
**no old result metrics, records, or download buttons**. The earlier successful
audit stays stored, but this schema-invalid input creates no new run.

Now select the downloaded valid `synthetic_operations.csv` in the uploader, but
**do not click Validate**. This selection triggers a rerun. The error must remain
visible, with no stale successful summary or downloads. File selection must not
silently validate the replacement or restore the previous success.

### 7. Recover, download to Files, and inspect the output

Click **Load synthetic demo**. Expect the error to clear and the saved result to
return with **50/41/9/1**. In **Quality overview**, click **Quality report (JSON)**
and **Accepted records (CSV)**. On iPad, use Safari's download indicator and Files;
if a file opens as a preview, use its share/download action to save it to Files.
On a desktop, open the downloaded files from the browser's Downloads list.

Inspect `dataops_quality_report.json` using the browser/Files text preview or an
available text viewer. Check `summary.input_count=50`, `accepted_count=41`,
`rejected_count=9`, and `advisory_count=1`; check `provenance` for the same run ID,
source hash, and `ruleset_version="2"` noted earlier. It also contains findings
and the separate truth evaluation.

Inspect `dataops_accepted.csv` using Files preview or an available spreadsheet
viewer. It must contain **41 data rows plus the header**. For this fixture that
is 42 text lines; row/line display varies by viewer. Check that `SYN-0050` with
quantity 500 remains and rejected `SYN-0041` is absent. If the viewer cannot expose
the count or text clearly, record that check as unverified rather than guessing.

### 8. Reset this session

Click **Clear session audit** in the sidebar. Expect no result metrics or
downloads, no selected uploader filename, disabled **Validate uploaded CSV**, and
the choose-input guidance. Expand the sidebar first on a narrow iPad screen.
Already downloaded files remain in Files/Downloads.

Reset clears this session's temporary audit and displayed state. It is not a
guarantee that an old Streamlit download URL is immediately revoked.

### 9. Check a separate private session

In the original session, load the demo again after reset and note its new run ID.
Open the same provided HTTPS URL in a separate private browser window/profile
(or Safari's Private tab group). A new private session should show the choose-input
screen, with no inherited source, metrics, records, or downloads. If you then load
the demo there, its audit should have its own run ID and one run. The original
session should retain its own result.

This checks session state/database separation. **Known active Streamlit media or
download URLs are not authenticated per session**: someone with such a link may
retrieve its contents, and cleanup can be delayed. A private window does not
make those URLs confidential. Use fictional, non-sensitive data only.

### 10. Inspect desktop and iPad layouts

Check the input controls, metrics, tabs, explanations, downloads, and sidebar in
a desktop browser and on iPad. Rotate the iPad to landscape and check again.
Use table-internal scrolling to reach columns, and confirm buttons and error
details are reachable and readable. Record the device/browser and any clipped
content or awkward scrolling. If one device is unavailable, leave that part
unverified. This manual smoke check is not a formal accessibility audit.

## Explain the implementation in plain language

`schema.py` defines the columns, bounds, and rules version. `ingestion.py` parses
bounded CSV/JSON and hashes the original bytes. `validation.py` separates hard
failures from advisory explanations. `repository.py` writes sources, runs, the
two row cohorts, and findings to SQLite together: the transaction commits the
whole new audit or rolls it back on a write failure. `reporting.py` derives counts
and exports; `streamlit_app.py` handles input and each session's temporary store.
The separate truth labels enter reporting, not validation decisions.

Two duplicate rules apply: every repeated business ID within a file is rejected,
and an ID accepted in an earlier different-content file is rejected in that
database. Exact bytes plus the same rule version instead reuse their saved run.
Renaming identical bytes does not change the hash; reformatting does. There is
no overwrite/update workflow. Older-rule audit stores are preserved but refused
for new ingestion.

SQLite here is temporary, local, and single-instance. Restart/cleanup can erase
it; there is no durable shared storage, authentication, total storage quota,
retention guarantee, or migration tool. The advisory heuristic can flag valid
values or miss unusual ones. A hosted preview and its upload/download behavior
need actual smoke testing; this document does not establish deployment success,
production security, or human code review. The implementation and software review
were AI-assisted; record only the owner's actual steps below.

## Owner acceptance / hosted smoke log — all observations pending

Fill this table only after personally performing each item. Leave unavailable
checks blank or record them as unverified. No entry below marks acceptance.

Exact provided HTTPS URL: ____________________  Reviewed revision: ____________________

Owner: ____________________  Date: ____________________  Devices/browsers: ____________________

| Item | Observed result | Evidence / run ID / filename | Remaining issue or unverified part |
| --- | --- | --- | --- |
| 1. Provided HTTPS URL opens the intended app |  |  |  |
| 2. Fresh demo shows 50/41/9/1 and expected provenance |  |  |  |
| 3. All rejected rows 41–49 and their reasons inspected |  |  |  |
| 4. `SYN-0050` quantity 500 remains accepted with an advisory |  |  |  |
| 5. Exact replay retains the same run ID and one run |  |  |  |
| 6. Malformed upload errors; no stale results across rerun |  |  |  |
| 7. Recovery and JSON/CSV downloads verified, including 41 accepted rows |  |  |  |
| 8. Reset clears selected file/results and disables Validate |  |  |  |
| 9. Separate private session does not inherit data; media-URL limit understood |  |  |  |
| 10. Desktop and iPad, including landscape, inspected |  |  |  |

Owner acceptance decision, to record separately after review: ____________________

Human acceptance, merge authorization, release authorization, and
deployment/publication authorization remain separate decisions. This blank log
grants none of them and does not change the draft PR's status.

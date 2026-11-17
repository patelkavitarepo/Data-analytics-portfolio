# Executed verification

These are observed local results, not simulated output. The implementation was
tested on the dedicated `feat/dataops-sentinel-issue-15` branch based on main commit
`ccdfb87a3d09730b0caa49c61b510ef8c7db6b06`. The final implementation and this evidence
are committed together; identify the tested source through the draft PR's commit.

Environment: Linux, Python **3.12.14**, SQLite **3.53.1**, pandas **2.3.3**,
Streamlit **1.51.0**, pytest **8.4.2**, Ruff **0.14.5**. A clean virtual environment
was created at `/workspace/work/dataops-venv`; dependencies were installed using:

```text
python -m pip install -r dataops-sentinel/requirements-dev.txt
Successfully installed ... pandas-2.3.3 ... pytest-8.4.2 ... ruff-0.14.5 ... streamlit-1.51.0 ...
```

The install line is an abbreviated excerpt of actual pip output, not a complete
lockfile. `python -m pip check` returned `No broken requirements found.`

## Test and source checks

From the repository root, with that virtual environment's Python:

```text
$ python -m pytest -q dataops-sentinel/tests
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 8.94s

$ python -m ruff check dataops-sentinel
All checks passed!

$ python -m compileall -q dataops-sentinel
# exit 0; no output
```

The 94 collected cases include parametrized inputs. Coverage includes:

- Required/missing/extra columns, normalized collisions, invalid UTF-8, empty/ragged
  CSV, stray quotes, correctly escaped quotes and multiline fields, byte/row limits.
- Bad and impossible dates, numeric epochs, naive UTC and explicit offsets,
  daylight-saving offset distinctions, finite integer/range/status rules.
- Within-batch duplicate groups, prior accepted IDs, exact-byte replay, concurrent
  same-input submissions, and SQL-like text persisted as parameter values.
- Six simultaneous missing-field findings on one row; mixed cohort reconciliation;
  forced SQL trigger failure rolls back **all five audit tables**, followed by recovery.
- Advisory-only outlier semantics, exact fixture regeneration/hash, complete truth
  labels, separate hard/advisory confusion counts, intentionally perturbed labels
  exercising both false positives and false negatives, malformed/wrong-context truth.
- One-shot mocked JSON response, HTTP errors/offline failures, safe spreadsheet
  exports, actual subprocess CLI success/replay/errors/path collisions.
- Actual Streamlit `AppTest`: demo, repeat load, private databases across sessions,
  reset isolation, and fresh-audit guidance when earlier IDs affect fixture results.

## CLI, SQLite and fixture results

From `dataops-sentinel/`, the following exact source was used:

```text
data/synthetic_operations.csv
SHA-256: 2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21
Bytes: 3656
```

Executed with a new database (the output directory was created by Repository):

```text
$ python -m sentinel data/synthetic_operations.csv --db /workspace/work/dataops-evidence/audit.sqlite3 --truth data/truth_manifest.json --report /workspace/work/dataops-evidence/report.json --clean /workspace/work/dataops-evidence/accepted.csv
{"run_id": "e5c37f53f2c448cca53dbae07776ce43", "input_count": 50, "accepted_count": 41, "rejected_count": 9, "advisory_count": 1, "reused": false}

$ python -m sentinel data/synthetic_operations.csv --db /workspace/work/dataops-evidence/audit.sqlite3 --truth data/truth_manifest.json --report /workspace/work/dataops-evidence/replay-report.json
{"run_id": "e5c37f53f2c448cca53dbae07776ce43", "input_count": 50, "accepted_count": 41, "rejected_count": 9, "advisory_count": 1, "reused": true}
```

Direct SQL `COUNT(*)` after replay returned: sources **1**, runs **1**,
accepted_rows **41**, rejected_rows **9**, findings **10**. The run has nine
hard-error findings and one advisory. Reconciliation is **50 = 41 + 9**, with
advisory row 50 retained in the accepted export.

The saved [quality report](example_quality_report.json) is the actual generated
JSON. Hard-error confusion counts are TP=9, FP=0, FN=0, TN=41; advisory counts are
TP=1, FP=0, FN=0, TN=49. These figures describe the constructed fixture only.

## Streamlit server and browser

Executed from the repository root:

```text
$ streamlit run dataops-sentinel/streamlit_app.py --server.headless=true --server.address=127.0.0.1 --server.port=8501 --server.maxUploadSize=2 --browser.gatherUsageStats=false
You can now view your Streamlit app in your browser.
URL: http://127.0.0.1:8501

$ curl -fsS http://127.0.0.1:8501/_stcore/health
ok
```

The README's project-directory command was also started on local port 8502;
its health endpoint returned `ok`. Reading the effective configuration from that
directory returned `server.maxUploadSize = 2` and `browser.gatherUsageStats = False`.
The CI import-smoke command was executed locally and exited 0.

An initial browser pass exposed a transport limit of 200 MB in Streamlit's default
uploader and deprecated width options in server logs. The final launch explicitly
sets 2 MiB, project-directory configuration sets the same limit, and width options
were updated. The repeated browser pass verified the displayed **2 MB** limit.

Headless Playwright with installed Chromium exercised **1440×1100** and **390×844**
viewports. Both passed: 50/41/9/1 metrics, records/audit tabs, saved-run replay,
downloaded and parsed JSON summary, valid CSV upload, and schema-error feedback.
No horizontal page/main overflow, browser console warnings, page errors, or failed
requests were recorded. The restarted server produced no further warning output
during that pass. [Machine-readable browser results](browser_test_results.json)
and [desktop](desktop-demo.png)/[mobile](mobile-demo.png) screenshots are committed.
This was a headless rendering check, not a formal accessibility audit.

## Verification limits

Python 3.11 is configured alongside 3.12 in the narrowly scoped GitHub Actions
workflow; only **3.12.14** was executed locally. Remote CI status is reported
separately in the PR, and must not be inferred from local success.

Community Cloud hosting, multi-instance persistence, authentication, durability,
long-term cleanup, a live API transport and empirical detection accuracy were not
tested. There was no deployment, release or merge. Hosted SQLite is intentionally
ephemeral and isolated per session; the limits in README apply.

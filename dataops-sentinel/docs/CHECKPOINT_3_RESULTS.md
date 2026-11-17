# Project 009 — Checkpoint 3 verification and handoff

**Recommendation: READY FOR OWNER ACCEPTANCE.** No blocking defect was observed
in these executed release-candidate checks. Human acceptance is **pending**;
this recommendation does not authorize merge, release, deployment or publication.

## Candidate and scope

PR #16 was confirmed **open, draft, unmerged**, targeting `main`, with feature
branch `feat/dataops-sentinel-issue-15` at reviewed application commit
`a7b801f36a3078aaabcdf7c1057245f453bc5687`. GitHub metadata, the local commit,
and `git ls-remote` agreed. The remote `main` was still
`ccdfb87a3d09730b0caa49c61b510ef8c7db6b06` at verification.

The existing nine-defect review and regression changes remain present. This
checkpoint changes only this project's README and acceptance/deployment/portfolio
documentation, evidence, and one intentionally malformed documentation CSV.
Application modules, tests, dependencies, Streamlit configuration and the scoped
workflow are unchanged from `a7b801f`. No other project or research holdout was
changed. The complete original PR remains isolated to `dataops-sentinel/` and
its existing `.github/workflows/dataops-sentinel.yml` addition.

## Fresh automated verification

Executed from the repository root using the existing isolated environment at
`/workspace/work/dataops-venv`, Linux, Python **3.12.14**:

```text
$ python -m pytest -q dataops-sentinel/tests
........................................................................ [ 33%]
........................................................................ [ 67%]
......................................................................   [100%]
214 passed in 24.83s

$ python -m ruff check dataops-sentinel
All checks passed!

$ python -m compileall -q dataops-sentinel
# exit 0; no output

$ python -m pip check
No broken requirements found.
```

[Unedited pytest output](checkpoint3_pytest_output.txt) is saved. No new tests or
features were added at this checkpoint. The full suite includes the existing
failed-submission persistence, exact replay, concurrent-ID, transaction rollback,
timezone, JSON precision, unsafe-path and CSV-export regressions.

The reviewed commit's [DataOps Sentinel CI run #2](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/44005885333)
was rechecked and was successful for Python **3.11 and 3.12**. Local execution
here was 3.12 only. CI for the subsequent documentation handoff commit is reported
separately in PR #16; an earlier green result is not substituted for that revision.

## Fixture, SQLite and exact replay

The generator was rerun in a scratch directory. CSV bytes and the parsed truth
manifest matched the committed files exactly. Fixture size: **3,656 bytes**;
SHA-256: `2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21`.

Using the CLI from `dataops-sentinel/`, a fresh audit and accepted/report exports
were created; the identical source was then reprocessed. Commands used:

```bash
python -m sentinel data/synthetic_operations.csv --db /workspace/work/checkpoint3/audit.sqlite --truth data/truth_manifest.json --report /workspace/work/checkpoint3/quality.json --clean /workspace/work/checkpoint3/accepted.csv
python -m sentinel data/synthetic_operations.csv --db /workspace/work/checkpoint3/audit.sqlite --truth data/truth_manifest.json
```

Observed run ID: `d03f3b96b8e04818ba4d76b020ed666b`. The fresh result returned
`reused=false`; subsequent exact-input results returned the same ID and
`reused=true`, with rule version **2**.

| Result | Observed |
| --- | ---: |
| Input | 50 |
| Accepted | 41 |
| Rejected | 9 |
| Accepted advisory subset | 1 |

**50 = 41 + 9**. The advisory is included in accepted rows. A further repository
replay compared SQL counts immediately before/after:

| Table | Before | After |
| --- | ---: | ---: |
| sources | 1 | 1 |
| runs | 1 | 1 |
| accepted_rows | 41 | 41 |
| rejected_rows | 9 | 9 |
| findings | 10 | 10 |

`PRAGMA integrity_check` returned `ok`; `PRAGMA foreign_key_check` returned no
violations. The accepted CSV parsed as **41 data rows**, contained advisory
`SYN-0050` quantity 500, and excluded rejected `SYN-0041`.
[Machine-readable verification](checkpoint3_verification.json) records these results.

## Acceptance demonstration executed by automation

A **fresh** local Streamlit process was started from `dataops-sentinel/`:

```bash
streamlit run streamlit_app.py --server.headless=true --server.address=127.0.0.1 --server.port=8504 --browser.gatherUsageStats=false
```

Its health endpoint returned HTTP **200**, body **`ok`**. Headless Playwright /
Chromium passed **14 acceptance checks** covering the owner's seven-step flow:

| Walkthrough action | Actual observation |
| --- | --- |
| Load demo | Metrics 50/41/9/1; matching source hash, rule version 2 |
| Review records | Actual table payloads: 41 accepted, 9 rejected, 10 findings; three visible records/findings tables |
| Investigate advisory | `SYN-0050`, quantity 500, present in accepted table and advisory finding |
| Repeat identical input | Same browser run ID `4a626050b60a4c90aa344509061c5aed`; audit table remained one run |
| Malformed CSV | Missing-column feedback; zero result metrics and zero download controls, immediately and after another uploader-triggered rerun |
| Recover and download | Demo recovery restored four metrics/three downloads; downloaded JSON contained 50/41/9/1 and accepted CSV had 41 rows with the advisory |
| Reset | No selected filename/result/error, Validate disabled; initial guidance restored |

The malformed schema used exactly the content in
[owner_malformed.csv](owner_malformed.csv). No new audit run was added; the saved
demo audit returned on recovery. Browser console warnings, page errors and failed
requests were all empty. Table verification decoded the actual Arrow payloads
received by that browser; CSV downloads were checked with Python's standard
CSV parser.

[Browser results](checkpoint3_browser_results.json) explicitly record
`automated_agent_execution=true` and **`human_acceptance=false`**. These 14 browser
checks are separate from the 214 pytest cases. No owner sign-off is inferred.

## Deployment and owner materials

- [OWNER_ACCEPTANCE.md](OWNER_ACCEPTANCE.md): exact local setup; seven steps with
  expected behavior, proof and owner verification; module, transaction, duplicate
  and anomaly explanations; deliberately blank owner decision record.
- [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md): official deployment references,
  verified local dependency/import/path layout, exact future `main` / entry-point /
  Python 3.12 settings, and post-deployment smoke checks.
- [PORTFOLIO_BRIEF.md](PORTFOLIO_BRIEF.md): project description, 30-second explanation,
  two-minute technical demonstration, one attribution-safe XYZ résumé draft and
  a blank owner contribution log.

Dependency files are correctly beside the entry point; pinned installed runtime
versions match. Root-directory import initialization and fixture paths were checked
locally. **Community Cloud itself was not deployed or executed.** Its actual build,
effective upload/telemetry configuration, HTTPS behavior and hosted smoke results
remain unverified until authorized owner deployment. Current official documentation
and the tested pinned local launch can differ in nested-config handling; verify
the effective host configuration rather than assuming it.

## Outstanding decisions and limits

There is no observed technical blocker to **owner acceptance of the synthetic
local MVP**. The following remain gates before publication, not completed actions:

1. The owner personally completes the walkthrough, reviews the relevant code,
   records actual contributions, and supplies an acceptance decision.
2. Merge, release and deployment/publication each require explicit owner direction.
   PR #16 stays draft; no such authorization has been recorded here.
3. An authorized Cloud deployment must run its documented hosted smoke tests and
   verify effective configuration. Local success does not prove hosted success.

Only fictional, non-sensitive inputs are appropriate. Temporary, single-instance
SQLite is not durable shared storage; cleanup/restarts can erase it. Streamlit
download URLs act as bearer links and may remain readable during framework cleanup;
session reset does not guarantee immediate revocation. There is no authentication,
aggregate storage quota, production retention service or empirical accuracy claim.
The advisory heuristic can flag legitimate values or miss unusual ones.

No human review, merge, release, deployment, publication or use of real private
data was performed by this checkpoint. **READY FOR OWNER ACCEPTANCE** means the
owner now has a working, verified candidate and concrete instructions to assess it.

# Research and verification record · 2026-11-11

## Current evidence status

**Real ETF acquisition now works on GitHub-hosted Actions. Validation performance
has NOT been computed. Holdout performance has NOT been computed or revealed.**

This supersedes the initial record that all acquisition attempts were blocked:
Codex's proxy remains restrictive, but it does not describe GitHub runner access.
No model choices, frozen calendar boundaries, default cap or objectives changed.

Latest examined source audit:
[Project 006 Actions run 43074147831](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43074147831),
job `Ephemeral eight-ETF acquisition audit (no performance)` (130709468061),
branch commit `e7a5e129504d6f938f0cf63dd2f103c3bbb3a5e4`.

- Environment: GitHub-hosted Ubuntu runner, Python 3.12.
- Source: Yahoo Finance via yfinance 0.2.65, `auto_adjust=True` daily Close.
  This is the configured split/dividend adjustment convention; independent
  verification of vendor adjustments is still pending.
- Retrieval timestamp: **2026-11-11T18:04:22.713360+00:00**.
- All eight ETFs present: **SPY, QQQ, IWM, EFA, EEM, TLT, GLD, VNQ**.
- Every ETF: **2,730 valid prices, 2016-01-04 through 2026-11-10**.
- Expected/common XNYS price sessions: **2,730 / 2,730**.
- Missing sessions, duplicate rows, nonpositive prices, misaligned sessions:
  **zero**. No gap filling or asset dropping.
- Canonical audited-price SHA-256:
  `36c291470ad6301970a851b78240a1667a968f723fdd48aade86db8a92ba6a2b`.
- Prices lived only in ephemeral runner memory. No raw-price file/artifact was
  uploaded, committed or redistributed. Only quality/provenance metadata logged.
- No return metrics, optimized weights, wealth charts or holdout comparisons
  were produced from these real inputs.

A first runner audit had a reporting-schema `KeyError` after download. That
integration error was corrected and covered by a source-audit regression test;
the successful run above is the coverage evidence. Errors now identify the
failure stage and fail the audit job instead of appearing as a green acquisition.

## Independent endpoint evidence

Status-only probe in the same run, job 130709467701, started at
2026-11-11T18:04:00.122951+00:00. Fixed endpoints; 15-second request timeout;
no redirects, payload/header logging or credentials sent to market-data hosts.

| Host | GitHub-hosted runner result | Meaning |
| --- | --- | --- |
| query1.finance.yahoo.com | HTTP 200 | Chart endpoint reachable |
| query2.finance.yahoo.com | HTTP 200 | Chart endpoint reachable |
| fc.yahoo.com | HTTP 404 | Host responded; root is not a successful data response |
| fred.stlouisfed.org | TimeoutError, no HTTP status | Treasury-series access not established |
| legal.yahoo.com | HTTP 200 | Terms endpoint reachable; no license conclusion |
| www.nasdaq.com | HTTP 403 | Independent historical-reference page not accessible in this probe |

Codex/local execution still could not reach these endpoints through its proxy:
the initial Yahoo/FRED attempts received CONNECT 403; fresh status-only probes
reported safe `URLError` types without attributing an origin-server status.
No global access-failure claim is made.

## Improvements requested by Holmes

- Archived CSV analysis requires explicit `as_of` (UI and CLI), no later than
  the last complete eligible session or the snapshot's true observed date.
  Full January-2016-to-cutoff session coverage is audited. No automatic
  shortening to a stale source. Historical/stale status, exact cutoff and
  excluded rows are visible and retained in manifests.
- A cutoff cannot conceal a missing-session gap in the excluded tail of a
  longer supplied snapshot. Missing sessions inside the interval still block
  analysis. Train 2016–2022, validation 2023–2024, holdout 2025+ remain fixed.
- All-eight source audit precedes analysis, including when a subset is selected.
  A snapshot-bound independent source-review JSON must document original
  retrieval, adjustment treatment, analysis entitlement and independently
  observed reference values for each ETF. Reference checks are restricted to
  training/validation dates and consistent adjustment bases. No synthetic
  evidence is accepted as a substitute for a real source review.
- Uploaded-CSV analysis rights are explicitly separate from redistribution,
  publishing and bundling permissions. Raw prices and completed reviews with
  reference observations stay out of git; unverified templates invent no values.
- At least 60 audited holdout sessions are required before UI reveal is enabled
  or the analytical engine may evaluate it. Only synthetic tests exercise reveal;
  no real holdout performance has been examined in this work.
- Dedicated read-only GitHub workflow restores an independent acquisition path;
  existing Project 002 workflow is unchanged. No workflow computes performance.

The application can verify consistency of a human review and numeric reference
agreement, not the truth of provenance or entitlement assertions. Publisher
access and a green acquisition audit do not themselves establish use rights.

## Verification actually performed

- **74 Project 006 pytest tests passed locally**, Python 3.12. All fixtures are
  synthetic. Original calculation, covariance/objective, solver, constraints,
  leakage, common-date benchmark, drift, cost, metrics and dashboard tests pass.
- Added cutoff completeness/bounds, archived-source disclosure, gap concealment,
  CLI manifests/no unverified performance, source-review identity/adjustment/
  rights/reference checks, 59-versus-60-session holdout threshold, disabled reveal
  UI, and safe status-only/acquisition-audit logging tests.
- Chromium/Playwright desktop empty state, upload controls and 390px mobile
  layout smoke checks pass; no JavaScript page errors, no page-level horizontal
  overflow. Full analytical UI paths are tested with synthetic AppTest fixtures.
- GitHub runner run 43074147831 passed Project 006 tests at the preceding
  72-test code state, endpoint probes and the real eight-ETF audit. The final
  commit also runs the expanded suite through the same workflow.
- Existing Project 002 workflow passed on the preceding pushed revision;
  unrelated project files were not modified.

## Can real-data validation run now?

**Not yet under the review's evidence requirements.** The infrastructure/data
availability blocker is resolved on GitHub, and the full source coverage audit
passes. Remaining gates are:

1. Obtain independently documented spot checks for all eight ETFs on the same
   split/dividend adjustment basis. Nasdaq's tested page returned 403; no
   independent observations have yet been obtained or fabricated.
2. Establish and record permission for the intended analysis under the source
   terms. HTTP 200 on a terms page and yfinance's accessibility establish no
   entitlement, and redistribution permission is not assumed.
3. Bind those reviews to a legitimately retained/reacquired input snapshot and
   its explicit cutoff/hash. Then run **validation only**, using frozen settings.
   Do not reveal final holdout or tune on it during this review.

Historical FRED yield ingestion/publication lags/vintages remain deferred; the
clearly labeled 2% effective-annual risk-free assumption remains unchanged.
One holdout, selected surviving ETFs, overlapping exposures, uncertain moments,
retrospective vendor adjustments and approximate executions remain limitations.
Shrinkage, walk-forward testing and statistical inference remain deferred.

The owner retains interpretation of any later validation evidence and source
permissions. No empirical superiority claim, merge or deployment is made.

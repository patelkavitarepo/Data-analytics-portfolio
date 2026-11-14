# Project 006 industry companion · ingestion checkpoint v1

Implements [Issue #11](https://github.com/patelkavitarepo/Data-analytics-portfolio/issues/11)
on a separate branch from current main. This directory is independent of the
unvalidated eight-ETF study and the published synthetic showcase. No earlier
protocol, results, release files, permission restrictions or holdout is changed.

## Frozen ingestion contract

- Source: Kenneth French **10 Industry Portfolios [Daily]**, official CSV ZIP:
  https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/10_Industry_Portfolios_daily_CSV.zip
- Primary: **daily value-weighted industry returns**. Parse the separately labelled
  daily equal-weighted table for a separate coverage/quality audit; it is only an
  optional *future* sensitivity, never a fallback or replacement primary panel.
- Columns: NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils, Other.
  These are SIC-assigned US equity industry portfolios, not stocks, ETFs, prices,
  or necessarily executable investments. The source's within-industry weighting
  differs from a future equal-allocation-across-industries benchmark.
- Development observations: **2016-01-01 through 2024-12-31 only**, inclusive.
  No configurable extension in this checkpoint. Filter by date before converting
  return tokens. Complete source bytes may contain later observations; immutable
  private archival retention is allowed, but excluded values are never converted,
  returned, logged, inspected for performance or exposed through the audit API.
- Units: source percentage points to decimal simple returns by division by 100.
  No magnitude-based unit guessing. Reject conflicting unit declarations,
  monthly/annual rows, wrong/duplicate/reordered columns and ambiguous sections.
- Strict rejection: malformed dates, duplicate/nonmonotone development dates,
  missing values or -99.99/-999 sentinels, nonfinite values, or returns below
  -100%. No universal finite upper return cap is invented. No filling, dropping
  industries, repaired rows, optimizer or performance calculations.
- Bounded ZIP validation without extraction: exactly one expected daily CSV;
  reject traversal, encryption, extra members and excessive expansion. Local
  bytes parser only; no networking/import-time acquisition.

## Predeclared audit, before acquisition

For each weighting table separately, report only development coverage endpoints,
row/valid-cell counts, XNYS expected/missing/non-session counts and strict-parse
status. Calendar basis is a cross-check, not proof of data provenance. No return
rows, means, volatilities, wealth series, optimization, or portfolio metrics are
included. Rejection reports a safe error code; never claim a complete clean audit
when parsing stopped. Preserve the snapshot/member hashes and publisher-vintage metadata and UTC retrieval
metadata privately. Hashes identify bytes, not accuracy or historical availability.

**Point-in-time availability remains unverified**, even after successful parsing:
a current revision is not evidence of what earlier releases contained at each
simulated decision. The documented **2025 FIZ→CIZ** processing change and possible
historical revisions limit future interpretation. No historical release-vintage
comparison is performed. `performance_cleared=false` remains mandatory.

## Private-first execution

See [DATA_USE.md](DATA_USE.md). Commit this contract, safeguards and passing
synthetic-format tests **before** any real retrieval. No real French observations
are test fixtures. No acquisition runs in automatic CI, imports or app startup. There is no
app/upload/download widget and no raw CSV export.

For the proposed iPad-controlled GitHub route, see
[GITHUB_ACTIONS_AUDIT.md](GITHUB_ACTIONS_AUDIT.md). Automatic PR checks remain
synthetic-only; the separate manual worker is live-locked pending hosted-processing
scope review. It never retains an immutable raw snapshot, unlike the desktop
commands below. Default-branch dispatcher installation needs a separate narrowly
scoped owner-reviewed PR; this draft is not merged to enable dispatch.

From this directory, use a private local Python 3.12 environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
source .venv/bin/activate
```

Then run:

```bash
python -m pytest -q
python scripts/check_safety.py
# Explicit private metadata setup, based on owner's direct permission:
python -m industry_companion record-permission --permission-active
# Only after safeguards/tests are committed and permission is still active:
python -m industry_companion acquire --permission-active
# Use the snapshot_id printed above; stdout contains whitelisted metadata only:
python -m industry_companion audit --snapshot-id <sha256> --permission-active
# On rescission or uncertain continued authority:
python -m industry_companion suspend
```

Private files are POSIX owner-only (directory 0700/files 0600), ignored and
untracked. Symlinks, traversal, nonregular files, tracked/private paths and
in-place overwrites are rejected. The archive hash and required provenance fields
are checked before processing; the audit records the current metadata hash, which
is not an independent seal against owner modification. Acquisition is one explicit bounded HTTPS request to the exact
approved URL, no redirects/retry loop. A connection blocker produces a code,
not a response body. Owner-manual download remains a possible fallback: save the exact official
archive as `private/manual-download.zip`, enforce mode 0600, and register it with
truthful UTC retrieval evidence (not a backdated historical decision time):

```bash
python -m industry_companion register-local --local-name manual-download.zip --retrieved-at-utc <actual-UTC-ISO-timestamp> --permission-active
```

The manifest distinguishes owner-recorded local provenance from bounded direct
HTTPS retrieval. A source assertion alone is not independent provenance proof.
Never copy the archive into a public ticket or chat.

## What is NOT preregistered yet

No Markowitz comparison or performance analysis. A separate future protocol must
freeze objectives (min-vol/LOCAL max Sharpe), equal-industry allocation comparator,
feasible concentration cap, development train/validation boundaries, risk-free
assumption, rebalancing/execution and costs, failure handling, revision sensitivity,
and the Decision Quality evidence hierarchy. Source equal weighting is not the
same as equal allocation across primary industries. **SPY is not an authorized
benchmark** and no Fama-French factors or external price series are authorized.
Industry returns must not be assumed executable at zero tracking cost.

The original ETF 2025+ holdout stays untouched. Any companion confirmation period
requires a distinct future registration and explicit authorization; none is assigned.
A clean audit enables review of ingestion only, not empirical promotion, merge,
deployment or investment-performance claims.

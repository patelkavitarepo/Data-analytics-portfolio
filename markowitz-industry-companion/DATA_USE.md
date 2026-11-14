# Data-use scope and private-snapshot safeguards

Permission evidence: the owner reports receiving Professor Kenneth French's
explicit approval on **November 13, 2026** for the uses described in
[Issue #11](https://github.com/patelkavitarepo/Data-analytics-portfolio/issues/11).
The approval is dataset/use-specific, **raw redistribution is prohibited**, and
permission **may be rescinded**. This public document summarizes scope only.

| Use | Scope at this checkpoint |
| --- | --- |
| Limited reproducible Python/manual collection | Official daily 10 Industry Portfolios archive only |
| Educational analysis and private historical retention | Permitted as described, subject to continued authorization |
| Publication of aggregate findings, optimized weights, metrics and visuals | Permitted in principle as described; this task publishes only coverage/quality metadata, no performance |
| Raw archives, CSVs, individual return rows, reconstructible daily paths | **Prohibited redistribution**; never commit, log, upload as CI artifacts, paste into issues/chat or expose in download widgets |
| Correspondence, sender address, original email or screenshots | Private; do not commit or publish |
| Other datasets / ETF prices / direct CRSP feeds / factors / vendor/benchmark prices | **Not covered**; no inference of entitlement |

The private `permission-receipt.json` records the owner's attested scope, receipt
reference/date, UTC recording time and rescission provision. It is **not** a
fabricated copy of the correspondence or a claim that this agent inspected the
original email. No sender address or letter text is stored by this implementation.
The original correspondence, if retained by the owner, stays outside public git.

## Entry and revocation gates

Require the private scoped active receipt AND explicit current-permission
attestation before acquisition, snapshot access or audit. No automatic receipt
creation, collection or default authorization on import. Known rescission or
uncertainty markers override an active flag. A JSON record cannot establish
that permission is still active; the owner must communicate any change.

On rescission/uncertainty: stop collection, reading/auditing and derived publication;
quarantine retained snapshots pending owner review of continued retention/use and
previously derived publication. Do not automatically delete historical evidence,
re-approve access, or treat a previous grant as perpetual. `suspend` creates an
immutable marker and cannot be overridden by `--permission-active`.

## Storage and disclosure

Only `private/` under this project is accepted by the storage wrapper. Require
Git-ignore coverage, reject already tracked files and symlinks/traversal, enforce
0700/0600 and regular files, and use exclusive creation instead of overwrite.
Snapshots use SHA-256 names; new revisions get new bytes/hash and a new manifest.
The original archive is immutable, with UTC retrieval/source/manifest metadata.
This implementation targets a POSIX private local workspace; other platforms need
a reviewed equivalent access-control mechanism.

The parser consumes explicitly supplied local bytes and exposes only 2016–2024
rows for private processing. Never print its data arrays. Object representations
are redacted; public-safe error codes do not echo values, lines, headers, private
paths or HTTP bodies. CLI audit output is a fixed metadata schema, not arbitrary
source contents. Private audits/manifests remain ignored. Any public summary must
be reviewed for aggregate-only content and reconstruction risk.

Git ignore rules and CI guards are defense in depth, not protection against an
owner intentionally rewriting code or force-publishing data. The metadata guard
cannot establish licence truth, economic accuracy, point-in-time validity or
honest source assertions. Human review remains necessary. Never stage `private/`
or upload it as a workflow artifact; CI uses invented synthetic format fixtures.

## Provenance and methodological limitations

Official library: https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html

Official construction: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html

These are US equity industry portfolios assigned using SIC classifications, with
value- and equal-weighted stock aggregation within each industry. They are not
individual stocks, investable ETFs or executable adjusted prices. Source return
units are percentage points, not a price panel; splitting/reinvestment/market
microstructure cannot be treated like ETF execution assumptions.

Retain publisher CRSP-vintage metadata when present and flag it unknown when not.
The library describes a 2025 FIZ→CIZ processing change; history can be revised.
Current downloads do not prove historical publication/availability at earlier
simulated decisions. No historical-vintage reconstruction or independently
entitled return verification has been completed. Calendar completeness is not
point-in-time correctness. This checkpoint always reports
`point_in_time_verified=false` and `performance_cleared=false`.

No original ETF entitlement, holdout use, strategy tuning, public release, merge
or deployment is authorized. Future optimization/performance needs separate
preregistration and owner instruction.

## Proposed hosted execution is a separate unresolved scope

[GITHUB_ACTIONS_AUDIT.md](GITHUB_ACTIONS_AUDIT.md) describes a GitHub-first
metadata-only route controlled from iPad. Transient raw bytes on a GitHub-hosted
VM are third-party processing; the existing approval does **not** establish that
this is covered. The separate `github_actions_scope.json` therefore remains
pending with live processing disabled. Manual checkboxes cannot change that
record or supply missing authority. No live GitHub acquisition is authorized by
this implementation.

Automatic CI remains synthetic-only. A future reviewed manual worker uses a
separate memory-only adapter and cannot claim the desktop `PrivateStore`'s
retained private snapshot. It creates no on-disk raw archive, manifest or receipt.
Provider access/retention and service terms remain part of the owner scope review;
not publishing raw files is necessary but does not itself settle that review.

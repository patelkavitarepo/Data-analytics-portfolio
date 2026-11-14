# Checkpoint 1 · ingestion implemented, source audit blocked

Status: **synthetic-format verification complete; no real archive acquired or
real-data quality finding established**. This is not a portfolio experiment.
Implements [Issue #11](https://github.com/patelkavitarepo/Data-analytics-portfolio/issues/11).

## What has been verified

- The ingestion contract, private storage, permission gates and 76 synthetic
  tests were committed in `6a8864c` before the first source request. Documentation
  clarification followed in `3a4fee2`; acquisition occurred after both commits.
- The final checkpoint has **79 passing tests**, using invented format fixtures
  only. Tests cover both daily weighting sections, percentage-point conversion,
  fixed 2016–2024 filtering, invalid/missing inputs, fingerprints, immutable
  snapshots, permission suspension, owner-only paths, output redaction and a
  local manual-registration fallback. Real market observations are not fixtures.
- A clean Python 3.12 environment installed the pinned dependency closure and
  ran the suite. The tracked-file/source guard passes; CI runs synthetic tests
  and the guard, with no source acquisition, secrets or raw artifact upload.
- The owner's dataset-specific permission has a private, ignored owner-attested
  scope receipt. No original letter, sender address or correspondence was copied.
  No raw archive or observations are tracked. This does not independently
  authenticate correspondence or make the rescindable grant perpetual.
- Work is isolated on `project-006-french-industry-ingestion`, based on main
  `996be24941d234840f14f66e42e1e6ddb7c30684`. Only this new companion directory
  and its dedicated test workflow change. Existing ETF research, synthetic
  releases, numerical evidence and the original holdout are untouched.

## Access evidence and unresolved source questions

One explicit bounded acquisition was attempted against the exact official daily
archive after the safeguards were committed. It returned the safe local code
`SOURCE_CONNECTION_BLOCKED_OR_UNAVAILABLE`. A subsequent status-only connection
diagnostic reported **proxy CONNECT 403**, with no publisher HTTP response
(`000`). The managed environment's enforced allowlist does not include
`mba.tuck.dartmouth.edu`. This establishes an **environment access blocker**, not
a publisher refusal, licensing denial or evidence that the dataset is unavailable.
No alternative mirror, proxy bypass or unrelated dataset was used.

| Question | Evidence at this checkpoint |
| --- | --- |
| Actual archive/member schema matches parser | **Unknown**; strict parser tested only against invented format mimics |
| Actual value-weighted and equal-weighted historical endpoints | **Unknown**; no source observations acquired |
| Complete 2016–2024 daily coverage and panel alignment | **Unknown**; no real missing/session counts calculated |
| Source missing sentinels, nonfinite or impossible returns | **Unknown**; rejection logic tested synthetically, not a clean-data claim |
| Actual publisher CRSP vintage and snapshot fingerprints | **Unavailable** until a real private snapshot is retained and parsed |
| Historical point-in-time release availability | **Unverified**; current retrieval would not establish earlier releases |
| Economic accuracy or independent return verification | **Unverified**; calendar/schema validation would not establish either |
| Portfolio performance, concentration or optimization quality | **Not calculated**; outside this checkpoint |

Unknown quality is not zero anomalies. No real row counts, return statistics,
portfolio weights or performance conclusions can be reported. The documented
FIZ→CIZ processing change in 2025 and potential historical revisions remain
methodological limitations from the issue/source documentation; this task has
not independently compared historical vintages.

## Narrow next step

Allow the official Dartmouth domain in the managed environment and retry the
single bounded acquisition, or have the owner manually save the official archive
to the ignored owner-only path and register its actual UTC retrieval time using
the commands in [PROJECT_PLAN.md](PROJECT_PLAN.md). Manual registration records an
owner source assertion, not independently authenticated provenance. Never upload
the archive to GitHub, CI artifacts or chat.

Then run the private audit on the immutable snapshot and review only the
2016–2024 aggregate coverage/quality metadata for each weighting panel. If the
real format differs, stop with a safe code and review a versioned parser change;
do not silently substitute a panel, repair values or broaden dates. Even a
complete audit must retain `point_in_time_verified=false` and
`performance_cleared=false`. Optimization needs separate preregistration and
owner instruction. No merge, deployment or release is part of this checkpoint.

# GitHub-first checkpoint · synthetic verification, live locked

Historical checkpoint at the commits cited below. The owner subsequently
installed PR #13 and completed a synthetic manual run. See
[HEAD_PREFLIGHT.md](HEAD_PREFLIGHT.md) for the next proposal; the earlier
unmerged-launcher statements below record the status when this checkpoint was written.

Responds to [Holmes's updated PR #12 review](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6869845274).
The original [79-test ingestion checkpoint](AUDIT_CHECKPOINT.md) and all earlier
research remain preserved. This adds execution infrastructure, not an experiment.

## Verified locally

- **150 tests pass:** the existing 79 tests, 56 hosted-runtime tests and 15
  workflow safety tests. Tests were written and observed failing for missing
  implementations before the new worker/validator was added.
- All source-format fixtures are invented. Hosted acquisition tests use mocked
  responses only; a global network prohibition remains active during tests.
- Tests cover pending/revoked scope, owner/ref/repository/SHA checks, missing
  acknowledgements/current-enable switch, reruns, debug/fault-handler rejection,
  source cutoffs, memory-only cleanup and raw-field injection rejection.
- Workflow mutations adding automatic triggers, write access, cache/upload-like
  extra steps, mutable action/code references, tracing or unsafe runner settings
  are rejected. Validation also rejects unsafe input under optimized Python.
- actionlint **v1.7.7** accepts the proposed dispatcher and automatic companion
  workflow. Its downloaded release binary was checked against the publisher's
  SHA-256 checksum. First-party action tag/commit mappings were independently
  checked with Git refs; the workflows use full immutable action SHAs.
- The default CLI was executed with synthetic bytes only and produced a safe,
  explicitly synthetic metadata report. No source archive was requested.

[GitHub CI run 43545095913](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43545095913)
confirmed all **150 tests**, both safety guards and synthetic CLI execution at
`38e0ee29e83b75d419bd3935e9985027e89e1c8f`. The logs were checked for synthetic
labelling and the mandatory false performance/point-in-time/retention flags.

## Reviewed design

Automatic PR tests and the manual `workflow_dispatch` path are separate. Manual
mode defaults to synthetic; live mode requires an exact reviewed code pin,
owner-only first-attempt dispatch on the companion branch, current acknowledgements,
an enabled current repository switch and a separately approved hosted-processing
policy. The committed policy remains **pending**, with live processing disabled.
No repository switch was enabled or cloud authority asserted by this task.

The worker reuses the existing bounded official-URL acquisition function, unchanged
parser/calculations and coverage audit. Its separate adapter keeps raw bytes in
process memory, never the checkout, a retained snapshot, logs, caches or artifacts.
Only the strict metadata schema reaches output. There are no upload, callback,
notification, generated-commit or artifact steps. Cleanup releases references,
not a claim of certified erasure or protection from service-operator access.

The runtime guard checks the workflow in the pinned code checkout. Owner review
and PR tests must also verify the actual branch-selected launcher; the worker
cannot authenticate or restrain a privileged editor's rewritten workflow.

## Unresolved before a real-data run

1. **Rights scope:** transient raw processing on GitHub-hosted infrastructure is
   not established by the existing grant. The owner must review that scope and
   service terms, seek clarification if needed, and record a dated public scope
   summary without correspondence or raw observations. A checkbox is insufficient.
2. **Dispatch availability:** GitHub's manual UI requires the workflow file on the
   default branch. [Workflow-only draft PR #13](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/13) is open for owner review;
   neither it nor PR #12 is merged by this task. Keep both launcher copies aligned.
3. **Operational verification:** default-branch installation, iPad UI operation,
   a manual hosted run, and Dartmouth connectivity from that runner remain
   unverified. The prior Codex proxy failure is not evidence about GitHub access.
4. **Real data:** actual format compatibility, vintage, historical endpoints,
   2016–2024 coverage and source anomalies remain unknown. No real archive was
   downloaded here. A successful future audit would still not establish economic
   accuracy, historical point-in-time releases or byte-for-byte repeatability
   without a separately authorized owner-controlled archive.

Follow [GITHUB_ACTIONS_AUDIT.md](GITHUB_ACTIONS_AUDIT.md) for exact iPad controls,
permission gates, revocation steps and safe-output review. No optimization,
performance finding, original ETF/holdout access, synthetic-release change, merge
or deployment is part of this checkpoint.

Reviewed implementation candidate pinned by the launcher: `ce26ac525f95dac4e6a14a23ed4de41746d51da6`.
The pending policy in that commit cannot be opened by dispatch inputs.

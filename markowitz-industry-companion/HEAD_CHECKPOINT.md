# HEAD preflight and protocol draft · synthetic verification only

Implements [Holmes's next PR #12 checkpoint](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6870252210).

## Verified evidence

- The owner's [manual synthetic run 43546213342](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43546213342)
  passed. Job/log inspection confirmed **150 tests**, synthetic labelling and
  false point-in-time/performance/durable-snapshot flags; no artifacts exist.
  This verifies the original iPad-controlled synthetic route only.
- The updated local suite has **208 passing tests**: the earlier 150, **53**
  HEAD tests and **5** additional workflow mutations. New tests were observed
  failing before implementation. All responses/handlers are mocked; network
  connections remain forbidden in tests.
- HEAD tests cover 2xx, redirects, 403, 405, timeout/connection errors, hostile
  headers/body traps, no body/error-response consumption, exact URL/HEAD/timeout,
  one open attempt, wrong-request refusal before opening, safe output and
  manual-context/pin/debug rejection. A real urllib handler chain is exercised
  with a fake HTTPS handler and no socket connection.
- Both workflow guards pass, including optimized-Python validation. Local
  actionlint v1.7.7 accepts both workflows. Synthetic remains the default; no HEAD
  request is added to automatic CI or ordinary synthetic runs.
- Independent read-only review found no critical HEAD path or raw-gate bypass
  within the documented owner/platform trust boundaries. The unchanged raw scope
  file remains `pending_owner_rights_review`, `live_enabled=false`.

## Implemented, not empirically verified

The manually selected `head` mode requires a separate explicit acknowledgement
and reviewed code SHA. It returns only a coarse status and UTC timestamp, never
response bodies/headers, raw archives, return rows or coverage claims. There is
no GET, range fallback, redirect following or retry. HTTP errors are closed
without reading their bodies. HEAD 2xx does not prove GET works; 405 and other
non-2xx statuses remain inconclusive about GET.

**No actual HEAD or GET request to Dartmouth was made in this task.** No raw
archive was acquired, parsed or published. Connectivity from GitHub, actual
archive format/quality/vintage and historical release availability remain unknown.
No optimization or empirical outcome analysis was run.

[EMPIRICAL_PROTOCOL_DRAFT.md](EMPIRICAL_PROTOCOL_DRAFT.md) is explicitly
`DRAFT_NOT_FROZEN`. It proposes 2016–2020 initial estimation and 2021–2024 paired
comparisons, a 60-month window, equal-industry/minimum-variance/local-Sharpe rules,
35% target cap, lagged monthly hypothetical execution, constant risk-free/cost
assumptions and a decision-quality metric hierarchy. These are review candidates,
not fixed choices or findings. Post-2024 confirmation remains unassigned,
unexamined and unauthorized; nothing changes the original ETF protocol/holdout.

## Remaining questions and exact next checkpoint

The unresolved rights question is whether the described publisher grant covers
transient processing of raw licensed archives on a third-party GitHub-hosted VM.
GitHub's software-testing terms, memory-only handling and a successful HEAD do
not answer it. Owner evidence review or, if necessary, publisher clarification
is required; no licensing email or self-approval occurs here.

Prepare the separate launcher-only draft from current main and let the owner
review its immutable code pin and manual settings. Do not alter merged PR #13,
merge either current draft or modify main. After owner-approved installation,
the next checkpoint is **one owner-initiated HEAD run**, with `mode=head`,
`head_only_ack=true`, exact reviewed SHA, both raw acknowledgements false and the
raw switch left disabled. Record only the run URL, coarse result and UTC time,
then stop. Follow [HEAD_PREFLIGHT.md](HEAD_PREFLIGHT.md) for exact iPad steps.

Only a later separately authorized scope decision can precede a coverage audit;
only later review/freeze and explicit instructions can precede optimization.
No archive acquisition, original ETF/holdout access, synthetic-release change,
merge, deployment or permission expansion is authorized by this checkpoint.

# Manual HEAD-only connectivity checkpoint

Responds to [Holmes's checkpoint](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12#issuecomment-6870252210).
This diagnoses the ingestion software's route to the official source. It does
not acquire an archive or establish permission to process raw data on GitHub.

## Verified evidence and current limits

The owner's iPad-dispatched [synthetic run 43546213342](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43546213342)
succeeded: its logs show **150 tests passed**, `evidence_kind=synthetic_format_fixture`,
`point_in_time_verified=false`, `performance_cleared=false` and no retained
snapshot. The run has no artifacts. This verifies the installed synthetic path,
not Dartmouth connectivity or real-data quality. The owner installed the initial
launcher through PR #13; this task does not alter that merged PR or main.

The new HEAD path has only been exercised against synthetic/mock responses.
No real HEAD or GET request was made by this implementation task. Actual
GitHub-to-Dartmouth HEAD reachability, GET behavior, archive compatibility,
coverage and vintage remain unknown. The older managed-Codex CONNECT 403 cannot
answer these GitHub-runner questions.

## Contract and isolation

- Exact destination is the existing approved daily 10 Industry Portfolios ZIP
  URL in `safeguards.SOURCE_URL`; no URL, method, range or date input exists.
- One explicit **HEAD** request, timeout 20 seconds, no redirects, retries,
  range request or fallback GET. Request method/URL/empty body are checked before
  opening. Replacement urllib status processing returns responses directly,
  avoiding redirect handlers that may inspect destinations or drain bodies.
- The application never reads response bodies or headers, parses an archive,
  stores data, invokes `acquire_private` or invokes a portfolio calculation.
  Responses/errors are closed without consumption. Networking necessarily
  processes HTTP protocol headers internally; no application header dump occurs.
  This is not a certified claim about hostile-server/network-buffer behavior.
- Output is exactly `result` plus `checked_at_utc`. No HTTP code, response text,
  header, cookies, private IP, path, URL token, hash, vintage or coverage finding
  is emitted. An authorization failure stops before networking with a safe code.
- Manual owner/triggering-owner, repository, companion ref, first-attempt,
  GitHub-hosted runner, no-debug and immutable code-pin checks remain required.
  `head_only_ack=true` explicitly opts in. Synthetic is still the default; PR
  tests and normal synthetic runs never issue a real HEAD automatically.
- HEAD deliberately does not open the **raw** permission gate. It requires
  neither a raw-processing acknowledgement nor an enabled raw-processing switch.
  The committed scope policy stays `pending_owner_rights_review` and
  `live_enabled=false`; even all live acknowledgements cannot override it.
- Read-only token, no persisted credentials, no artifact/cache/upload/callback
  or generated-commit steps, pinned setup actions and workflow mutation guards
  remain in force. Scope review, not memory-only handling, determines whether
  future raw hosted processing is permitted.

| Coarse result | Interpretation |
| --- | --- |
| `REACHABLE_HEAD_2XX` | A HEAD request received a 2xx status. It does not establish GET success, source contents, data quality or processing rights. |
| `HEAD_UNSUPPORTED_OR_NON_2XX` | An HTTP non-2xx response, including redirects, denial or unsupported HEAD. **405 is inconclusive about GET.** Do not follow a destination or substitute GET. |
| `BLOCKED_OR_UNAVAILABLE` | No usable HEAD status was obtained, e.g. timeout or connection/proxy failure. No private network diagnostics are published. |

The exact status code is intentionally not printed. Consult this interpretation
for all non-2xx results rather than using the workflow as a probe loop.

## Exact next checkpoint, controlled from iPad

1. Review PR #12's implementation, synthetic CI, actionlint and
   [EMPIRICAL_PROTOCOL_DRAFT.md](EMPIRICAL_PROTOCOL_DRAFT.md). The protocol stays
   unfrozen; no optimization or archive is needed to review it.
2. Review the **new launcher-only draft PR** based on current main. It updates
   only `.github/workflows/industry-companion-audit.yml` and pins the tested HEAD
   implementation. Leave it unmerged until owner approval. Do not modify PR #13
   retrospectively, merge the full research PR or change the default branch.
3. Only after the owner approves and installs that launcher, check that both
   default-branch and companion-branch copies match. GitHub executes the selected
   branch's definition; runtime validation of the pinned checkout does not
   independently authenticate the launcher GitHub started.
4. In Safari: repository **Actions → Industry companion manual coverage audit →
   Run workflow**. Select branch `project-006-french-industry-ingestion`, set
   `mode=head` and `head_only_ack=true`, and copy the launcher's full pinned SHA
   into `reviewed_code_sha`. Leave `permission_active=false` and
   `ephemeral_processing_ack=false`. Do not enable the raw repository switch.
5. Authorize **one new first-attempt run**. Monitor its audit job, inspect only
   the two-field HEAD result, and record the run URL, coarse result and UTC time.
   A green job means the diagnosis ran; the `result` determines its meaning.
   Do not click Re-run jobs, change to GET, follow redirects or retry repeatedly.
6. **Stop after reporting that result.** Hosted raw-data rights remain unresolved
   whatever HEAD reports. Any network/code correction is a new reviewed step;
   a HEAD success does not authorize acquisition or optimization.

This task neither merges the launcher nor dispatches it. Current main's older
launcher does not establish that the new HEAD UI/path has been installed/tested.
The existing passing synthetic default is preserved.

## Rights question and later decisions

Professor French approved the described limited Python collection, private
educational analysis/retention and aggregate-derived publication, prohibited raw
redistribution and retained rescission rights. Does that permission cover raw
licensed-archive bytes being transiently processed on a **third-party
GitHub-hosted/cloud-provider VM**, under the applicable service terms? The
available evidence does not resolve this question. A private, ephemeral buffer
and green CI do not establish a grant. If owner review of the permission cannot
establish coverage, publisher clarification is needed; no email is sent here.

The [Actions additional product terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)
limit hosted work to the associated software project/development/testing; this
bounded diagnostic tests ingestion software, not a general research compute
service. Those terms do not license the French data.
[Hosted-runner documentation](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
also makes the cloud-provider trust boundary relevant. See
[GITHUB_ACTIONS_AUDIT.md](GITHUB_ACTIONS_AUDIT.md) for service-term and retention
limitations and revocation controls. No original correspondence belongs in git,
logs, comments, inputs or artifacts.

After HEAD, resolve scope separately before proposing any authorized coverage
audit. After actual coverage evidence is reviewed, a separately approved frozen
empirical protocol and explicit instruction are required before outcome analysis.
No step opens the next automatically. The original ETF holdout, post-2024
companion returns and published synthetic showcase remain outside this work.

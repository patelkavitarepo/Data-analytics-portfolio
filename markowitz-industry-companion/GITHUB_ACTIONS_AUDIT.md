# GitHub-first coverage audit · proposed, live processing locked

The iPad is the control surface: the owner can review code, initiate a manual
workflow and inspect safe metadata in GitHub's web interface. No Mac, Codespaces
session or iPad Python installation is required for this proposed route.

**Current status:** synthetic verification only. No live French archive has been
downloaded through this workflow. Existing permission does not yet establish
whether transient processing on a GitHub-hosted VM is within the approved scope.
The committed `github_actions_scope.json` records
`status="pending_owner_rights_review"` and `live_enabled=false`. The live gate
remains closed pending an explicit scope review and workflow review.
A separate current-permission repository-variable gate is also required; this
implementation does not configure or enable that variable.
A passing synthetic run would establish neither real source access nor coverage.

## Permission boundary

Professor French approved the described educational use of the **daily 10 Industry
Portfolios** dataset, limited reproducible collection, private historical retention
and publication of derived aggregate findings. Raw redistribution is prohibited;
permission may be rescinded. See [DATA_USE.md](DATA_USE.md). These are industry
return portfolios, not individual stocks, ETFs or executable prices.

A GitHub-hosted runner is a third-party execution service. Even if the job keeps
raw bytes out of the repository and public outputs, the bytes would transiently
exist in that service's memory. Neither an ignored path nor
an owner acknowledgement resolves whether this is permitted. Before enabling
live processing, the owner must review the publisher grant together with the
relevant GitHub service terms, establish whether this particular processing is
authorized, and obtain clarification if the grant remains ambiguous. Record only
a dated public scope summary/review reference; retain original correspondence
privately. Do not publish an email, sender address or screenshot as evidence.

If this review cannot establish authority, leave the live gate closed and retain
the owner-controlled local audit as a fallback. Do not upload the archive to
GitHub, ChatGPT, an online notebook or another hosted execution service to work
around the decision. Rescission or uncertainty stops acquisition and further use;
set `FRENCH_INDUSTRY_EPHEMERAL_ENABLED=false` or delete it, cancel any in-flight
run and disable the manual workflow. Review already published metadata and
retained private copies separately. Changing a variable does not retroactively
stop a job that already captured its value, so cancellation is also necessary.

## Two separate paths

| Path | Trigger and data | What it establishes |
| --- | --- | --- |
| Automatic companion tests | Pull requests; invented deterministic format fixtures only | Parser, cutoff, output and workflow guards behave as tested |
| Proposed manual coverage audit | `workflow_dispatch`; synthetic mode by default; live mode separately gated | Only after authorization and successful execution: actual 2016–2024 coverage metadata |

There is no push/schedule/PR-triggered live acquisition. A manual synthetic run
does not contact Dartmouth. A live run, once legitimately enabled, makes at most
one bounded request to the exact approved URL, with no redirects or retries:

`https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/10_Industry_Portfolios_daily_CSV.zip`

GitHub-hosted connectivity is distinct from the managed Codex proxy that returned
CONNECT 403. GitHub access **may work but is unverified**. Do not repeatedly retry
a failed real-data job or use GitHub's re-run control to cause another download.
Review a safe failure code, make any needed reviewed correction, and authorize a
new first-attempt manual run instead.

## Why the Run workflow button is not available yet

[GitHub requires a `workflow_dispatch` file on the default branch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
and repository write access before the manual interface is available. PR #12 deliberately remains draft; its
presence on a feature branch does not make this workflow dispatchable from the
Actions interface. Do not merge PR #12, change the default branch or modify the
original ETF branch to work around this restriction.

After review, propose a **separate, narrowly scoped workflow-only PR** for the
owner's approval. Its launcher must check out an explicitly reviewed immutable
commit from `project-006-french-industry-ingestion`, not mutable branch-head code.
The owner decides whether and when to approve and merge that separate launcher.
That decision is outside this implementation; no merge is performed here. The
launcher must retain all permission gates and the synthetic default. Any changed
code SHA requires another review and launcher update, not an arbitrary dispatch
input that bypasses the pin.

GitHub executes the workflow version on the selected dispatch branch. The
default-branch copy makes the UI available; keep it and the companion-branch
copy identical when installing or repinning the launcher. Review the selected
branch's file, not only the default-branch copy.

## iPad process after the prerequisite reviews

1. In Safari, open [draft PR #12](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/12).
   Review the latest code, workflow and synthetic CI results. Confirm the exact
   immutable code SHA used by the reviewed launcher. Do not infer authority from
   a green check.
2. Complete and record the third-party processing scope review described above.
   Keep live processing disabled unless the review establishes that it is
   authorized and the permission remains active. Review the public policy record
   and launcher through normal GitHub changes; do not paste private evidence or
   raw data into a workflow input, variable, secret, comment or attachment.
3. If the owner approves the separate workflow-only PR, install its reviewed
   launcher on the default branch. Confirm that it still checks out the approved
   fixed SHA and accepts dispatch only for the companion branch.
4. Open the repository's **Actions** tab, select **Industry companion manual
   coverage audit**, and choose **Run workflow**. Select the exact companion
   branch `project-006-french-industry-ingestion`. Run **synthetic** mode first;
   leave live acknowledgements unset. Wait for all checks to pass, then inspect
   the synthetic-labelled metadata JSON in the run log. This step uses no market
   data.
5. Only after the scope and workflow gates are reviewed and legitimately opened,
   open repository **Settings → Secrets and variables → Actions → Variables**
   and set `FRENCH_INDUSTRY_EPHEMERAL_ENABLED` to the literal string `true`.
   This is a current owner-controlled switch, not a place for private permission
   evidence, secrets or correspondence. Then initiate a new **live** run.
   Set `mode=live`, `permission_active=true` and
   `ephemeral_processing_ack=true`; set `reviewed_code_sha` to the exact full SHA
   hardcoded in the reviewed launcher. An acknowledgement is a statement of
   current facts, not a new grant, and cannot enable a pending or disabled policy.
   Never provide an alternative URL, arbitrary code reference or date range.
6. Monitor the run in **Actions**, including its first-attempt status. Inspect
   only the final metadata JSON or stable safe failure code. Do not enable
   runner/step debug logging, add print statements, download raw artifacts or
   share screenshots that might disclose private inputs. On a failure, stop for
   review instead of clicking **Re-run jobs**.
7. For a successful live audit, review both weighting panels separately and share
   only the approved coverage/hash metadata. Keep `point_in_time_verified=false`
   and `performance_cleared=false`. No optimization or empirical performance work
   follows automatically; that requires separate preregistration and instruction.

The launcher is `.github/workflows/industry-companion-audit.yml`. Its inputs are:

| Input | Default | Live requirement |
| --- | --- | --- |
| `mode` | `synthetic` | Explicit `live` choice |
| `permission_active` | `false` | Current scoped permission remains active |
| `ephemeral_processing_ack` | `false` | Previously reviewed GitHub-hosted processing is authorized |
| `reviewed_code_sha` | Empty | Exact full immutable SHA pinned in the launcher |

Both the initiating and triggering actor must be the owner account
`patelkavitarepo`, the repository must be
`patelkavitarepo/Data-analytics-portfolio`, and the dispatch ref must be
`refs/heads/project-006-french-industry-ingestion`. Only run attempt 1 is accepted.
A future approved policy change requires a new reviewed code pin; a checkbox or
arbitrary SHA input cannot open the current policy. These steps do not assert
that default-branch installation, scope authorization or a real run has occurred.

The runtime workflow guard examines the file in the pinned code checkout; it
does not independently authenticate the later launcher revision GitHub started.
Automatic PR tests and owner review must verify that the installed/selected
launcher matches the reviewed file. A privileged workflow editor could add a
disclosure step outside the worker; the worker cannot prevent that rewrite.

The repository Actions variable `FRENCH_INDUSTRY_EPHEMERAL_ENABLED` is evaluated
for the dispatched run and passed to the worker as `HOSTED_PROCESSING_ENABLED`.
Only the exact string `true` is accepted; absent, empty or `false` blocks live
processing even if the pinned policy and input acknowledgements permit it.
Historical pinned policy alone cannot establish that a grant is still active.
The present policy remains pending and disabled, and the variable has not been
configured by this implementation. This additional switch and current owner
acknowledgements reduce accidental stale authorization; they cannot establish
licence truth or remove trust in the privileged owner and service operator.

## Ephemeral handling and its limits

- Use a GitHub-hosted Ubuntu job with read-only `contents: read`, no persisted Git
  credentials, reviewed immutable source and pinned first-party setup actions.
  No unreviewed third-party action should run after raw data enters the job.
- Keep source bytes **in memory only**, using an explicitly separate ephemeral
  adapter, not the desktop `PrivateStore`. Do not create ZIPs, manifests or
  permission receipts on disk. Never stage/generated-commit raw content. No raw
  artifact upload, cache, callback, notification or persistent workspace copy is
  part of the job.
- Emit only a strictly validated metadata whitelist of coverage dates/counts, missing/non-session
  counts, hashes, vintage and safe status fields. No source return observations,
  response bodies, paths, exception text, means, wealth series or portfolio
  metrics are permitted in logs. There is no artifact or summary widget. Metadata
  is still publicly visible in a public repository and needs reconstruction-risk
  review.
- Perform dependency setup before acquisition; keep raw data out of dependency
  caches. Never enable command tracing or GitHub debug logging for a live run.
  Cancellation/failure can interrupt application cleanup: runner disposal and
  service-provider handling remain part of the trust boundary, not a proof of
  secure erasure. The implementation cannot prevent a privileged owner from
  rewriting a workflow or the service operator from accessing its infrastructure.
- Retain **no immutable raw snapshot in GitHub**. Hash/UTC/code/dependency metadata
  identify the observed input and processing but cannot reproduce it if the
  publisher later revises the archive. A separately authorized owner-controlled
  private archive is needed for longer-term byte-for-byte reproducibility; it
  must not be uploaded back to GitHub to fill this gap.

[GitHub's hosted-runner documentation](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
describes a new VM for standard hosted jobs and regularly updated runner images.
That is an execution-isolation property, not legal permission, certified erasure
or a fully frozen operating system. The workflow records dependency/code versions
but cannot promise an identical future runner image.
[GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
supports least privilege and full-SHA action pins and warns against relying on
automatic log redaction. Reviewed setup pins are `actions/checkout` v4.2.2
(`11bd71901bbe5b1630ceea73d27597364c9af683`) and `actions/setup-python` v5.6.0
(`a26af69be951a213d495a4c3e4e4022e16d87065`); changing either needs review.

Only development rows from **2016-01-01 through 2024-12-31** may reach numerical
conversion, with value-weighted primary and equal-weighted independently audited.
No Mon–Fri approximation replaces the pinned XNYS session audit. Calendar/schema
completeness is not economic verification or evidence of historical publication
at simulated decision times. Current vintages, revisions and the 2025 FIZ→CIZ
change remain limitations. The original eight-ETF study, its untouched holdout
and the published synthetic showcase are outside this companion workflow.

# Streamlit Community Cloud deployment readiness

**Configuration validated locally; Cloud not executed.** This checkpoint reviewed
commit `a7b801f36a3078aaabcdf7c1057245f453bc5687` for Checkpoint 3. Owner authorization
for merge and publishing remains pending. No merge, deployment, Cloud account
change, secret, or repository-root configuration change was performed.

## Future owner procedure

After the owner approves the reviewed change and authorizes publishing:

1. Merge the reviewed pull request into the repository's `main` branch. Confirm
   that the merged tree contains this project's entry point, runtime requirements,
   `sentinel/` package, and synthetic `data/` files.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with the
   GitHub account authorized to deploy this repository. Create a new app with:

   | Setting | Value |
   | --- | --- |
   | Repository | `patelkavitarepo/Data-analytics-portfolio` |
   | Branch | `main`, after the owner-authorized merge |
   | Main file path | `dataops-sentinel/streamlit_app.py` |
   | Advanced settings → Python version | Explicitly select **3.12** |

3. Keep credentials and secrets empty: the app uses bundled fictional data and
   local SQLite, with no external API or database connection. Community Cloud
   should discover `dataops-sentinel/requirements.txt` beside the entry point.
   That file pins `pandas==2.3.3` and `streamlit==1.51.0`; the adjacent
   `pyproject.toml` contains test/lint configuration. Do not select
   `requirements-dev.txt` as the runtime dependency file.
4. Review the upload/configuration caveat below before publishing. If the host
   offers supported configuration overrides, set `server.maxUploadSize=2` and
   `browser.gatherUsageStats=false`, then verify the effective settings. The
   nested configuration alone is not evidence that Cloud applied those values.
5. Deploy the app and inspect the build/runtime logs. Confirm Python 3.12 and the
   pinned runtime dependencies, then run every smoke check below using fictional,
   non-sensitive data. Record the deployed URL, merged commit, date, effective
   configuration, and results. A successful local test does not replace this
   Cloud check.

## Upload and working-directory configuration

Community Cloud documentation describes the repository root as its working
directory. The pinned Streamlit 1.51.0 launcher adds the entry point's directory
to Python's import path, so sibling `sentinel` imports work. The app derives
`ROOT = Path(__file__).resolve().parent` and reads both bundled fixture files from
that location; these reads do not depend on the process working directory.

There is no repository-root `.streamlit/config.toml`. The project's nested
`dataops-sentinel/.streamlit/config.toml` sets a 2 MiB upload transport limit and
disables usage telemetry. Fresh local processes demonstrated:

| Working directory | `server.maxUploadSize` | `browser.gatherUsageStats` |
| --- | --- | --- |
| Repository root | `200` MB, framework default | `true`, framework default |
| `dataops-sentinel/` | `2` MB, nested configuration loaded | `false` |

Thus the nested file was ignored by the tested root-directory launch. The
versioned Streamlit 1.51.0 uploader documentation gives a **200 MB default** unless
configuration overrides it. Plan for that default transport limit on Cloud
unless the host demonstrably applies another value; Cloud's effective value has
not been checked. Current Cloud documentation also describes app-specific nested
configuration for repositories with multiple apps. Host behavior may therefore
differ from this pinned local launch: inspect the deployed behavior instead of
assuming either configuration path was applied. This checkpoint adds no root
configuration and provisions no host override.

The application parser independently rejects inputs over **2,097,152 bytes
(2 MiB)** or **10,000 records**. The uploader reads at most one byte beyond the
parser byte bound for validation, but that occurs after Streamlit's upload
transport. Parser rejection does not lower the framework's network/body limit.
Confirm the intended transport limit separately if the owner requires it.

## Local checks performed

Checks used `/workspace/work/dataops-venv/bin/python` without installing or
changing dependencies. The environment reported Python **3.12.14**,
Streamlit **1.51.0**, and pandas **2.3.3**.

| Check | Observed result |
| --- | --- |
| Entry point syntax and required files | Passed; entry point, sibling package, runtime requirements, CSV and truth manifest present |
| Dependency discovery layout | Runtime requirements are beside the entry point; no competing root dependency file among `requirements.txt`, `uv.lock`, `Pipfile`, `environment.yml`, and `pyproject.toml` |
| Installed runtime versions | Both match the exact `requirements.txt` pins |
| Root-directory app initialization | No AppTest exception with the installed Streamlit launcher's app-directory import initialization |
| Load synthetic demo | Input 50, accepted 41, rejected 9, advisory 1; three download widgets present |
| Fixture truth evaluation | Hard errors TP=9, FP=0, FN=0, TN=41; advisories TP=1, FP=0, FN=0, TN=49 |
| Exact demo replay | Same run ID, `reused=true`; database remains one source, one run, 41 accepted rows, 9 rejected rows, 10 findings |
| New AppTest session | Different temporary database; no result inherited from the first session |
| Clear session audit | Result removed and previous temporary database deleted |
| Configuration lookup | Fresh root/app-directory processes produced the values in the configuration table above |

The root-directory AppTest check used `streamlit.web.bootstrap._fix_sys_path`
from the installed launcher before executing the actual app. Plain AppTest does
not perform that launcher initialization. These checks establish local import,
path, dependency-version, and app behavior; they do not test a Cloud build,
Cloud filesystem, remote HTTP transport, or a published browser session.

## Owner's post-deployment smoke checks

1. Open the deployed HTTPS URL in a clean browser session. Confirm the initial
   screen loads without a Python exception, missing module, missing fixture, or
   database-open error. Inspect logs for the expected Python/dependency versions.
2. Click **Load synthetic demo**. Confirm **50 input = 41 accepted + 9 rejected**,
   with **1 advisory** that remains in the accepted cohort. Confirm the synthetic
   truth evaluation has the confusion counts listed above and the source is
   `synthetic_operations.csv`.
3. Record the audit run ID, then load the same demo again. Confirm the replay
   message and unchanged run ID; the audit trail must still show one run.
4. Download all three outputs: **Quality report (JSON)**, **Accepted records
   (CSV)**, and **Findings (CSV)**. Confirm the JSON counts and matching provenance,
   41 CSV data rows in the accepted export, and 10 finding rows in the findings
   export. Inspect only fictional records.
5. Upload a small fictional CSV with a missing required column and click
   **Validate uploaded CSV**. Confirm actionable feedback, no new audit run, and
   no stale successful result/download controls. Load the demo again and confirm
   successful replay restores its result.
6. Check limits with synthetic inputs: a file of 2 MiB + 1 byte and a correctly
   shaped CSV containing 10,001 records. Confirm rejection without an audit run.
   The byte-limit rejection may occur at the upload widget if the host's 2 MiB
   transport setting is active, or at parser validation if the host permits the
   larger upload. Record which behavior occurred and the effective host limit.
7. Open a separate browser session and confirm its audit starts empty. In the
   first session, click **Clear session audit**: confirm displayed results clear,
   the uploader resets, and reloading the demo creates a fresh run. This checks
   audit isolation; it does not establish download-link confidentiality.
8. Check a narrow/mobile viewport and a normal desktop viewport for usable input,
   summary, findings, audit, and download controls. Record any browser-specific
   failures before treating hosting as verified.

## Hosting limits and permitted data

Use **fictional, non-sensitive inputs only**. Each app session owns a temporary
local SQLite directory. Session cleanup, a server restart, or the host replacing
the instance can erase it. The app provides no durable shared database, account
authentication, total-session storage quota, or retention service. Download
outputs before leaving if they are needed.

SQLite session isolation is separate from Streamlit media delivery. A person
who knows an active download/media URL can retrieve its contents from another
browser session. Such a URL acts as a bearer link, and framework cleanup may
leave it usable after a failed submission or session change. Clearing the UI or
session audit is not a guaranteed immediate link-revocation mechanism. An
unguessable-looking URL is not an authorization boundary. Sensitive-data hosting
would require a separately designed and verified access/download/retention model.

## Official references checked

Checked during Checkpoint 3; documentation checks did not access a Cloud account or deploy
an app.

- [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy):
  repository, branch, entry-point fields and Advanced settings Python selector;
  explicitly choose 3.12 rather than relying on the documented current default.
- [App dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies):
  search the entry-point directory before the repository root; `requirements.txt`
  takes precedence over `pyproject.toml`.
- [File organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization):
  root working directory and configuration placement, plus the current
  app-specific nested-configuration guidance noted above.
- [Streamlit 1.51.0 file uploader](https://docs.streamlit.io/1.51.0/develop/api-reference/widgets/st.file_uploader):
  200 MB default upload transport limit and `server.maxUploadSize` setting.
- [Configuration reference](https://docs.streamlit.io/develop/api-reference/configuration/config.toml):
  working-directory configuration and environment/command-line override rules.

**Pending:** owner merge authorization, owner publishing authorization, the actual
Cloud build/deployment, effective hosted configuration, and all hosted smoke
results. No public URL or live-Cloud verification is claimed by this document.

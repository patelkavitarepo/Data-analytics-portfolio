# Temporary DataOps Sentinel preview from an iPad

This guide is for the owner-authorized **temporary, public, synthetic-only
preview**. Deploy the feature branch below. This checkpoint does not authorize
merging the pull request, changing `main`, creating a release, or permanent
publishing. These instructions do not establish that a preview was deployed or
that any hosted test passed.

All steps use Safari and website controls. No terminal, local Python installation,
paid service, database service, secret, or new infrastructure is needed.

## 1. Check the source in Safari

1. Open the [feature branch on GitHub](https://github.com/patelkavitarepo/Data-analytics-portfolio/tree/feat/dataops-sentinel-issue-15).
   Confirm the branch selector reads `feat/dataops-sentinel-issue-15`.
2. Open the latest commit. The prepared revision is
   **`fd15c5b867920a0ac76e37de10e56bfb36843533`** (`fd15c5b`). A later revision is
   acceptable for this guide only when it contains documentation/evidence changes
   and preserves the reviewed application code. Use GitHub's commit/compare views
   to check the changed-file list; the entry point, `sentinel/`, runtime
   requirements, fixture data, and Streamlit configuration must be unchanged.
3. Record the full branch-head revision in the results table below. A branch is
   mutable: later pushes can automatically update its Cloud app. Recheck the
   revision after a rebuild rather than treating the branch name as a fixed SHA.

## 2. Create the preview in your own account

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) in Safari. Sign
   in to **your own account** and connect the GitHub account that can access this
   repository. Complete any login or two-factor prompt yourself; do not share
   passwords, login codes, tokens, or credentials in chat. If controls are clipped,
   use Safari's page menu to request the desktop website or rotate the iPad.
2. In the correct workspace, tap **Create app**, then **Yup, I have an app** to
   use the existing repository. Enter these values exactly; type them manually
   if a suggestion is missing:

   | Field | Value |
   | --- | --- |
   | Repository | `patelkavitarepo/Data-analytics-portfolio` |
   | Branch | `feat/dataops-sentinel-issue-15` |
   | Main file path | `dataops-sentinel/streamlit_app.py` |
   | Optional app URL | Choose an available name clearly identifying this as a preview |

3. Tap **Advanced settings**, select **Python 3.12**, leave **Secrets** empty,
   and tap **Save**. Keep a screenshot of the source fields and Python selection
   before deploying. Do not substitute `main` or edit repository files.
4. Tap **Deploy**. If login, repository access, or a payment prompt prevents the
   free preview, stop there and record the blocker. No credentials or paid
   resources should be added to work around it.

Community Cloud searches the entry-point directory for dependencies before the
repository root. The adjacent `dataops-sentinel/requirements.txt` already pins
`pandas==2.3.3` and `streamlit==1.51.0`; no install commands are needed on the iPad.
The deployment flow and Python selector are described in the official
[deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
and the file lookup is documented under
[app dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## 3. Verify the preview and its revision

1. Open the resulting app URL. As the signed-in owner, tap **Manage app** at the
   lower right to inspect the build/runtime logs. Check the repository, feature
   branch, and entry point against the saved source fields. Look for Python
   **3.12.x** and the pinned dependency versions; record anything not shown as
   unverified. The log panel's overflow menu can download the log if needed.
2. If a full deployed commit is displayed in the logs, record it and compare it
   with the reviewed branch-head revision. Official Cloud documentation does not
   promise a deployed-SHA inspector. If no commit evidence is visible, record
   **exact running revision unconfirmed**, together with the selected branch and
   GitHub head; do not claim SHA verification from the app's audit run ID.
3. From the workspace, open this app's **⋮ → Settings → Sharing**. Under **Who
   can view this app**, confirm **This app is public and searchable**. A public
   repository normally produces a public app. Use only fictional, non-sensitive
   inputs: this preview is publicly reachable and may be indexed.
4. Copy the actual preview URL into the results table. No example URL in this
   guide is a claim that an app exists.

These controls are described in the official
[app management](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app),
[app settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings),
and [sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)
documentation. Do not use repository-editing or Codespaces actions for this
preview-only task.

## 4. Run the iPad smoke checks

1. In a fresh session, tap **Load synthetic demo**. Confirm **50 input = 41
   accepted + 9 rejected**, with **1 advisory** that remains accepted. Confirm the
   source is `synthetic_operations.csv` and inspect the synthetic truth results.
2. In **Audit trail**, note the run ID. Load the demo again: confirm the replay
   message, the same run ID, and one audit run. A replay must not add rows.
3. Download **Quality report (JSON)**, **Accepted records (CSV)**, and **Findings
   (CSV)**. Use Safari's download list, or **Share → Save to Files** if a preview
   opens. Check the JSON counts and provenance; the accepted CSV has 41 data
   rows, and the findings CSV has 10 finding rows. Downloading all three is a
   smoke check, not permission to upload personal files.
4. For error feedback, save the branch's bundled
   [owner_malformed.csv](https://github.com/patelkavitarepo/Data-analytics-portfolio/blob/feat/dataops-sentinel-issue-15/dataops-sentinel/docs/owner_malformed.csv)
   using GitHub's file download control, then choose it through the app's CSV
   uploader and tap **Validate uploaded CSV**. Confirm an actionable schema
   error, no new audit run, and no stale successful result/download controls.
   Load the demo again to restore its saved result.
5. Tap **Clear session audit**. Confirm the result and selected upload clear.
   Loading the demo again should create a fresh audit run. Check portrait and
   landscape layouts for readable controls and usable downloads.

Record actual outcomes below. The full no-terminal checklist, including all nine
rejections, the advisory, a second browser session and desktop/iPad layouts, is in
[BROWSER_ACCEPTANCE.md](BROWSER_ACCEPTANCE.md); local results are described in
[DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md).

## Upload and storage limits to check

The parser independently enforces **2 MiB (2,097,152 bytes)** and **10,000
records**. Streamlit 1.51.0's upload **transport defaults to 200 MB** unless an
effective configuration overrides it. The nested
`dataops-sentinel/.streamlit/config.toml` requests 2 MB and disables telemetry,
but a tested local repository-root launch ignored that nested file. Current
Cloud guidance also describes app-specific nested configuration, so its actual
effect on this host remains pending verification. Do not assume the app's
2 MiB caption proves the transport limit. Record the limit shown by the upload
widget, if present, separately from parser validation; do not change root
configuration or add infrastructure for this preview.

See the versioned [1.51.0 uploader reference](https://docs.streamlit.io/1.51.0/develop/api-reference/widgets/st.file_uploader)
and the [Cloud file-organization guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).
The earlier local configuration checks are recorded in
[DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md).

Audits live in a temporary SQLite directory for each session and can disappear
on cleanup, restart, or host replacement. They are not durable hosting or
authentication. Active download/media URLs behave as bearer links: someone who
knows a URL may retrieve it from another session, and clearing the UI is not
guaranteed immediate link revocation. Keep every input and output fictional and
non-sensitive.

## Owner-filled preview record

| Item | Owner's actual observation |
| --- | --- |
| Deployment attempted / date | _Not recorded_ |
| Actual preview URL | _Not deployed or not recorded_ |
| Selected repository / branch / entry point | _Not recorded_ |
| GitHub branch-head full revision | _Not recorded_ |
| Deployed revision evidence, or unconfirmed | _Not verified_ |
| Python / dependency log evidence | _Not verified_ |
| Public visibility | _Not verified_ |
| Effective transport limit / telemetry | _Not verified_ |
| Demo / replay / three downloads / invalid input / clear | _Not tested on Cloud_ |
| iPad portrait / landscape | _Not tested on Cloud_ |
| Blockers or deviations | _Not recorded_ |
| Preview deleted / date | _Not recorded_ |

## Delete only this preview when finished

Deletion is a destructive owner action. Confirm that the selected app's URL is
the preview URL recorded above and that its source is this feature branch. Keep
any fictional outputs needed for review first. The owner should personally
decide to proceed and enter the confirmation; cancel if the app identity differs.

1. Sign in to the same owner workspace at
   [share.streamlit.io](https://share.streamlit.io/).
2. Find **this preview app**, tap its **⋮** menu, then **Delete**.
3. Read the confirmation dialog. Type exactly the confirmation string it requests,
   verify the app identity again, and tap **Delete** only if you intend to remove
   this preview. The documentation does not guarantee that the requested string
   is always the URL.
4. Check that the preview no longer appears in your workspace and record the
   deletion outcome. Deleting the preview does not erase copies already
   downloaded by viewers.

This procedure removes the **Streamlit preview app only**. Leave the GitHub
repository, feature branch, pull request, and other deployed apps intact. The
current UI flow is documented under
[Delete your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/delete-your-app).

Official public documentation was checked read-only for this guide. No Cloud
account action, deployment, hosted test, or deletion is claimed by the guide.

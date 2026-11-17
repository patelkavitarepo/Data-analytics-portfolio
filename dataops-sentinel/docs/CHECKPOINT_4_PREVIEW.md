# Project 009 — Checkpoint 4 preview status

**PREVIEW BLOCKED — ACTION REQUIRED.** The application candidate and CI are ready
for a synthetic-only feature-branch preview, but this environment cannot reach
the Streamlit Community Cloud account page. **No preview was created or verified,
no public app URL was obtained, and no hosted smoke test was executed.** Owner
acceptance remains pending.

The owner authorized a temporary preview, including a possible public URL, from
the existing feature branch. That authorization does not include a merge, a
production release, or an unrestricted real-data service. No application changes,
credentials, app secrets, paid services, database services or new infrastructure
were introduced by this checkpoint.

## Exact configuration to use

| Field | Prepared value / observed status |
| --- | --- |
| Repository | `patelkavitarepo/Data-analytics-portfolio` |
| Branch | **`feat/dataops-sentinel-issue-15`**, not `main` |
| Main file | `dataops-sentinel/streamlit_app.py` |
| Python selection | **3.12** |
| Runtime dependencies | Adjacent `dataops-sentinel/requirements.txt` |
| Locally checked candidate | `fd15c5b867920a0ac76e37de10e56bfb36843533` |
| Application baseline | `a7b801f36a3078aaabcdf7c1057245f453bc5687`; application files unchanged |
| Actual deployed commit | **Not available — no deployment** |
| Actual hosted Python version | **Not observed**; local verification used 3.12.14 |
| Public HTTPS preview URL | **Not available — none created or verified by this task** |

This checkpoint adds only README/documentation/evidence. When deploying the branch,
record its then-current full head revision, which may be this documentation-only
successor of `fd15c5b`. Branches can auto-update their Cloud apps on later pushes.
Record running-revision evidence if Cloud exposes it; otherwise distinguish the
selected branch/head from an unconfirmed exact running SHA. An audit run ID is
not a Git commit identifier.

## Deployment access: observed blocker

The attached cloud browser attempted `https://share.streamlit.io/` and showed
**“This site can't be reached” / `ERR_TUNNEL_CONNECTION_FAILED`**. The browser
navigation helper also reported `Browser Use could not read requirements`; native
browser navigation reproduced the tunnel failure rather than reaching the account
page. This is not evidence that the Streamlit site is down or that the owner is
signed out. Authentication state and repository deployment permission could not
be inspected.

A separate read-only HTTP-client check using the supplied network settings failed:

```text
curl -sS -L --max-time 20 -o /workspace/work/checkpoint4/streamlit-access-response.txt -w '%{http_code}\n' https://share.streamlit.io/
# exit 56; HTTP status 000
CONNECT tunnel failed, response 403
```

The **403 was a proxy CONNECT refusal**, not a verified application HTTP response,
account rejection, or bot challenge. No login details were requested, no deployment
form was submitted and no network/security workaround was attempted. The available
tools provide no dedicated authenticated Streamlit deployment connector.
[Access evidence](checkpoint4_access_check.json) separates these observations from
unknown hosted state.

**Owner action:** follow [PREVIEW_IPAD.md](PREVIEW_IPAD.md) in your own iPad Safari
session. Sign in yourself, deploy the exact feature-branch settings above, and
record the actual HTTPS URL, source/revision evidence, Python version and effective
configuration. No terminal or local Python installation is required. Do not send
passwords, login codes or tokens in chat. The account website may work on your
iPad even though this environment's proxy could not reach it.

## Candidate checks actually executed

GitHub PR metadata, local Git and `git ls-remote` agreed on the feature head
`fd15c5b867920a0ac76e37de10e56bfb36843533`. PR #16 was open, **draft** and unmerged;
`main` remained `ccdfb87a3d09730b0caa49c61b510ef8c7db6b06` when checked.

The [DataOps Sentinel CI run #3](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/44008406926)
was inspected: both **Python 3.11 and 3.12** jobs successfully completed dependency
installation, source checks, pytest/AppTest and Streamlit imports. The existing
214-case suite was not rerun locally at this checkpoint; its previous actual local
result remains [214 passed in 24.83 seconds](checkpoint3_pytest_output.txt).
CI for this checkpoint's later documentation commit is reported separately in PR
#16, rather than inferred from the prior run.

Fresh **local** checks used the isolated Python 3.12.14 environment:

- Required entry point, sibling `sentinel` modules, dependency files, CSV and
  separate truth manifest were present. Imports succeeded; installed pandas
  2.3.3 and Streamlit 1.51.0 match their pins. Fixture paths derive from the app
  file directory, not from the working directory.
- The fixed-seed generator reproduced both committed artifacts exactly. CSV
  SHA-256: `2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21`.
- Two successful CLI runs against a fresh scratch database produced
  **50 input = 41 accepted + 9 rejected**, with **1 accepted advisory**. The second
  returned the same run ID `fd962d986617463dba70036782b20dd7` and `reused=true`.
- SQL counts before/after replay were unchanged: one source/run, 41 accepted rows,
  nine rejected rows and ten findings. Integrity check returned `ok`; no
  foreign-key violations. The accepted export had 41 rows including `SYN-0050`.
- The application, tests, dependencies, fixtures, Streamlit configuration and
  workflow were unchanged from the reviewed application; changes remain confined
  to this project's documentation and README.

[Local evidence](checkpoint4_local_verification.json) records commands, versions,
outputs and the explicit local-only scope. The existing synthetic notices, input
warning, temporary-audit explanation and bearer-download notice remain in the UI.
These checks do **not** establish a deployed build or hosted browser behavior.

## Upload limits: local observation versus unknown hosted configuration

Fresh configuration processes returned:

| Process working directory | Upload transport setting | Usage telemetry |
| --- | ---: | --- |
| Repository root | 200 MB, framework default | `true` |
| `dataops-sentinel/` | 2 MB, nested configuration loaded | `false` |
| Actual Community Cloud preview | **Not observed** | **Not observed** |

The parser always enforces **2,097,152 bytes / 10,000 records / 131,072 decoded
characters per field**. Parser rejection happens after Streamlit's upload
transport and does not prove that transport's cap. The app's “Maximum 2 MiB”
caption is not evidence of the hosted transport setting.

Current Cloud documentation describes app-specific configuration, while the pinned
local root launch ignored the nested file. On the deployed preview, record the
upload widget's displayed cap and any supported effective-config evidence, plus
the Python/dependency logs. If it differs, document that difference; do not silently
claim 2 MiB transport, disable safeguards, modify root configuration or add new
infrastructure. [The iPad guide](PREVIEW_IPAD.md) explains the remaining checks.

## Hosted smoke-test record — none executed

All results below remain **NOT EXECUTED** because no hosted URL was available.
Previous localhost tests, local AppTest and CLI results are not substituted.

| Requested HTTPS smoke check | Hosted result |
| --- | --- |
| 1. Page loads without imports/dependency/database errors | NOT EXECUTED |
| 2. Synthetic demo loads | NOT EXECUTED |
| 3. 50 input = 41 accepted + 9 rejected; 1 accepted advisory | NOT EXECUTED |
| 4. Duplicate pair rejected; `SYN-0050` remains accepted | NOT EXECUTED |
| 5. Exact replay retains its run without double-counting | NOT EXECUTED |
| 6. Fictional malformed CSV gives feedback without stale results | NOT EXECUTED |
| 7. JSON and accepted CSV downloaded and counts verified | NOT EXECUTED |
| 8. Reset clears displayed state | NOT EXECUTED |
| 9. Second browser session begins without inherited data | NOT EXECUTED |
| 10. Desktop and mobile/iPad layouts usable | NOT EXECUTED |

After deployment, personally repeat [BROWSER_ACCEPTANCE.md](BROWSER_ACCEPTANCE.md).
It needs only Safari/browser controls and Files, explains every rejected row and
the accepted advisory, and leaves ten observation rows and owner acceptance blank.
Record failed or unavailable checks rather than guessing. If further automated
hosted testing is requested, supply the actual public HTTPS URL and non-sensitive
deployment details; do not supply credentials.

## Public-preview boundaries and removal

Only bundled or other deliberately fictional, non-sensitive inputs are permitted.
Do not upload customer information. Each session's SQLite is temporary, local and
single-instance: cleanup/restarts can erase it. No persistence, production readiness,
authentication, aggregate quota or real-world detection accuracy is claimed.

Known active Streamlit media URLs can be read by anyone who possesses the link,
including from another browser session. Cleanup and reset do not guarantee
immediate revocation. Session/database separation is not media authentication.
Public app visibility can also make the preview discoverable/searchable.

When review is finished, use the [preview-only deletion steps](PREVIEW_IPAD.md#delete-only-this-preview-when-finished):
sign in to the correct workspace, verify the preview URL and feature-branch source,
choose that app's **⋮ → Delete**, and personally complete the exact confirmation
requested by the dialog only if you intend to remove it. Leave the repository,
branch, draft PR, other apps and `main` intact. Deletion does not erase copies
already downloaded by visitors. No deletion was performed here.

The next action is owner account access/deployment through the iPad guide, followed
by actual hosted tests. Human acceptance remains separate and unrecorded. PR #16
stays draft; no merge, production release, deployment or publication was performed
by this checkpoint.

# Deploy Project 006 — Synthetic Research Showcase

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

This deployment publishes only the static-evidence Streamlit exhibit from the synthetic-only package, **not** the unfinished Project 006 empirical application.

## Exact Streamlit Community Cloud settings

| Setting | Value |
| --- | --- |
| Source provider | GitHub |
| Repository | `patelkavitarepo/Data-analytics-portfolio` |
| Branch | `main` |
| Main file path / Entrypoint | `markowitz-synthetic-showcase/synthetic_showcase.py` |
| Python version | `3.12` |
| Dependencies | `markowitz-synthetic-showcase/requirements.txt` |
| Secrets | None required |
| Custom app URL | Optional — choose a unique available name, e.g. `project-006-synthetic-research` |

### Deploy

1. Open [Streamlit Community Cloud](https://share.streamlit.io) and sign in with GitHub. Authorize the public repository if prompted. The owner needs appropriate GitHub repository access.
2. Choose **Create app** → **Yup, I have an app**.
3. Enter the repository, `main` branch and exact entrypoint path above. If search does not list a path, paste it manually or choose the option to paste a GitHub file URL.
4. In **Advanced settings**, select **Python 3.12** and leave Secrets empty; then save.
5. Optionally set a custom app subdomain. Choose **Deploy**.
6. Once deployed, open the public `https://<your-app-name>.streamlit.app` URL and inspect **Start here** plus each of the five studies. Check mobile navigation, download buttons, explicit synthetic labels and negative findings.

The app runs from local, checked-in JSON evidence; it neither fits a model at page load nor contacts ETF/market data providers. It uses public repository source files. Clicking documentation links opens GitHub. The first install on Streamlit Cloud requires ordinary dependency downloads.

### Pre-share verification

- The top banner says **SYNTHETIC DATA — NOT EMPIRICAL RESULTS**.
- Five investigation panels open, and original report downloads work.
- The eight-ETF performance question remains **unanswered**.
- Known true covariance and the oracle are explicitly synthetic-only, with the theoretical oracle **non-investable**.
- No market-data provider access, historical ETF performance chart, user-uploaded price file or interactive optimizer is exposed.

If installation or loading fails, consult Streamlit Cloud's app logs and verify the branch, file path, Python version and pinned requirements. Do **not** bypass the source policy or run the empirical app as a workaround.

**Official documentation:** https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

### Source and research boundary

[GitHub synthetic-only source](https://github.com/patelkavitarepo/Data-analytics-portfolio/tree/main/markowitz-synthetic-showcase) · [Draft empirical PR #6](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6)

Deployment does not authorize any ETF evaluation, vendor permissions or use of the protected 2025+ holdout.

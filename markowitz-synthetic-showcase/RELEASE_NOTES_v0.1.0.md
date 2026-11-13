# Project 006 — Synthetic Portfolio Research v0.1.0

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

The first standalone release of Project 006 is a reproducible, educational investigation of constrained Markowitz portfolio optimization. It publishes a read-only Streamlit showcase and five completed synthetic studies, each preserving positive, mixed and negative results.

## Included
- Offline standalone Streamlit research exhibit (`markowitz-synthetic-showcase/synthetic_showcase.py`)
- Five unchanged, SHA-256-pinned synthetic JSON evidence reports with original-byte downloads
- Research findings, counterexamples and design/limitations for each investigation
- Case study, Decision Quality Framework, data-rights gate and reproducibility checks
- Isolated automated tests and source/evidence audit

## Research insights
- Historical correlations can change unexpectedly, disrupting estimated risk.
- Longer training windows can stabilize some allocations without guaranteeing future protection.
- Serial dependence complicates IID versus block-bootstrap interpretation.
- Fixed diagonal covariance shrinkage can worsen risk estimation even when conditioning improves.
- Better covariance matrix accuracy does not necessarily improve constrained portfolio decisions.

## Important limitations
**No real-world ETF performance, alpha, or investment superiority has been established.** All displayed results are from deliberately constructed synthetic assets, not live investment experience. A theoretical known-covariance oracle appears only as a **non-investable synthetic diagnostic**.

The separate eight-ETF empirical research remains in [draft PR #6](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6). Its 2025+ holdout is untouched, and required data rights and independent adjustment checks are unresolved. No market-data provider, live trading software or ETF prices are included in this release.

**This is educational research, not investment advice.**

## Explore
- [Project 006 README](https://github.com/patelkavitarepo/Data-analytics-portfolio/tree/main/markowitz-synthetic-showcase)
- [Streamlit Community Cloud deployment guide](https://github.com/patelkavitarepo/Data-analytics-portfolio/blob/main/markowitz-synthetic-showcase/DEPLOYMENT.md)

A public Streamlit app requires a separate Streamlit Community Cloud deployment from the `main` branch; the GitHub release does not deploy a website.

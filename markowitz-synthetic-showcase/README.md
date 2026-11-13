# Project 006 — Synthetic Portfolio Research Showcase (release candidate)

**SYNTHETIC DATA — NOT EMPIRICAL RESULTS**

This is an **offline, read-only release candidate** for the educational Markowitz portfolio research showcase. It combines five previously completed, deterministic synthetic investigations. **No historical ETF performance has been demonstrated**, and no strategy, estimator or investment allocation is recommended.

**Status: for owner review only. Not merged, deployed, tagged, or released.**

## The research question

Can constrained portfolio optimization improve out-of-sample risk-adjusted performance versus equally weighted investments? **Unanswered for real ETFs.** The separate eight-ETF research prototype remains a draft in [PR #6](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6) with the 2025+ holdout untouched and provider-data permission/independent adjusted-price verification outstanding.

This package is deliberately restricted to a standalone Streamlit presentation, a standard-library evidence reader, five unchanged labeled synthetic JSON reports, research documentation, and isolated offline tests. It contains **no provider downloader, ETF prices, empirical optimization runner, vendor credentials or live trading system**.

## Run the showcase locally

Requires Python 3.12.

```bash
cd markowitz-synthetic-showcase
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run synthetic_showcase.py --browser.gatherUsageStats false
```

The app loads local committed files and does not require market-data services. Installing Python dependencies may require internet access once; the research showcase itself uses local evidence only. On Windows, substitute `.venv\\Scripts\\` for `.venv/bin/`.

## Verify evidence, offline

```bash
cd markowitz-synthetic-showcase
.venv/bin/python -m pytest -q tests/test_showcase.py
.venv/bin/python scripts/check_showcase.py
```

The read-only audit checks evidence file hashes, labels, link targets, supported imports and the five presentations. Tests do not prove financial performance, legal authorization or that all possible security risks are absent.

## Investigations

| Study | Main insight | Evidence |
| --- | --- | --- |
| Scenario lab | Estimated-return errors and correlations affect portfolio decisions | [Original findings](SYNTHETIC_LAB.md) |
| Unseen correlation jump | Stable allocations can face higher future modeled risk | [Robustness findings](SYNTHETIC_ROBUSTNESS_FINDINGS.md) |
| Serial dependence | IID and block resampling can disagree in either direction | [Serial findings](SYNTHETIC_SERIAL_FINDINGS.md) |
| Fixed diagonal shrinkage | Better conditioning or lower concentration need not lower risk | [Shrinkage findings](SYNTHETIC_SHRINKAGE_FINDINGS.md) |
| Shrinkage mechanism | Covariance accuracy and constrained decision regret are distinct | [Mechanism findings](SYNTHETIC_SHRINKAGE_MECHANISM_FINDINGS.md) |

Start with the [case study](CASE_STUDY.md) and [Decision Quality Framework](DECISION_QUALITY_FRAMEWORK.md). Review [data rights](DATA_RIGHTS.md) and [adjustment verification](ADJUSTMENT_REVIEW.md) for the **blocked** empirical research. Other linked source modules and execution instructions in the retained technical research records may refer to the full [PR #6](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6), rather than runnable modules in this intentionally narrow showcase package.

## Provenance and limitations

Source of the reviewed showcase and JSON evidence: Project 006 branch at commit `d37127250826d410e24b41bbf6289d3f1401aa58`. The five JSON files and the showcase Python files are copied by their original Git blob hashes, not regenerated or recalculated. Panel downloads are byte-for-byte source reports. The educational scenarios use constructed Gaussian assets, limited fixed random seeds and simplified assumptions; known covariance and the theoretical oracle are **synthetic privileges**, not observable market truths.

Do not present synthetic Sharpe, drawdown, volatility or optimization regret as historical or investable results. **No provider permission has been established for historical ETF validation.** Approval of this release candidate does not authorize a merge, GitHub release, public Streamlit deployment, evaluation of the real holdout, or use of a restricted data provider.

This branch is an independently reviewable release **candidate**. The owner decides whether to publish the synthetic-only results after manual review.

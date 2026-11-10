# Project 002 — Version 1.0 release notes

**Release:** v1.0.0 · November 10, 2026

## What is included

- Daily Stock Volatility Prediction and Model Failure Analysis, a **human-led research / AI-assisted implementation** project.
- Three tested forecasts of unannualized five-session close-to-close volatility: M0 historical-volatility baseline; M1 stock-specific Ridge; M2 stock-specific Ridge with broad-market inputs.
- Reproducible chronological 2014 tuning and quarterly 2015 internal evaluation, with leakage and data-quality checks.
- An interactive Streamlit dashboard at `optiver-realized-volatility/forecast_app.py` with predicted-vs-actual charts, comparisons, failure cases, coverage and exports.
- Both narrow and conservative data-quality masks, research evidence and lead decisions, including the frozen D001–D006 foundation.

## Headline findings (conservative masking, same 111,428 stock-date observations)

| Model | RMSPE (lower is better) | MAE (volatility percentage points) | RMSE (volatility percentage points) |
| --- | ---: | ---: | ---: |
| M0 historical-volatility baseline | 0.8774 | 1.3722 | 2.0146 |
| M1 stock-specific Ridge | 0.5688 | 1.1973 | 1.8995 |
| M2 stock + market Ridge | 0.5765 | 1.1865 | 1.8714 |

The learned models improve overall internal RMSPE relative to M0 but both perform worse in the highest realized-volatility band. M2 lowers aggregate MAE/RMSE relative to M1 but raises RMSPE; descriptive differences are uncertain. Retained failure cases and metric disagreements are in [D008 results](research/forecast-D008/RESULTS.md).

## Evidence boundaries and limitations

- **These are internal 2015 historical results, not independent future-market proof, a trading system, or profitability claims.**
- 2016–2018 remains **reserved**; there was no approved final independent evaluation.
- Data is daily Plotly stock OHLCV (2013–2018), **not** the Kaggle Optiver high-frequency competition dataset. Data quality/corporate-action adjustments, survivorship bias, and retrospective cleaning remain limitations.
- No context-aware multiple-reference-stock model, CVR ranking, adaptive baseline switching, or claim that extreme failures' causes were established.
- Implementation assisted by AI; human research questions, choices and interpretations are separately documented. No AI code is represented as manually written by the lead.

## Verification and deployment

At the version 1.0 release candidate: 64 local tests passed; Python 3.11/3.12 CI green; desktop and mobile-browser controls checked in Chromium. Physical iPad Safari and public Streamlit hosting have **not** been verified.

To deploy to Streamlit Community Cloud:
- Repository: `patelkavitarepo/Data-analytics-portfolio`
- Branch: `main` (after PR #2 is merged)
- Entry point: `optiver-realized-volatility/forecast_app.py`
- Python: 3.11 or 3.12

A cloud deployment is separate from publishing repository code. Do not claim a live app URL until Streamlit confirms it.

## Future research, not v1.0 promises

Investigate extreme-condition training diversity, out-of-training-distribution detection, uncertainty communication and evidence-backed baseline fallback. The advanced conditional-stock-vulnerability and multiple-reference methodology from D001–D006 is preserved for later study. Further modeling, reserved-period analysis and feature expansion require new research approvals.

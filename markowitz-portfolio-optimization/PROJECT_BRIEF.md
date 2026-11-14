# Project 006 — Markowitz Portfolio Optimization

**Working title:** The Efficient Frontier  
**Project type:** Finance / quantitative data analytics portfolio project  
**Stack:** Python, pandas, NumPy, SciPy, Plotly, pytest, Streamlit, GitHub; use publicly accessible market data only.

## Investigative question

Can a constrained Markowitz minimum-volatility or maximum-Sharpe portfolio deliver better **out-of-sample risk-adjusted performance** than a simple equally weighted portfolio? The answer is unknown until we test it. Do not assume that optimization adds value.

## Scope and research principles

- This is a reproducible educational analysis, not an investment adviser or trading recommendation.
- Use **real historical data** and show provenance; never invent returns, optimization outcomes, or performance numbers.
- Separate observations, modelling assumptions, hypotheses, and the user's eventual interpretation.
- Never use post-period information to estimate earlier portfolio weights, choose a strategy, or tune settings.
- Keep changes contained to `markowitz-portfolio-optimization/`. Leave the existing portfolio projects intact.
- Work on branch `project-006-markowitz-portfolio-optimization`. Open a **draft PR**, do not merge or deploy without approval.

## Candidate assets

Start with eight ETFs: SPY, QQQ, IWM, EFA, EEM, TLT, GLD, VNQ. Explain overlapping US-equity exposure and different inception/availability constraints. Avoid survivorship or selection bias claims we cannot support. Allow a small, user-editable subset only if the estimation and constraint checks remain feasible.

## Data pipeline

1. Implement a repeatable historical daily price downloader (e.g. yfinance with `auto_adjust=True`) from 2016-01-01 through the last **available complete trading day**, rather than pretending today's partial data are final.
2. Document vendor, retrieval timestamp, tickers, price adjustment method, time zone, last observation date, and libraries. Add a data-quality audit: missing dates, ticker coverage, duplicate rows, nonpositive prices, misaligned calendars, and gaps.
3. Do not silently fill long price gaps or drop assets without a conspicuous audit result. Align common valid trading dates before calculating daily simple returns; document the chosen rule and lost rows.
4. Handle rate limits, offline mode, and failed downloads gracefully. Use Streamlit cache with a reasonable TTL. Offer upload of a validated user-supplied historical price CSV as a fallback.
5. **Market-data licensing:** Before committing raw downloaded prices or deploying a bundled copy, check the source terms. Prefer repeatable acquisition code and synthetic fixtures for automated tests; do not redistribute vendor data if not permitted.
6. Risk-free rate: ideally retrieve date-aligned historical 3-month Treasury yield observations from FRED (DGS3MO or an explicitly documented comparable series). Convert annualized yields to appropriately scaled daily rates when calculating Sharpe; use only information available at each time. If unavailable, offer a **clearly labeled user-entered constant assumption**, not an invented historical series.

## Portfolio methodology

- Calculate annualized mean returns and covariance (252 trading days/year) from the training sample; implement sample covariance first, with optional shrinkage as a robustness comparison.
- Long-only, fully invested, no leverage: weights >= 0, sum(weights) = 1. Use a default per-ETF upper bound of 35% and verify feasibility for the selected universe.
- Using SciPy constrained optimization, find the global/minimum-variance candidate (numerical solver with checks), a maximum ex-ante Sharpe candidate (make local-solver nature explicit), and an **efficient frontier** from feasible target-return constraints. Report diagnostics and constraint violations; never plot failed optimization points.
- Include simple equally weighted baseline (same assets) and SPY as an external benchmark.
- Produce a reproducible **time-based split**, initially proposed: training 2016–2022; validation 2023–2024; final untouched holdout 2025 through latest available. Freeze model choices after validation, then fit on training+validation only when evaluating the final holdout. Explain that a single holdout is limited evidence.
- Compare all strategies out of sample using identical return dates and documented rebalancing (e.g. monthly to target weights for diversified portfolios). Include cost-free baseline first and at least one realistic transaction-cost sensitivity; never compare unequal cost assumptions.
- Report annualized return, volatility, Sharpe, cumulative growth, maximum drawdown, concentration, and weights. Display train vs validation vs holdout clearly; avoid interpreting the sample optimizer's Sharpe as a guaranteed future return.
- As a stretch goal, include a rolling or walk-forward backtest with an expanding/rolling training window and lagged rebalancing, plus turnover and cost analysis.

## Streamlit MVP

Create a readable, mobile-friendly multi-section interface:
1. **Case overview:** research question, dataset coverage, and data-source / disclaimer panel.
2. **Evidence audit:** completeness report, asset statistics, correlations and covariance heatmap.
3. **Efficient frontier:** risk/expected return chart with min-vol, max-Sharpe, and equal-weight points; explicit in-sample labelling.
4. **Portfolio comparison:** weights, out-of-sample cumulative wealth, drawdowns, metrics table, and benchmark.
5. **Sensitivity & limitations:** concentration caps, covariance uncertainty, benchmark assumptions, and reasoned interpretation placeholders.
6. Downloadable tabular audits and metrics; do not expose misleading forecasts or recommendations.

Keep the core analytical logic in testable Python modules rather than Streamlit callbacks. Add a concise README with reproducible install/run commands and deployment steps for Streamlit Community Cloud using this repo branch and `markowitz-portfolio-optimization/app.py`.

## Acceptance criteria

- Tests for return computations, missing/duplicate/nonpositive prices, covariance annualization, budget and bound constraints, infeasible cases, objective calculations, date splits, time leakage, benchmark alignment, and metrics.
- Synthetic fixtures only in tests; visually obvious warnings if live data cannot load.
- `pytest` passes; `streamlit run markowitz-portfolio-optimization/app.py` works when dependencies and real data are available. Record what was and was not actually verified.
- Dates and data sources visibly disclosed in the UI and README.
- Provide a transparent research summary, *not* fabricated conclusions. Reserve final human interpretation for the owner after examining real results.
- Work in small reviewable changes, commit to the dedicated branch, open a **draft PR**, and leave `main` untouched.

## Initial Codex mission

Read this file, inspect the existing repository, and implement the smallest credible MVP with **real-data ingestion, validation, static train/validation/holdout optimization, a working Streamlit dashboard, and thorough tests**. If required data are unavailable, report the blocker and keep a clearly labelled fallback. Do not synthesize a claim of real-world performance. Run tests and a UI smoke check if possible; summarize results, caveats, and exactly what the owner should review. Do not merge or deploy.

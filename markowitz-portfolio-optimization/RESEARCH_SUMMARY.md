# Research and verification record · 2026-11-11

## Evidence status

**No real-market performance results are available.** The requested experiment
has been implemented but its empirical question remains unanswered. A direct
Yahoo chart probe, a FRED DGS3MO CSV probe and the actual yfinance acquisition
all failed with proxy CONNECT 403. The owner authorized host access, but the
managed allowlist remained restrictive on retry; this session provides no
configuration mutation tool. No alternative source was substituted and no
synthetic test output is presented as financial evidence.

Eligible last session at verification: **2026-11-10**, using the conservative
rule excluding today's New York date. This is a requested cutoff, **not a claim
that prices through that date were retrieved**. All eight ETFs must pass coverage
checks after network access is restored or a real adjusted-price CSV is provided.
The final holdout has not been inspected with real data in this work.

## Implemented

- Independent adjusted-price acquisition, bounded retry, provenance, versions,
  checksums and session-calendar audit; CSV fallback; no price interpolation.
- Sample mean/covariance, feasible long-only .35 caps, minimum variance,
  deterministic local max-Sharpe candidates and checked efficient frontier.
- Frozen train/validation/holdout windows with estimation preceding evaluation;
  identical benchmark dates, monthly drifting holdings, initial purchase costs,
  cost-free and equal 10 bps sensitivity comparisons.
- CAGR, sample volatility, daily-excess Sharpe, growth, inception-aware drawdown,
  target HHI, maximum target weights, gross traded notionals and diagnostics.
- Streamlit provenance/audit, training statistics/heatmaps/frontier, comparison
  tables/charts, downloadable artifacts and holdout reveal warning. No holdout
  optimization is run while hidden.
- Versioned protocol and pinned direct dependencies plus installed-version lock;
  CLI for auditable local outputs without committing vendor prices.

## Actually verified

- **39 pytest tests passed** on Python 3.12, including synthetic Streamlit
  AppTest checks for full validation and revealed holdout, empty and failed-live
  states, and incomplete-history blocking. All generated prices/returns in tests
  are synthetic fixtures, not evidence about ETFs.
- Analytic minimum-variance solution, budget/bounds, feasibility, target-return
  residuals and failed frontier exclusion; means/covariance and objective math;
  simple returns; duplicate, missing, nonpositive, non-session and stale prices;
  timezone/cutoff behavior; download parameter/provenance behavior.
- Future-return mutation leaves earlier weights and validation performance
  unchanged. Holdout mutation leaves both fitted weight sets unchanged.
  Daily calendar gaps are rejected for evaluation; SPY uses identical dates
  and cost assumptions. Hand-calculated drift, turnover, costs, CAGR, volatility,
  Sharpe and initial drawdown cases pass.
- `streamlit run markowitz-portfolio-optimization/app.py` started; health endpoint
  returned `ok`. Chromium/Playwright reached the empty-data screen and upload
  controls at 1440px desktop and 390px mobile. No JavaScript page errors;
  mobile document width was 390px (no page-level horizontal overflow).
  Screenshots were inspected locally and are not financial evidence.
- Real acquisition was attempted and failed visibly. No full real-data dashboard
  run, vendor adjustment verification or empirical comparison was possible.

Re-run pytest with the README command. With the app already running, optional
browser smoke: `.venv/bin/python tests/browser_smoke.py` from this directory
(uses `/usr/bin/chromium`; Playwright is in the installed-version lock).

## Limitations and owner decisions

1. Restore market-data host access or provide an entitled real adjusted-price
   CSV covering the full interval. Rerun the audit before examining performance.
   Source licensing must be reviewed before redistribution or hosting; no raw
   vendor data is included and no distribution permission is asserted.
2. Historical FRED yield ingestion/publication lags/vintages are deferred. The
   UI uses a disclosed constant **2% effective annual assumption**, editable by
   the owner, consistently converted to a daily rate. Review its sensitivity.
3. Both objectives, sample covariance, .35 cap and monthly resets were fixed
   before real results. There is no validation-based winner selection. Record
   any changes before revealing the final holdout; repeated tuning makes it
   exploratory rather than untouched evidence.
4. One holdout and a retrospective selected ETF universe cannot establish
   general superiority or eliminate selection/survivorship concerns. Overlapping
   equity exposures, noisy means, covariance uncertainty and vendor revisions
   remain material. Shrinkage, rolling tests and statistical inference are
   explicitly deferred.
5. Transactions use a proportional gross-notional cost approximation at prior
   close. No actual execution, taxes or market impact are simulated. Target
   caps can be exceeded by market drift. SPY is intentionally uncapped.
6. After acquiring real evidence, the owner must judge whether any advantage
   persists out of sample and net of equal costs, whether concentration is
   acceptable, and whether differences have practical significance.

No merge or deployment performed.

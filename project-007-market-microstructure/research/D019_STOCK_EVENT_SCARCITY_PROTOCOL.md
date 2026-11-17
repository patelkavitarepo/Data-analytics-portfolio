# D019 — Preregistered stock heterogeneity and event-scarcity study

## Question
Does the positive directional AP-minus-prevalence observed in D016 and conditional complete-day D018 persist across stocks and market periods, or is it driven by stock heterogeneity and zero-positive stock-days?

## What existing evidence does and does not establish
D018's February 10–23, 2023 confirmation is spent. It contains 30 stock-days and ten direction/stock/day slots with undefined AP because positive support was zero despite matched observations. Upward complete three-stock days: 6/10; downward: 4/10. Do not select an alert threshold or refit models on these outcomes. D018 complete-day AP-lift estimates are **not** directly comparable to D016's all-day estimates.

## Predeclared analyses on a *new* confirmation
1. Report the full three-stock × ten-date × two-direction population, with source, feature-ready, matched and positive counts. For each direction, show fraction of zero-positive stock-days and days with at least one zero-positive stock, by stock and overall. Zero-positive days are retained in denominator reports.
2. Report AP and matched base prevalence for every positive-support stock-day, with no imputation for undefined AP. Provide per-stock mean AP-minus-base over its eligible days, eligibility counts, positive-support totals and median lift; show all stocks even if no AP can be calculated.
3. Compare a descriptive **available-stock-day** mean (each defined stock-day equally weighted) with the **complete-three-stock-day** mean. These are different conditional estimands. Report how many days and stock-days each excludes. Do not treat either as a population-wide performance claim.
4. Report a leave-one-stock-out descriptive sensitivity on defined stock-days, showing the remaining stock-day count and lift; do not select a preferred stock from this comparison.
5. Report calibration separately (Brier and event prevalence) for all matched observations, including zero-positive days. If aggregation weights differ, identify them.
6. Keep the balanced and unweighted models paired on identical matched stock-day populations. For paired AP differences, require both defined; disclose joint denominators. No model selection from the results.
7. Uncertainty: descriptive day-cluster resampling with all stocks in each resampled date, 2,000 replicates, seed 7007; if an estimand lacks enough eligible independent date clusters, withhold its interval. Explain the tiny ten-day cluster sample and possible serial dependence. Do not call the interval a significance test.

## Chronology and safeguards
- Choose the **first 40 common observed source dates strictly after the sealed D018 final, 2023-03-09**, using source timestamps only; allocate 20 warmup, 10 confirmation, 10 sealed final.
- Authenticate pinned three-stock source and publish date-list SHA256 and source counts **before** any new prices or target labels are opened.
- Preserve original D012 fit and model specification, and isolate all earlier confirmation and sealed-final periods. No use of D018 confirmation for threshold tuning.
- Synthetic-test no positives, no matched observations, one eligible date, missing stocks, unequal populations, and differences between stock-day and complete-day estimands **before** spending confirmation.
- One-time aggregate-only execution after review of the timestamp manifest and reporting code. Do not redistribute raw source rows.
- No new threshold, trading simulation, profitability claims, or access to any final holdout.

## Decision standard
A positive result must be described as conditional ranking evidence with full denominators. A result dominated by one stock, with large complete-day selection differences or frequent zero-positive days, is fragile evidence. A negative or undefined result must be reported rather than suppressed. The outcome cannot justify a live strategy without separate execution and alert-policy validation.

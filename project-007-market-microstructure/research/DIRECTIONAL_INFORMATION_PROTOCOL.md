# Case 016 — Directional information-content audit: research-first protocol

**Status: prospective design only. No new market-source read, model fit, threshold adjustment, or final test.** Motivated by Case 015's one-time August 10–23, 2022 confirmation, in which directional precision was ~6–10% and every illustrative +1 correct/−4 false utility was negative. These dates are **spent confirmation** and cannot be reused for feature selection or model tuning.

## Core question

Do our existing three five-level order-book snapshot features have directional information at the frozen target horizon, or is poor alert precision principally a consequence of (a) rare directional labels, (b) weak separation from stationary, (c) feature/target timing alignment, (d) temporal/stock variation, or (e) source snapshot defects? The audit must distinguish **base-rate, ranking, calibration and coverage** rather than treating a low alert count as success.

## Phase A: design and invariants — no new prices

1. Lock feature definitions: spread in basis points clipped at 100, best-level volume imbalance, first-five-level volume imbalance. Lock target: average of five next eligible within-session midpoints vs current midpoint at ±0.2%; prohibit using any future midpoint for features or decisions.
2. Lock population: same three original Shenzhen stocks and source timestamp chronology; same two March-trained models as D012; exact source current-and-past validity, same-session continuity and frozen April score calibration. Do not retrospectively exclude bad source dates, substitute stock identities, or relabel unavailable targets as stationary.
3. Lock a **new** untouched common-date cohort, strictly after D015's August 24–September 6 sealed final, using authenticated publisher available_at timestamps **only**; freeze first 40 common observed dates: 20 fit/diagnostic warm-up (no future labels if used only to construct live cutoffs), 10 one-time confirmation, 10 sealed final. Prior D009, D012, D014 and D015 finals stay unscored. The 20-day warm-up may be used to calculate source-only distributions; it is not a new training period.
4. Lock primary analysis on *all* source origins, then on current-feature-eligible origins, then on future-label-verifiable origins. Explicitly reconcile every denominator and every source/stock/day. Avoid extrapolating from available-only records to all market conditions.

## Phase B: frozen diagnostics on new one-time confirmation

- **Label prevalence** (up, stationary, down), including per-stock/day and verifiability; confidence intervals clustered by trading day. Compare majority-class and always-abstain references, not just alerting models.
- **Score separation**: prespecified per-class score quantiles (p10/p50/p90/p98) and precision–recall AUC for up-vs-rest and down-vs-rest, with AP compared against each class's base prevalence. If any class has zero support, report metric undefined, not zero.
- **Ranking rather than threshold rescue**: fixed top 1%, 2%, 5% per stock on confirmation for *descriptive diagnostic only*, explicitly labeled as retrospective and **not** an executable policy or new calibration. These cannot be promoted or used to select a cutoff.
- **Calibration**: reliability bins based on *fixed* probability boundaries 0–0.1, …, 0.9–1, with bin counts, observed target frequencies, and Brier score for each directional class. Never call the ratio score a probability.
- **Timing/source integrity**: count and stratify failed current five-level books, missing past five quotes, missing future five target quotes, and session-boundary effects. Confirm no overlap of current and future indices, strict increasing timestamps, and <=30s within-session quote gaps. Source flags are proxies and cannot independently establish exchange market conditions.
- **Cross-stock and day heterogeneity**: preserve every stock/date and identify concentration of positives, false alerts and missingness without cherry-picking a subset.
- **Uncertainty**: 2,000 day-clustered bootstrap samples, seed 7007; resample common dates jointly across stocks, not quote rows as IID. Ten confirmation dates are too few to claim stable deployable performance.
- **Costs**: no execution or trading return claim. Retain original illustrative +1 correct/−4 incorrect/0 abstain, with zero-alert reference; diagnostics cannot select a new trading strategy.
- **Stop conditions**: fail closed on publisher hash mismatch, different original March training count, any date-list discrepancy, any access to sealed final features/labels, or any source/feature/target misalignment. Keep GitHub PR #7 draft and no model promotion.

## Interpretation gate

This study is about identifying which part of the **information pipeline** is failing, not finding a new model that performs better by repeated testing. Even strong ranking on ten historical days would only justify a new separately preregistered experiment on genuinely later untouched data. Negative or inconclusive findings are legitimate results.

**Implementation next:** add pure label-prevalence/ranking/calibration/denominator diagnostics and synthetic tests first; then freeze a new timestamp-only cohort; only then allow a one-time market-source confirmation. Do not use D015 confirmation to choose bins, thresholds or feature changes. Original D015 sealed final remains sealed indefinitely unless an explicitly separate predeclared final-evaluation gate is authorized.

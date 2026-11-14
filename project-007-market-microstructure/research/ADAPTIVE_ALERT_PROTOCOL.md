# Project 007 — D014 registered prospective adaptive-alert stability study

**Status: FROZEN DESIGN BEFORE ANY D014 NEW-DATE PRICE READ. No D014 outcomes yet.** This is a forward chronological, noncommercial method comparison following D012's failed directional-alert model and D013's source-authenticated score-tail diagnosis. The human lead authorized continuing research; method design, engineering and interpretation are AI-assisted. No trading, brokerage connection, model promotion, or portfolio-performance claim.

## Single scientific question

**Can a strictly PAST-ONLY rolling per-stock score cutoff keep alert frequency closer to 2% than D012's frozen cutoff, and does that produce *trustworthy* directional decisions rather than merely fewer alerts?**

D013 found that, even after aligning label-free eligibility between calibration and confirmation, fixed D012 score cutoffs exceeded on **6.5924% balanced / 6.3281% unweighted** of confirmation decisions vs 1.9924% in calibration. This is a reason to test temporal stability, **not authorization to adjust thresholds using April 21–27 confirmation outcomes**. D013's explanatory analysis is known before D014 design, so it is a hypothesis source; it is not independent predictive evidence.

## Data rights, pre-price date selection and frozen original models

- Historical source: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) (Quant Arena / LaPlace's Eye / Einsia AI), **CC BY-NC 4.0 noncommercial with attribution**, publisher SHA `fa85d7b95e56e81317ac349f52e916ca482f0f68`. No raw quote/price sequences or individual model predictions committed.
- Same pinned three stock members and publisher `SHA256SUMS` checks: `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet`; no stock substitution, source permissions or license changes.
- Before reading ANY *new* post-May-16 price, volume, flag, target or model score: source-authenticate each original Parquet member, read **only** `available_at` timestamps to find common observed exchange-local trading dates strictly **after May 16, 2022**. Freeze the **first forty common observed dates** as **20 label-free warmup**, next **10 one-time prospective confirmation**, next **10 SEALED later final**, and commit canonical SHA256 manifest (stock list, three date lists, source checksums and calendar). Selection uses no source prices/outcomes.
- The previously registered D012 `Apr 28–May 16, 2022` ten-day final block and D009 `Feb 22–Mar 7` final block remain unscored, strictly inaccessible to features, labels, model fitting, score summaries or choices. D014 dates are strictly later than D012 final's final date. No FI-2010 reserved data. Reauthentication may read original complete compressed Parquet member bytes for publisher checksum, and a boundary Arrow batch can decompress unintended rows; **only approved dates may become market observations**. Holdout isolation is statistical, not cryptographic.
- Recreate the ORIGINAL D012 two fitted, global three-feature `StandardScaler + LogisticRegression(C=1, solver=lbfgs, max_iter=400, random_state=7007, sklearn=1.6.1)` models, `class_weight=balanced` vs `None`, **only on D012 Mar 8–Apr 6, 2022 fit dates**, exactly as before. Confirm original **54,290** complete-book eligible train examples. The old D012 unlabelled Apr 7–20 stock score cutoffs (original p98, strict greater-than) are **published frozen baseline values**, NOT re-estimated from D013 confirmation.
- Feature vector is frozen: current spread bps (cap 100), displayed level-one bid/ask volume imbalance, and displayed first-five-level volume imbalance. Same source flags, `available_at` gating, five prior contiguous observations within same stock/day/continuous auction, maximum 30s gap, exclude closing call. Model output is an uncalibrated *score* `s=max(p_up,p_down)/(p_stationary+1e-12)`, with up/down choice from max of up and down. **No execution stream, queue position, bid fill, trade sign or demonstrated alpha**.
- Targets only on the 10 later confirmation dates: next **five valid quotes** arithmetic midprice average, ±0.2% relative to origin midpoint, same stock/day/continuous auction, 30s continuity; up=1, stationary=2, down=3. On 20 warmup dates: **NEVER compute future targets**, even for internal reporting. Later 10 sealed dates are never admitted to any price-dependent calculations.

## Two predeclared policies — comparison, not tuning

For EACH of the two frozen models, apply both policies to exactly the same decision-ready quote origins:

**S — frozen static reference.** Reuse each stock's *exact original* D012 cutoff from Apr 7–20 calibration, never alter it. Threshold equality is abstention. These fixed cutoffs are reproducibility gates.

**R — rolling past-10-day recalibration, entirely label-free.** Score each of the twenty newly frozen *warmup* dates using only current/past source features, without target construction. Before each of the ten confirmation **trading days**, independently for each stock/model set the cutoff to the `higher` 98th percentile of all eligible quote scores from its immediately preceding **ten complete observed common trading days** (warmup and later earlier confirmation days). Apply `score > cutoff` to **the full next trading day only**; update AFTER the day closes using that day's quote scores for the *following* day, **never the current day**, and never its outcomes. Tied scores never trigger extra alerts. Require at least one valid score for each previous day and a fully ordered ten-day window, or fail closed instead of fallback or expanding the window. The rolling method has no mathematical guarantee of a 2% future rate under abrupt shift.

**Frozen analytical comparisons:** two fitted models × two cutoffs = four fixed policies, not four candidates to select from the confirmation. Do not add another lookback, percentage, model, feature, stock or cutoff, even if results disappoint.

## Estimands and scientific fail gates

**Primary operating-stability metric** (source decision-time population only, irrespective of target): absolute deviation of realized alert fraction from 2%, by model/policy/stock/day and pooled, plus fraction of stock-days above **4%** and maximum day/stock rate. Show the complete distribution, not just pooled means; compare paired daily absolute errors of R vs S. No claim 2% must hold on future dates.

**Primary scientific reliability metric** (identical confirmation origins with legitimate future labels): count of up and down alerts, up/down recall, directional precision, wrong-direction alerts including stationary and opposite direction, false alerts per 1,000 eligible labelled origins, and confusion + abstention count. Report both current/past denominators and label-verifiable matched denominators separately; never silently map abstention to stationary.

**Explicit hypothetical cost exercise**, not trading money: among verifiable directional alerts assign +1 unit for an alert matching the true direction, −4 for an incorrect directional alert, and 0 for abstention. This *illustrative 4:1 false-to-correct cost ratio*, declared before fresh source outcomes, has break-even directional precision **80%** for nonzero alert count. Also show 1:1 and 9:1 sensitivity solely as descriptive scenario analysis. This is not a measured investor utility, risk appetite, actual return, slippage or price impact. A no-alert policy scores exactly zero and is a necessary baseline. Do not select the best sensitivity scenario post-hoc.

**Decision and stop rules:** A candidate is not trustworthy on this evidence if it merely reduces alerts, if utility under primary 4:1 cost is nonpositive, if either direction has zero detection, if days/stocks remain highly unstable, or if any reproducibility/source guard fails. Even positive cost utility in just ten days would be provisional: require adequate day/stock distribution, precision and recall reporting with **day-cluster rather than quote-IID** uncertainty (bootstrap 2,000 resampled common trading days, all stocks together; seed 7007; descriptive interval, no causal p-value), and a separate human review before any sealed final evaluation. No model is promoted in D014 automatically; final remains strictly sealed.

## Stepwise authorization and source hygiene

1. Commit this protocol and synthetic-only rolling-cutoff/date-isolation tests; routine GitHub CI remains synthetic-only.
2. Run separate, timestamp-ONLY publisher-authenticated metadata job to choose 40 post-May-16 common observed dates; commit SHA256 date manifest BEFORE new quote/volume/target reads, then delete its temporary source-reading job.
3. One specially audited source-run may reconstruct D012 original fit, score fresh warmup without labels, evaluate four precommitted policies **once** on the ten confirmation days, emit aggregate stock/day/session evidence only, never open sealed price rows, then remove its temporary access job.
4. Preserve PR #7 draft/unmerged and BOTH prior final tests; do not evaluate D014's new final unless separately approved after reviewing all outcomes. No ordinary CI may fetch provider source.

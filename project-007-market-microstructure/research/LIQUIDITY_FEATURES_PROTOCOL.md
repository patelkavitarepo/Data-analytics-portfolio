# Project 007 — D010 preregistration: snapshot liquidity features (TRAINING-DATES ONLY)

**Recorded November 11, 2026 before any D010 market-price re-read.** Human direction: "Alright Holmes lets keep it moving" after D009 baseline validation. This authorizes investigating source-backed order-book **snapshot** features, NOT unlocking the earlier five validation dates (Feb 15–21), not opening the final ten dates (Feb 22–Mar 7), not creating live orders, and not claiming trading profitability. AI-assisted design and interpretation; results require actual source verification.

## Scientific question and scope

**Question:** Do contemporaneous ten-level order-book *snapshot* liquidity conditions contain a more useful signal for predicting the existing three-class future-midpoint labels than a constant training majority or the fixed previous-five-midpoint rule, **on previously unexamined internal training dates**?

The public [Quant-Arena Public L1 source](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) distributes quote snapshots every ~15 seconds, with best through ten-level bid/ask prices and displayed share volumes, source timestamps and quality flags, under **CC BY-NC 4.0 noncommercial use with attribution**. It is **not** an event-by-event order message stream. Do **NOT** call snapshot depth changes "true order-flow imbalance," compute queue priority or infer fills. Separate market and 2022–23 calendar from the original FI-2010 Helsinki benchmark.

## Frozen source and train-internal dates

- Exact publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`, three already authenticated stock members `000012.SZ`, `000025.SZ`, `000031.SZ`, independently checked against publisher `SHA256SUMS`.
- Preserve [D009 canonical date manifest](CHRONOLOGICAL_SPLIT_MANIFEST.json), SHA256 `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6`.
- **Only the 20 previously approved training dates are admitted to D010 feature/label computations.** Subsplit the exact ordered **first 14** for model fitting, **last 6** for a single frozen internal chronological confirmation. No shuffling of dates, stocks or quote-level observations. Original five-date **validation and final ten-day test remain unscored and unexamined in D010**, respectively. No tuning on the new internal confirmation after scoring it.
- Parquet caveat: individual whole-stock source files must be downloaded for member SHA256 verification, and a streaming batch may physically decompress rows on the other side of the training cutoff; unapproved dates must never be converted to feature or target rows. This is **statistical** isolation, not a byte-level claim of inaccessible data.

## Original unchanged labels and observation eligibility

- The exact D009 `make_examples` target remains fixed: `k=5` future valid quote midpoints, average future relative to decision-time midpoint, class **1 up**, **2 stationary**, **3 down** at ±0.2%, with no cross-stock/day/morning-vs-afternoon boundaries and a maximum adjacent 30-second gap.
- Only regular continuous-auction windows are eligible: **09:30–11:30** and **13:00–14:57 exclusive** local UTC+08; exclude the afternoon closing call auction. No stale/missing-depth/current source-time violations or invalid best quotes.
- Feature vectors use only the **current** book snapshot, at decision `available_at`, and never use a future quote, future label, future trading-day statistic or target-exclusion reason to construct an input. B1's fixed previous-five lagged signal is computed separately from its historical midpoint series.

## Exactly three registered liquidity features

For a current quote snapshot requiring **complete valid levels 1–5 on both sides** (non-null, strictly positive prices, nonnegative integer share volume, a monotonic bid/ask price ladder, noncrossed book, positive total side volume, `stale=False`, `missing_depth=False`, `source_event_time<=available_at`):

1. **Spread, in basis points**: `10,000 * (ask_price_1-bid_price_1)/mid`. Numeric value clipped to `[0,100]` bps for fixed outlier control, not optimized on labels.
2. **Top-level displayed volume imbalance**: `(bid_volume_1-ask_volume_1)/(bid_volume_1+ask_volume_1)`, requiring positive denominator; range [-1,1].
3. **Five-level displayed volume imbalance**: `(sum(bid_volume_1..5)-sum(ask_volume_1..5))/(sum(bid)+sum(ask))`, range [-1,1].

No order messages or trade initiator flags are in the public snapshot file. Missing one of the mandatory depth levels makes B2 **abstain**, not impute or replace a source level. The quality/coverage effects must be reported by stock and source date. Absolute volume is intentionally excluded from this first cross-stock model to avoid confusing security scales with direction.

## Frozen predictors and model configuration (no grid search)

- **B0 (training-only majority)**: constant class from the *14 fit dates only*, global across the same three stocks, tie preference 2 > 1 > 3.
- **B1 (unfitted existing trend)**: existing fixed B1 five-previous-quote signal from `chronological_baselines.make_examples`, no refit.
- **B2 (single fixed liquidity-feature model)**: `StandardScaler` fitted on the 14 fit dates only, then scikit-learn **multinomial logistic regression** with `C=1.0`, `class_weight="balanced"`, `solver="lbfgs"`, `max_iter=400`, `random_state=7007`. Deterministic single fit, no search, no class-specific manual threshold tuning. In case the source lacks all three classes, fail closed; no ad hoc alternative.
- B2 fit uses label-eligible and complete five-level depth feature rows from fit dates. Confirmation comparison uses **identical confirmation rows with valid future target, B1 history and B2 depth**, so differences aren't hidden by differing coverage. Also report B0 and B1 full eligible coverage separately for context. Do not compare different denominator metrics as though they were matched.
- Primary comparisons: three-class macro-F1 and balanced accuracy, then accuracy; report confusion matrices, up/down recall, per-stock and per-day coverage, plus count of training records excluded for invalid depth. This is **internal training-only confirmation**, *not* the original untouched five-day validation or the sealed final test.
- No p-values treating overlapping next-five targets as independent; no naive row bootstrap. Do not interpret coefficients as causal effects or feature importance unless separately tested. If B2 performs badly, report that without fitting a new model to rescue the result.

## Engineering and publication gates

1. Synthetic tests prove feature determinism, source-availability restrictions, level ordering, no future price leakage (mutating later quotes cannot change an earlier feature), missing-depth abstention and hard date-only isolation.
2. Real-source one-shot runner must verify each publisher member SHA256 and frozen 20 training-date row counts before computing features. It may use only train dates, never Jan 4–10 discovery, Feb 15–21 original validation, or Feb 22–Mar 7 final evaluation prices.
3. Source records remain ephemeral. Publish only date split, per-stock/day aggregate class counts/metrics/coverage and licensing/limitations; no raw price, order-depth rows, or per-origin prediction sequences committed.
4. Keep PR #7 draft and unmerged, restore synthetic-only CI after a one-time empirical study.

**Decision after D010:** An observed internal comparison may suggest whether an *independently preregistered* prospective validation is justified. Do not retune B2 using the same six internal confirmation dates or the original five validation dates. Final ten-date holdout remains closed until a distinct final-model evaluation decision.

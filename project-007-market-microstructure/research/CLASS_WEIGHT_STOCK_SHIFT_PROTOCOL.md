# Project 007 — D011 preregistered diagnosis of B2 cross-stock failure

**Frozen November 12, 2026 before any new D011 market-price read; successfully executed afterward without modifying the registered comparisons.** Full findings: [CLASS_WEIGHT_STOCK_SHIFT_RESULTS.md](CLASS_WEIGHT_STOCK_SHIFT_RESULTS.md). Human directive: "On to the next", following our recommendation to investigate why the class-balanced snapshot-liquidity model B2 collapsed on 000031.SZ. The research design and provisional interpretations are AI-assisted, not authored conclusions by the human lead.

## Hypotheses (not findings)

D010 reported B2 macro-F1 **0.1124** and **0% stationary recall** for 000031.SZ on the **six previously examined internal confirmation dates**, while pooled B2 achieved balanced accuracy 0.5199. Candidate explanations to investigate, NOT assert: (a) inverse-class weighting may excessively favor rare up/down classes in a highly stationary dataset; (b) source-quote spread and bid/ask imbalance distributions may differ across stock identities; (c) global scaling combined with stock-heterogeneous feature distributions may harm generalization. Other possible causes remain unobserved.

**This study must NOT use the original D010 six confirmation dates (Feb 7–14), D009 five validation dates (Feb 15–21), or final ten-date sealed test (Feb 22–Mar 7) in feature distributions, fitting, prediction scoring or model revision.** D011 is a retrospective diagnostic of the **same 14 D010 fit dates**, so it does not create a new independent test set.

## Pinned source, date and selection

- Quant-Arena Public L1 (Quant Arena / LaPlace's Eye / Einsia AI), **CC BY-NC 4.0 noncommercial with attribution**, pinned exact source revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`, same published SHA256 verified members `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet`.
- Original immutable D009 date-list SHA256 `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6`; **only the first 14 training dates** `2022-01-11` through `2022-01-28` may enter source quote features and label processing.
- To avoid an in-sample-only examination, **predivide** those exact 14 days chronologically into **first 10 dates (Jan 11–24) for fitting** and **last four dates (Jan 25–28) as a single diagnostic comparison**. The 4 dates were previously part of D010's fitting allocation and are NOT an untouched final validation.
- Whole publisher stock member bytes must be fetched for source-file SHA256; a Parquet decoding batch may physically reach outside Jan 28, but only the first 14 selected-date rows may be converted to quote features, labels or predictions. No future source market quote rows may be included in any model computation, observation or reporting.

## Registered descriptive diagnostics (no exploratory feature search)

On both the ten-date fit and four-date diagnostic portions, show **per-stock**:
- Full input quote count, k=5 label-eligible count, 3-class target prevalence, full-depth feature-eligible count and last-five-lag B1 coverage.
- Descriptive **mean, p10, median, p90** for only the three existing B2 features: spread basis points clipped to 100, best-level displayed volume imbalance, five-level displayed volume imbalance. Use deterministic, finite percentiles; no data-driven rejection threshold.
- Per-stock directional vs stationary class support; report data clustering/serial dependence. Do NOT expose raw vendor quote, book-level values, individual example sequences or predictions.

## Registered fixed model diagnostics: class weighting vs stock shift

Train **exactly two** global three-feature, three-class estimators on the same **first ten dates' eligible complete-depth rows**:
1. `W_BALANCED` — `StandardScaler()` plus `LogisticRegression(C=1.0,class_weight="balanced",solver="lbfgs",max_iter=400,random_state=7007)`, reproducing the D010 *configuration*, but **not the original D010 14-date fit**.
2. `W_UNWEIGHTED` — identical scaler, features, solver, C, iteration cap and seed, but with `class_weight=None`; a **diagnostic ablation**, not a promoted model.

The original D009 B0 fit-only majority and unfitted B1 are retained as interpretive references. Compare all methods on the **exact same k=5 target-eligible, B1-history-covered, complete-depth four-date rows**, using confusion matrices, 3-class accuracy, macro-F1, balanced accuracy, true-direction recall, *precision for predicted up/down*, and predicted class frequencies by stock. No class threshold tuning, no grid search, no reweighting based on the four dates, no per-stock models, no feature additions, no repeated looks for selection.

Report model coefficients and intercepts **only in standardized feature space** with clear noncausal caveat, and **training-fitted scaler mean/std** (these are aggregate model parameters, not source rows). Report stock-by-stock standardized feature-center shifts using the ten-day global scaler, explicitly *diagnostic correlations*, not proof of an explanatory cause. Compare whether the original 000031 failure pattern (excess directional predictions, almost no stationary) **reappears** in the registered four-date split. If it does not, record the lack of replication.

## Reporting and stop gates

- Fail closed if authentic source member hashes differ from original frozen audit; no replacement symbol, dates or different vendor.
- Synthetic unit tests must detect leakage across Jan 28, parsing errors, altered five-level quote feature values, partial-depth failures, invalid rows, classes/metric mismatch and source invalidity.
- Run just one ephemeral authenticated CI job, remove the source-download job and return to synthetic-only CI. Commit aggregate diagnostic report with source attribution and limitations. No advanced deployment, brokerage orders, market-making profitability, model promotion, FI-2010 holdout access or merge.
- **Do not use already examined D010 internal confirmation or D009 validation to decide between these models.** This is investigation of a failure mechanism, not a new proof of performance. The final ten-date test remains untouched statistically.

**Suggested next gate only after results:** If the class-weighting hypothesis receives some support, define new hypotheses and acquire genuinely later, *new and prospectively frozen* non-holdout dates for independent development. Do not unlock the already sealed test or relabel a previously used validation window as unseen.

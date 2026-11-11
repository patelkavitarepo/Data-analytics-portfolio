# Project 007 — predeclared cross-stock label-construction replication (proposal)

**Status:** Proposed design, not yet executed. Prepared after the independently verified single-stock/two-day Quant-Arena pilot. The human lead has not selected a predictive model or approved any holdout release. Study remains noncommercial under the source's **CC BY-NC 4.0** license. AI-assisted design; not a human finding.

## Hypothesis and purpose

Test whether the strong stationary-class prevalence and its sensitivity to the chosen classification threshold are reproducible **across multiple securities and trading dates**, rather than unique to source stock 000012.SZ. This is a **label-construction study**, not a forecast or trading strategy. Findings must not be used to validate FI-2010's original Helsinki 2010 labels.

## Source and frozen definitions

- Publisher: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), **CC BY-NC 4.0**.
- Repository revision: `fa85d7b95e56e81317ac349f52e916ca482f0f68` (already observed). Verify selected member SHA-256 against publisher's `SHA256SUMS`; require successful HTTP 206 range reads and member integrity, never entire 6.23 GB TAR as fallback.
- Select **three stock files** deterministically: the previously reviewed example `000012.SZ.parquet` plus the next **two lexicographically smallest distinct, valid** `.SZ.parquet` file paths listed in this pinned archive. If fewer than three exist, report and stop. Do not select stocks for favorable labels or recentness.
- Select **the first five chronologically distinct complete observed trading dates per stock**, using only identifiers/availability timestamps before examining the price-based labels. Report if dates are missing and do not replace with cherry-picked days. Do not claim that chronological presence proves an exchange-complete day.
- **Reserve all later dates** from each stock for future hypothesis testing. Do not score, train on or explore future reserved labels in this descriptive pilot.
- Preserve exactly the previous fixed rule: best-mid `(bid_1+ask_1)/2`, fractional difference to arithmetic mean of next k midpoints, class 1 up if >= +threshold, class 3 down if <= -threshold, class 2 otherwise. Exclude source-invalid/missing/stale/one-sided/locked/crossed quotes, stock/day boundary, >30 second gaps (provisional cadence rule), and insufficient valid future targets. Never fill or bridge gaps.
- Horizon grid `k={1,2,3,5,10}` at the **±0.2%** rule. Threshold sensitivity **at k=5 only**: ±0.1%, ±0.2%, ±0.4%, fixed before new data access. Changes in threshold are different definitions, not parameter tuning to improve prediction.

## Output and numerical checks

1. Provenance inventory: exact source full revision, member SHA256, bytes transferred, selected dates, source schema, quality-flag distributions, excluded/eligible counts. No row-level vendor quotes in Git or logs.
2. Per-stock/per-date and pooled (explicitly weighted) class counts and stationary percentages **among eligible labels**. Always report all-source-row denominators and exclusion reasons; QC flags can overlap.
3. Independent slow label oracle verifies **every** optimized origin record, including exclusion reason and future indices, for every stock, day and horizon. Check class sums equal selected observation counts; fail closed for any mismatch.
4. Report descriptive variation by stock/day, and threshold sensitivity per stock/day. Do not compute test-set significance using naive IID assumptions because labels overlap heavily.
5. Document any discontinuities and missing dates. If a source file is oversized, inaccessible or schema-incompatible, report the problem without substituting an unverified mirror or another unannounced security.
6. Do not fit a predictive model, use any real broker, compute execution P&L, optimize thresholds, or merge the PR based on these descriptive results.

## Decision after replication

Only if the source labels remain trustworthy and boundaries are independently verified should a **separate, preregistered predictive experiment** be considered, beginning with a naive training-only benchmark. Before that experiment, define session-block training/validation/final-reserved holdout with gap/purge rules and no lookahead. A benchmark-classification score is not executable trading alpha.

**Current empirical evidence:** [verified two-day report](QUANT_ARENA_EMPIRICAL_PILOT.md). Second-run independent quote check matched 10,230/10,230 label records. Further panel analysis has not run yet.

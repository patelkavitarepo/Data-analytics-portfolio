# Project 007 — Prospective chronological prediction design (NOT YET EXECUTED)

**Status:** study design only, written during the D008 explicit-session labeling audit; **no model has been trained, scored, or selected, and no later-date market prices have been opened**. The human lead authorized moving forward from data quality to session-aware engineering and design, not discretionary release of a holdout. AI-assisted experiment design; the human lead has not supplied an empirical result.

## Separate scientific questions

- **Completed discovery:** On Quant-Arena Public L1 (Shenzhen 2022), we verified historical stock/day quote-label construction and found that scheduled lunch recesses require explicit session segmentation.
- **Next prospective research question:** Can strictly *past/present* book information distinguish later 5-snapshot midpoint-average up/stationary/down movements *beyond a training-only constant-majority baseline* on unseen chronological dates?
- **Not tested here:** tradable returns, execution costs, spread capture, queue position, market-making profit, or original FI-2010 Helsinki label correctness.

## Source, terms and permitted access

Dataset [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) by Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0, noncommercial**; same SHA-pinned publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`. Use per-member published SHA256 and ephemeral local storage; do **not** commit raw quotes, proprietary files, individual price rows or model-derived pseudo-price reconstructions.

**Already inspected/discovery dates:** January 4, 5, 6, 7, 10, 2022, same stocks 000012.SZ, 000025.SZ, 000031.SZ. These dates may inform engineering tests but cannot be called an untouched out-of-sample final test.

## Proposed date partition — source identifiers only

Before reading any additional bid/ask/volume prices or derived targets:
1. Verify source SHA256 and inspect **only available_at date identifiers** to form the sorted intersection of stock trading dates across the three fixed securities. Halt if source version, stock identity, timezone or chronology differ from the archived source audit.
2. Remove the five already inspected discovery dates. Require **at least 35 additional common observed dates** for the study. Use the **first 20** as training, next **5** as validation, next **10** as **sealed final holdout**. Any subsequent dates remain unused. No replacement based on label class mix, performance, null counts or economic events.
3. Store the selected **date-list SHA256** and partition boundaries in a public metadata-only manifest *before* reading market prices from training/validation; do not disclose provider row-level data.
4. **Do not open final 10 dates' price or label columns during feature selection, hypothesis iteration or validation.** Final test requires a separate explicit human decision after model/classifier and all preprocessing choices are frozen.
5. No random quote-level split. Date-only partitions and session-isolated targets prevent cross-boundary k=5 future windows; never label beyond a same-stock/date/session boundary. If a security/date is incomplete, report missing coverage rather than swapping in a different observation period.

## Fixed source and target rules

- Eligible decision quote: positive best bid, strictly ask > bid, non-stale and non-missing-depth source flags; `source_event_time <= available_at`.
- Exchange-local operational session: **09:30:00–11:30:00 morning** and **13:00:00–15:00:00 afternoon** (inclusive endpoints). These are distinct, and *no* feature/label history crosses the lunch break or a stock/date boundary. Afternoon contains the **14:57–15:00 closing call auction**, a known distinct phase that must be reported and could justify a later, separately preregistered segmentation revision; do not silently treat it as identical execution liquidity.
- Adjacent observed quote gap maximum **30 seconds**, no filling/interpolation and no extending source quote validity through a recess.
- Target: class 1 up, 2 stationary, 3 down from the average of the **next 5 strictly future valid midpoints** relative to current midpoint; threshold ±0.002. End-of-segment and otherwise incomplete targets are *excluded*, not class 2.
- Model input can only use values published **at or before** the decision's availability timestamp; no future labels, future returns, day-level aggregates completed after the decision, or whole-sample normalizations.
- For any lagged input feature, restart history after a quote invalidation, session boundary, or gap >30 seconds. Quote snapshot recency and feature availability should be logged; latency and order book queue mechanics are not represented by this pilot.

## Candidate benchmarks (not yet evaluated)

**B0:** constant class chosen as the majority among eligible *training* labels only; no day-eight or validation counts used to pick the class.

**B1:** predefined simple backward-looking midpoint-trend heuristic using only an origin and previous 5 contiguous eligible quotes; map a ±0.002 backward-looking midpoint trend to class 1/2/3. If insufficient backward history, abstain and report coverage; evaluate on the same eligible future-target population when possible.

**Future candidate (requires separate approval):** a small book-feature model using spread, relative depth imbalance and recent historical quote changes, fitted using only training days. Do not add features after seeing the final test.

## Model selection and leakage controls

- Report **macro-F1 and balanced accuracy** (primary diagnostic combination) alongside accuracy, class confusion counts, per-class recall and fraction of origins excluded/abstained. Heavy stationary class prevalence makes accuracy alone misleading.
- Evaluate by stock and by trading day, not only pooled source rows. Because k=5 targets overlap substantially, naive IID confidence intervals/p-values are inappropriate. Future intervals should be built using stock/day clustering or chronologically disjoint folds, with clear small-sample limitations.
- Source QC, feature imputation, normalization/scaler parameters, class weighting, thresholds and candidate selection are defined and/or fitted **only on training dates**, validated only on the designated five validation dates. No refitting on validation until a separately recorded decision; no use of final holdout labels to fix bugs or improve scores.
- The final holdout can be opened once per fully frozen design and should retain a documented *no retest after post-hoc modifications* rule. If data defects prevent evaluation, report that rather than quietly choosing alternative final dates.

## Stop conditions and next authorization

**At this stage, only synthetic tests and the source-confirmed D008 session audit are authorized.** Implementing the date-only metadata selection and a dry-run B0/B1 trainer will require another explicitly recorded research gate before reading new market prices. Do not merge PR #7 or imply that a high classification score is financially useful.

**Scientific question to answer first:** Does the newly enforced session policy match or appropriately correct our previously published class counts on the *already inspected* 15,233 source observations, with an independent oracle? See [SESSION_AWARE_PROTOCOL.md](SESSION_AWARE_PROTOCOL.md) and subsequent D008 results.

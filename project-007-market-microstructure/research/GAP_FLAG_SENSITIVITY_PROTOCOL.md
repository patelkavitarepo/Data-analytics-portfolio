# Project 007 — D006 preregistration: quote continuity and quality-flag sensitivity

**Frozen before the new source-data run on November 11, 2026; subsequently EXECUTED without changing the registered scenarios.** Full attributed findings: [GAP_FLAG_SENSITIVITY_RESULTS.md](GAP_FLAG_SENSITIVITY_RESULTS.md). Human directive: **"Next challenge it is holmes"** in response to our proposed sensitivity investigation. This is an AI-assisted method proposal, not a human-provided causal explanation. Noncommercial use only under Quant-Arena Public L1's **CC BY-NC 4.0** terms. This study does not contain a predictive model, deployment, or trading result.

## Objective / source

Measure whether the previous **three-stock/five-day** class distribution remains similar under *predeclared changes to quote continuity and flag handling*, explicitly reporting the effect on **who is eligible** as well as label values. The previous `THREE_STOCK_PANEL_RESULTS.md` at k=5, ±0.2%, max 30 seconds, strict source flags is **frozen** and is our reference. We are not trying to select the setting with the greatest stationary share or forecasting accuracy.

**Unchanged source/version/selection:** `Ashitemaru/Quant-Arena-Public-L1`, publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`, source files `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet`; only January **4, 5, 6, 7 and 10, 2022**; input price, first-level bid/ask midpoint, original source-time and quote flags. Use SHA256SUMS to verify each member, never fetch the full archive. No new stock or date selection, later-date quote outcomes or FI-2010 holdout access.

**Fixed label target:** k=5 sampled quote snapshots ahead; neutral band ±0.002 around arithmetic average of next five midpoints relative to origin; price-valid, same-stock, same-day, contiguous futures; origin itself excluded if invalid. All results use class 1 up, class 2 stationary, class 3 down; include excluded origins as a distinct category. **No other horizons/thresholds may be used to choose these settings.**

## Scenarios fixed in advance

**Group G — quote gap rule, source flags fully respected:**

| ID | Max permitted adjacent interval in same stock/date | Interpretation |
| --- | --- | --- |
| G15 | 15 s | Stricter sensitivity for nominal 15s sampling |
| G30 | 30 s | **Frozen primary / existing reference** |
| G60 | 60 s | Permissive diagnostic; may span short data gaps |
| G120 | 120 s | More permissive *stress test*, not an endorsed data-cleaning rule |

Always preserve stock/day boundaries, outright invalid prices and both quality flags. Never let a gap scenario cross calendar days. Never interpolate a missing quote. G60/G120 **are not candidate deployment settings**.

**Group F — input-quality flags, with gap fixed at 30 seconds and raw best-quote prices still required to be positive and ordered:**

| ID | Diagnostic counterfactual | Acceptable for real analysis? |
| --- | --- | --- |
| F0 | Honor stale and missing-depth flags | **Yes; same as G30** |
| FS | Deliberately ignore only `stale` (including source event time missing) | **No — stress-only** |
| FD | Deliberately ignore only `missing_depth` | **No — stress-only** |
| FSD | Deliberately ignore both flags | **No — stress-only** |

A source flag is **never** changed in the original data or exported. These are *in-memory counterfactual label constructions* only. No invalid/locked/crossed, missing, nonfinite or negative best prices are admitted even in the stress settings. Ignoring flags is explicitly not a recommendation for future live use; it might introduce fictitious executable liquidity.

## Expected outputs (do not select after results)

1. Before any sensitivity result: independently reproduce previous G30/F0 stock-level `all rows / up / stationary / down / unlabelled` values exactly: 
   - `000012.SZ`: `5078 / 122 / 4438 / 126 / 392`.
   - `000025.SZ`: `5077 / 58 / 4267 / 39 / 713`.
   - `000031.SZ`: `5078 / 308 / 4107 / 271 / 392`.
2. Per-scenario / per-stock / per-day counts, eligible denominator, stationary among eligible and excluded-reason breakdown, with explicit **newly eligible**, **newly excluded**, and **still-eligible-but-different-class** compared with frozen G30/F0 **on the same original row indices**. Do not use percentages alone as causal evidence.
3. Descriptive original source-quality cross-tab (stale flag, missing-depth flag, invalid/absent best quote, overlaps); counts of adjacent source timestamp gaps exceeding each threshold, only within stock/date. Quality categories may overlap, so never sum non-disjoint counts as distinct missing observations.
4. Independent, slower oracle verifies every origin's class, future target indices and exclusion reason in **every scenario**. Fail closed if any mismatch.
5. Noncommercial aggregate report only, including exact source-file hashes, fixed source version, counts and known limitations. No quote-level source data, raw Parquet or credentials committed.
6. Report whether the observed **between-stock ranking** changes under each scenario and whether any difference is due partly to eligibility changes. No p-values based on overlapping observations, no optimization or predictive model.

**Interpretive boundaries:** A stock's quote gaps or flags may be associated with changes in eligible labels without proving causes of missingness or future return behavior. The results cannot validate FI-2010's inaccessible Helsinki original labels, compare trading profitability, or imply a live market-making edge.

**After this diagnostic:** Consider a separately preregistered chronological training/validation/holdout design *only* when source validity is adequate. All source dates beyond these five per stock remain reserved.

# Project 007 — D008 registered plan: explicit Shenzhen session labels and chronological prediction gate

**Research status:** engineering validation authorized by the human lead's continuation (“On to the next Holmes”). This plan precedes the new real-data session audit. **No predictive model authorized or fitted; no future-date market outcomes accessed.** AI-assisted methods, not human-authored empirical interpretations.

## Why session structure matters

The authenticated D007 panel (same three Shenzhen stocks on Jan 4/5/6/7/10 2022) found fifteen exactly 11:30:00–13:00:00 source gaps, matching Shenzhen's scheduled midday break. Removing only the maximum time-gap rule constructed **74 false across-lunch targets**. A 30-second continuity rule protected the original study, but session labels should be an *independent invariant* so that permissive gap settings can never silently bridge lunch.

## Rules fixed before the next source read

- Dataset: Quant-Arena Public L1 by Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0 (noncommercial research)**, pinned revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`. Authenticate original file SHA256 against publisher `SHA256SUMS`. No vendor raw records in git, no full 6.23GB download, no new dates/stocks.
- Same stock files: `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet`; first five observed dates Jan 4, 5, 6, 7, 10 2022 only; **15,233** source rows.
- Exchange-local **+08:00** `available_at`. Morning continuous auction: **09:30:00 through 11:30:00 inclusive**; afternoon regular/closing window: **13:00:00 through 15:00:00 inclusive**. These are **operational source-label segmentation rules**; the closing call auction 14:57–15:00 has different microstructure and must be disclosed as such. The inclusive exact endpoints reflect the observed 11:30/13:00 source observations and are not universal exchange-event semantics. Outside these windows is explicitly *out-of-session* and must never yield a forward label.
- Keep source quality requirements: `stale=False`, `missing_depth=False`, positive `bid`, strictly `ask > bid`; no interpolation. **Max 30-second adjacent timestamp** remains primary.
- Pre-fixed target: future **mean of the next five midpoints**, fractional relative difference from origin, ±0.002 class thresholds (1 up, 2 stationary, 3 down). A target may not cross security, trading date, *morning/afternoon session*, invalid quote, or max interval. Last incomplete targets are excluded, never labeled stationary.
- Independently compare optimized session-aware labels against a separate slower per-origin oracle for *all rows*, including excluded and future-index lists. Both calculators must agree. Validate **legacy strict labels** against the frozen D005 reference first.
- Diagnostic counterfactual: **remove only max-gap rule while keeping source flags and explicit session boundaries enforced**. Require **zero** across-lunch labels regardless of interval setting; inspect any extra labels solely inside the same session. Do **not** promote no-gap as an endorsed setting.
- Report source-quality exclusions and per-stock/day eligible class counts. If explicit session handling changes valid labels relative to legacy G30, disclose class and eligibility differences, rather than forcing a match or rewriting past reports.
- No day after Jan 10, 2022 receives market-price analysis; original FI-2010 days 9 and 10 stay untouched.

## Next *design only* chronological prediction experiment

Following the above engineering gate, propose (but DO NOT train/score until a separate decision):
- **Discovery engineering segment**: existing first five observed dates per stock (Jan 4,5,6,7,10, 2022). Already inspected repeatedly; **not an untouched final test**.
- **Prospective modeling design** on later source dates selected by ordered observed trading-date identifiers **before** accessing later quotes: 20 subsequent stock-session dates for training, next 5 for validation/model selection, next 10 held under a **sealed final test**. If fewer than 35 later dates are valid, stop and revise *before opening prices*. No shuffled observations or within-day random splitting. No cross-boundary features or future targets.
- **Initial baselines**: training-only constant-majority class, then training-only backwards-looking midpoint-change rule; advanced price/LOB features only if those are beaten consistently on validation under a preregistered metric. Comparisons should include macro-F1 and balanced accuracy, per-stock/day class prevalence, coverage and instability; all performance is classification, *not executable alpha*.
- Features for any predictive test must use source **available_at <= decision time**, strictly current/past bids/asks and potentially past depth; source event time must not exceed availability. Prevent indicator windows from crossing stock/day/session, stale/invalid segments or midday closure.
- Overlapping k=5 future-label windows must not leak from training into validation/holdout. Use chronological **entire-date block** splits, a one-full-session purge/embargo near transitions if needed, fit scalers/imputation/thresholds on training alone, never use held-out labels to pick models; no forward-fill across session boundary. Final reserved block can only be opened by explicitly separate evaluation.
- Any later-date model data use must respect CC BY-NC; no raw vendor prices pushed to GitHub.

## Final caveat

This is an independent Shenzhen 2022 source-label project, **not** a reconstruction of FI-2010's Helsinki 2010 publisher labels. It establishes no modern market edge, fills, queue priority, fees or trading returns.

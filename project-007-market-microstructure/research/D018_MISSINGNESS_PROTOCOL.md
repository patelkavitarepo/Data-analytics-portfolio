# D018 — Missingness-aware reporting protocol, before new source access

Case 017 (December 8–21, 2022) **spent its confirmation** and failed before aggregate reporting due to undefined stock-day directional AP. See `D017_FAILED_RUN_POSTMORTEM.md`. The December 22, 2022–January 5, 2023 final remains sealed. No D017 rerun is authorized.

## Frozen reporting rule for a future fresh confirmation

- Preserve **all source-origin and matched-origin denominators** and per-stock-day metrics, including null AP and class support.
- Undefined AP (including no matched directional positives) is **not zero**, not a valid ranking estimate, and not evidence of poor or good ranking.
- Report missing/undefined slots by stock, date, model, and direction. Show number of complete three-stock days out of the original ten; never hide the excluded days.
- For a descriptive day-cluster AP-lift interval, restrict to **complete three-stock dates** for that model/direction, clearly label the changed estimand, and withhold the interval if fewer than two dates remain. Bootstrap 2,000 whole dates with seed 7007. This conditional interval can suffer selection bias and is not comparable to an all-date interval without qualification.
- For model-to-model paired differences, require *joint* complete dates across both models for each direction. Never compare different date subsets or silently impute missing AP. If joint complete days are fewer than two, withhold comparison interval.
- Keep ranking and probability calibration separate. Brier may be defined even when AP is undefined, provided there are matched observations.
- All non-finite scores remain hard failures; null AP is a reported condition, not a pipeline crash.
- A future D018 calendar must be selected from **source timestamps only strictly after 2023-01-05** and committed before new quote/target reads.
- No threshold optimization, retraining, sealed-final scoring, live trading, or profitability claims are authorized.

This protocol is committed before any D018 source read.

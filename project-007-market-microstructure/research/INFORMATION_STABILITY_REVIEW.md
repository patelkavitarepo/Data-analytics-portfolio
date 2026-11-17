# Case 016 — Day-level ranking stability (D018)

**Read-only diagnostic of spent confirmation results.** Derived from successful GitHub Actions run [43291108945](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43291108945), not a new market-data query, model fit, or threshold choice. Source: Quant-Arena Public L1, Quant Arena / LaPlace's Eye / Einsia AI, CC BY-NC 4.0 noncommercial.

Frozen calendar SHA-256: `495ae84000e64114e445e7c7dbed9dec0b12d1379a53b954f9af5472b7a20899`. Ten common confirmation trading dates, three stocks, two unchanged March-trained logistic models. No final labels accessed.

## Daily paired-stock descriptive AP lift

For each day and direction, calculate each stock's average precision minus its *matched-stock-day class prevalence*, then average the three stock lifts. This is **not pooled average precision**. The table reports the ten-day mean and the observed minimum/maximum daily three-stock means.

| Original model | Direction | Mean AP lift (percentage points) | Minimum day | Maximum day | Days with positive three-stock mean |
|---|---|---:|---:|---:|---:|
| Balanced | Up | +4.879 | +1.718 | +7.850 | 10/10 |
| Balanced | Down | +9.210 | +3.812 | +14.175 | 10/10 |
| Unweighted | Up | +3.635 | +1.334 | +6.283 | 10/10 |
| Unweighted | Down | +6.136 | +3.015 | +9.939 | 10/10 |

The stronger balanced ranking is accompanied by poorer probability Brier losses (see `INFORMATION_CONFIRMATION_RESULTS.md`). Positive average daily lift is encouraging, but the stocks share dates and market conditions, and all results belong to **one already-consumed confirmation period**.

## Required before stronger claims

1. Execute the committed deterministic 2,000-replicate **paired trading-day cluster bootstrap** on the existing stock-day aggregate outputs. Report the resulting percentile intervals as descriptive, **not** independent proof of generalization.
2. Verify uncertainty and cross-stock heterogeneity, especially whether one stock dominates AP lift.
3. Do **not** retune any model or threshold on this spent confirmation window.
4. Design any new challenger and its success criteria before a *new*, source-timestamp-only frozen confirmation calendar. All D009/D012/D014/D015/D016 final periods remain sealed.
5. Do not infer execution edge, costs, or profitability from AP lift alone.

**Decision:** evidence supports continued investigation of ranking and calibration separately. It does **not** authorize model promotion, deployment, or use of the sealed final.

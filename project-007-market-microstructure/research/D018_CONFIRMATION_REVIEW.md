# D018 — Independent replication confirmation and zero-positive diagnostic

**Source:** [successful GitHub Actions run 43341331517](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43341331517), job 131610107395. Quant-Arena Public L1 (Quant Arena / LaPlace's Eye / Einsia AI), CC BY-NC 4.0 noncommercial with attribution. No raw vendor quotes committed.

**Frozen dates:** warmup January 6–February 9, 2023; confirmation February 10–23, 2023; sealed final February 24–March 9, 2023. Calendar SHA256 `9fe984246797d2a1617e5c83816fcfceb4debec268ba4cf55621cc1c454e2d03`.

## Verified outcome

The empirical run succeeded, authenticated all three pinned stock members, reproduced **54,290** original D012 training examples, and emitted aggregate diagnostics for all ten confirmation dates. **30,687** source-origin observations were represented across 30 stock-days (three stocks × ten dates). Original model specifications were unchanged. Neither new nor prior sealed-final rows were scored. The confirmation has now been **spent**; do not rerun for model/threshold selection.

| Direction | Model | Complete three-stock dates | Mean complete-day AP minus prevalence | Descriptive day-bootstrap 95% percentile interval |
|---|---|---:|---:|---:|
| Up (class 1) | Balanced | 6/10 | +4.1713 pp | [+2.8725, +5.7480] pp |
| Up (class 1) | Unweighted | 6/10 | +3.0251 pp | [+2.4317, +3.5816] pp |
| Down (class 3) | Balanced | 4/10 | +4.8518 pp | [+3.3379, +6.3657] pp |
| Down (class 3) | Unweighted | 4/10 | +3.9147 pp | [+2.8359, +5.2824] pp |

Paired balanced-minus-unweighted AP-lift difference, restricted to jointly complete dates: upward **+1.1462 pp**, 6 days, descriptive interval **[+0.3893, +2.1927] pp**; downward **+0.9371 pp**, 4 days, interval **[+0.3405, +1.8661] pp**. Each interval is a 2,000-replicate day-cluster percentile interval with seed 7007; these are descriptive, conditional on complete days, **not pooled AP** or independent significance tests.

## Root-cause investigation of undefined AP

All **ten undefined direction/stock/day slots** had nonzero matched observations and **zero positive support**, rather than zero matched observations. This is the direct reason for undefined AP under `information_audit.average_precision`, which intentionally returns `None` when no positives are present.

| Direction | Stock | Date | Matched observations | Positive support |
|---|---|---|---:|---:|
| Up | 000012.SZ | 2023-02-10 | 929 | 0 |
| Up | 000012.SZ | 2023-02-15 | 929 | 0 |
| Up | 000012.SZ | 2023-02-23 | 929 | 0 |
| Up | 000025.SZ | 2023-02-22 | 918 | 0 |
| Down | 000012.SZ | 2023-02-10 | 929 | 0 |
| Down | 000012.SZ | 2023-02-13 | 929 | 0 |
| Down | 000012.SZ | 2023-02-15 | 929 | 0 |
| Down | 000012.SZ | 2023-02-17 | 929 | 0 |
| Down | 000012.SZ | 2023-02-20 | 929 | 0 |
| Down | 000012.SZ | 2023-02-23 | 929 | 0 |

The undefined slots are identical across both models because they arise from the matched target population. The original D017 reporting crash is consistent with this kind of zero-positive AP condition, but D017's exact missingness pattern was **not** established by its failed run and must not be inferred from D018.

## Interpretation and decision

The replicated signal is **positive AP lift on a selected subset of complete stock-days**, with the balanced model having larger descriptive lift than the unweighted model on those same days. This is evidence of conditional ranking information, **not** evidence that ranking is uniformly positive across all 30 stock-days, nor a tradable profit advantage. Six of ten dates were excluded from the downward complete-day estimand; four from the upward estimand. Complete-day selection may materially bias estimates upward or downward, and small numbers of correlated dates make bootstrap intervals fragile.

A day with zero directional positives is not a model's ranking success or failure: no positive events exist to rank. It remains informative for event prevalence, false-alert risk and calibration, which should be analyzed separately. **Do not impute undefined AP as zero**, do not discard exclusions without disclosure, and do not compare these conditional complete-day estimates naively with D016's all-day estimates.

**Next research question:** how much of the signal is explained by event prevalence, stock-level heterogeneity and zero-positive-day frequency? Design a fresh, preregistered analysis using an unspent chronological period. Retain no new threshold, model, or live-trading claims; keep all final holdouts sealed.

## Reproducibility and integrity

- Empirical run: 43341331517, job 131610107395, successful.
- The confirmation is spent; no new training, threshold choice, or rerun on these confirmation labels is authorized.
- All old final holdouts and D018 February 24–March 9 final remain sealed.
- The full aggregate JSON was emitted in the run logs; this file preserves the high-level metrics and all missingness causes without redistributing market quotes.

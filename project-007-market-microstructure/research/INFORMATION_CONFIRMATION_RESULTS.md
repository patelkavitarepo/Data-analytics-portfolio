# Case 016 — Directional information confirmation (D017)

**Status:** one-time confirmation completed; diagnostic evidence only. No model adoption, no new threshold, no trading claim.

- GitHub Actions run: https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43291108945
- Source: Quant-Arena Public L1 (Quant Arena / LaPlace's Eye / Einsia AI), CC BY-NC 4.0 noncommercial, authenticated pinned publisher revision.
- Pre-price committed calendar SHA-256: `495ae84000e64114e445e7c7dbed9dec0b12d1379a53b954f9af5472b7a20899`.
- Original D012 March training examples exactly reproduced: **54,290**.
- Warmup: 2022-09-07–2022-10-12, **no warmup future labels computed**.
- Confirmation: 2022-10-13–2022-10-26, ten common trading dates, three stocks.
- New final: 2022-10-27–2022-11-09 **sealed**; all earlier final periods remain sealed.
- Source origins **30,665**; source feature/history ready **28,120**; matched with verifiable future labels **27,783**.
- Among matched observations: **1,044 upward**, **918 downward**; respective class prevalence **3.7577%** and **3.3042%**.

| Original model | Direction | Mean stock-day AP | Mean stock-day base rate | Stock-days AP > base | Matched-weighted Brier |
|---|---|---:|---:|---:|---:|
| Balanced | Up | 8.6338% | 3.7552% | 26/30 | 0.12919 |
| Balanced | Down | 12.5129% | 3.3025% | 29/30 | 0.11170 |
| Unweighted | Up | 7.3904% | 3.7552% | 26/30 | 0.03850 |
| Unweighted | Down | 9.4382% | 3.3025% | 30/30 | 0.03304 |

## Interpretation and limitations

- These AP values are **arithmetic means of individual stock-day AP**, **not pooled average precision**. The pooled ranking statistic cannot be recovered by averaging stock-day AP.
- The baseline comparison is matched-population prevalence, not the all-source prevalence. No-alert is abstention, not stationary truth.
- The balanced model exhibits stronger stock-day directional ranking, while the unweighted model has lower Brier loss. **Ranking and calibration are distinct**.
- Stock-days are correlated and intraday observations are highly dependent. Counting 26/30 or 30/30 as independent successes would be invalid. No day-clustered confidence intervals or paired model comparison have yet been established.
- This is **not** evidence of executable edge, realistic costs, PnL, positive alert utility, or out-of-sample generalization beyond this confirmation window.
- The D016 confirmation window is now **spent**: do not choose thresholds, retrain, or optimize using these outcomes. Preserve the sealed final.
- Next: implement a deterministic day-clustered paired bootstrap and a prespecified report of stability/uncertainty from this fixed diagnostic evidence, without modifying predictions or thresholds. Any subsequent challenger requires a fresh precommitted calendar.

## Reproducibility

One-time successful source-authenticated run used the frozen original scikit-learn 1.6.1 fit, class-specific `predict_proba` values (not directional score ratios), and source-origin-aligned future labels. The temporary market-access workflow was deleted after dispatch. Only aggregate statistics and methodology are retained in this repository; no vendor price rows are committed.

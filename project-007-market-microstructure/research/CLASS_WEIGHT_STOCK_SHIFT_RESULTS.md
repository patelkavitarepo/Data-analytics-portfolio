# Project 007 — D011 registered class-weighting and stock-shift forensic

**Completed November 12, 2026.** Human lead requested: "On to the next" after B2 failed on 000031.SZ. This is an **AI-assisted, retrospective training-only diagnostic** using source-verified noncommercial historical book snapshots. **No model is promoted, no later validation/final test evaluated, no trading outcomes inferred.**

## Executive findings

**The severe 000031.SZ weighted-model failure replicated on a distinct four-day subset of the original fitting data**, with no later-date lookups. On the common **10,218** historical stock/quote origins, the **weighted** three-feature logistic model classified directional outcomes more often and increased balanced accuracy relative to the always-stationary baseline, but sacrificed substantial accuracy and issued many false directional signals. The otherwise identical **unweighted** model mainly classified everything as stationary, recovering accuracy while missing almost all real up/down movements.

On 000031.SZ, class-weighted accuracy **9.53%**, stationary recall **0.00%**. Among 3,650 eligible matched origins, the weighted model predicted stationary only **1** time(s), and that prediction was incorrect. By contrast, unweighted 000031 accuracy rose to **86.58%**, while up recall was **0.00%** and down recall only **0.40%**.

**No causal explanation is proven**: class weighting clearly changes the prediction frequencies in the registered ablation, and feature distributions differ by stock, but the study does not isolate a definitive cause for global-model cross-security failure.

## Protocol, source integrity, and data protection

- [Frozen, pre-data-read D011 protocol](CLASS_WEIGHT_STOCK_SHIFT_PROTOCOL.md) specified exactly **two fixed models**, three existing features, matched-denominator comparisons, stock feature summaries and the first-10/last-4 chronological **original fitting-date** division. No parameter grid, coefficient selection, post-hoc thresholds or model promotion.
- Authenticated [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) by Quant Arena / LaPlace's Eye / Einsia AI. **CC BY-NC 4.0 (noncommercial)**. Stock names **000012.SZ, 000025.SZ, 000031.SZ**; source publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68` and original per-member publisher SHA256:
  - `000012.SZ.parquet` = `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`
  - `000025.SZ.parquet` = `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`
  - `000031.SZ.parquet` = `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`
- Canonical D009 source-date manifest SHA256: `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6`. **First 10 fitting dates 2022-01-11–2022-01-24; last four retrospective diagnostic dates 2022-01-25–2022-01-28.** All 14 dates were previously inside the D010 fit allocation; four-day diagnostic is **not a genuinely unseen external validation**.
- **Excluded from D011 model/label calculations:** D010 six confirmation dates Feb 7–14; D009 original five validation dates Feb 15–21; final sealed ten dates Feb 22–Mar 7. No future source quote converted to a feature, target or score. For SHA256 verification the complete three publisher stock members were downloaded (70,447,590 HTTP-range bytes total); an Arrow batch might physically decompress beyond January 28, so this is *statistical* model-use isolation rather than cryptographic byte secrecy.
- [Successful real-data GitHub Actions run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43234247334). Original quote/feature files were discarded after execution, not committed. **155 synthetic tests passed on Python 3.11 and 3.12**, including fail-closed first-14-day filtering, unapproved-date rejection, and matched-source-origin class metric checks.
- Periodic displayed book snapshots are **not** authentic order-submission, cancel, executed-aggressor order-flow, queue priority, latency, fill probability or executable trading P&L data. Unrelated original FI-2010 Helsinki 2010 reserved data remains unopened.

## Fixed dataset and fit-period class balance

- First ten fitting days: **30,642** quote origins, **27,215** eligible fixed k=5 future-midpoint labels; all **27,215** eligible have usable five-level depth features.
- Next four diagnostic days: **12,273** quote origins, **10,691** eligible fixed labels, **10,691** complete-depth eligible, and **10,218** also have valid B1 five-previous-quote input history.
- Target labels are unchanged: mean of next five contiguous valid same-stock/date/regular-continuous-auction-session midpoints vs current midpoint, ±0.2% decision thresholds, strict source validity and 30-second gap, no crossing the 11:30–13:00 midday recess. Source quote features only exist at or before origin availability.
- Training fit class support: **763 up / 25,747 stationary / 705 down**. A balanced fit gives relative source-row weights of approximately **11.89 up / 0.352 stationary / 12.87 down**; for equal raw sample lengths, the down-to-stationary weight ratio is approximately **36.5×**. These are train-objective weights, **not** probabilities, returns or causal proof.

## Same-origin four-way model comparison

**All models below are scored on the same 10,218 current-quote origins.** B0 is the first-ten-day global majority, B1 the fixed past-only previous-five trend. Both logistic models use exactly the same existing spread (clipped 100bps), top1 imbalance and top5 imbalance features; the same training-only StandardScaler, C=1, lbfgs solver, max400 iterations and random seed7007; their **only registered difference is class_weight balanced versus None**.

| Model | N | Accuracy | Macro-F1 | Balanced accuracy | Up recall | Stationary recall | Down recall | Up precision | Down precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 majority | 10,218 | 92.89% | 0.3211 | 0.3333 | 0.00% | 100.00% | 0.00% | undefined | undefined |
| B1 previous-five trend | 10,218 | 87.82% | 0.3634 | 0.3633 | 9.04% | 93.95% | 6.00% | 9.32% | 5.69% |
| W_BALANCED | 10,218 | 53.73% | 0.3245 | 0.5468 | 55.85% | 53.61% | 54.57% | 9.03% | 7.22% |
| W_UNWEIGHTED | 10,218 | 92.86% | 0.3229 | 0.3341 | 0.00% | 99.95% | 0.29% | undefined | 16.67% |

The weighted model predicted 4,970 directional labels, versus 6 for the unweighted model. Directional precision remained poor. The unweighted gain in accuracy is mostly a return to the dominant stationary prediction; it is **not improved detection of movements**. Pooled macro-F1 remains **0.3634 for B1**, versus **0.3245 weighted** and **0.3229 unweighted**.

### Per-stock matched prediction results

| Stock | N | B0 acc | B1 acc | Weighted acc | Unweighted acc | B1 macro-F1 | Weighted macro-F1 | Unweighted macro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 3,694 | 94.99% | 91.45% | 68.87% | 94.99% | 0.3810 | 0.3246 | 0.3248 |
| 000025.SZ | 2,874 | 98.09% | 96.31% | 90.40% | 98.09% | 0.3843 | 0.3310 | 0.3301 |
| 000031.SZ | 3,650 | 86.68% | 77.45% | 9.53% | 86.58% | 0.3374 | 0.1126 | 0.3120 |

### Why 000031.SZ was especially concerning

Weighted-model confusion on 000031.SZ during **only January 25–28**:

| True movement | Pred up | Pred stationary | Pred down |
| --- | ---: | ---: | ---: |
| Up | 173 | 0 | 66 |
| Stationary | 1454 | 0 | 1710 |
| Down | 71 | 1 | 175 |

Only **1** observation(s) were predicted as stationary in this stock, with **zero** correctly predicted stationary among 3,164 true-stationary origins. This is a close qualitative replication of D010's terrible performance on the *separate* February 7–14 internal confirmation, without reusing those previously examined February outcomes in the D011 diagnosis. It does **not** independently validate a causal explanation for that failure.

## Stock-level source feature distribution shifts

The following feature statistics are computed only for **label-eligible, fully source-valid five-level snapshot records** on the **ten fit dates**. Spread is in bps; imbalance is dimensionless in [-1,+1]. Quantiles are descriptive and source-date clustered; not IID confidence intervals.

| Stock | Feature | Eligible N | Mean | P10 | Median | P90 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | Spread bps clipped | 9,389 | 11.7750 | 10.5097 | 10.9230 | 11.3058 |
| 000012.SZ | Top-level imbalance | 9,389 | 0.1071 | -0.8069 | 0.1747 | 0.8770 |
| 000012.SZ | Five-level imbalance | 9,389 | 0.2372 | -0.5174 | 0.3641 | 0.7136 |
| 000025.SZ | Spread bps clipped | 8,491 | 8.2677 | 6.6203 | 6.7499 | 13.4409 |
| 000025.SZ | Top-level imbalance | 8,491 | 0.0598 | -0.7931 | 0.1000 | 0.8315 |
| 000025.SZ | Five-level imbalance | 8,491 | 0.1367 | -0.4256 | 0.1877 | 0.6723 |
| 000031.SZ | Spread bps clipped | 9,335 | 26.0767 | 25.0941 | 25.6739 | 26.0078 |
| 000031.SZ | Top-level imbalance | 9,335 | 0.0536 | -0.8151 | 0.0766 | 0.8704 |
| 000031.SZ | Five-level imbalance | 9,335 | -0.0486 | -0.4157 | -0.0546 | 0.3148 |

The spread distribution differs strongly by stock: mean **26.08bps on 000031.SZ**, versus **11.78bps** and **8.27bps** on the other securities. Five-level cumulative displayed-volume imbalance averages also differ. We **cannot** say on this evidence whether differences reflect ticks, liquidity, price level, market regime, normalization, or some confounder.

### Four retrospective diagnostic dates: aggregate feature checks

| Stock | Eligible N | Up | Stationary | Down | Mean spread (bps) | Mean top1 imbalance | Mean top5 imbalance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 3,744 | 116 | 3,551 | 77 | 13.269 | 0.109 | 0.141 |
| 000025.SZ | 3,227 | 29 | 3,164 | 34 | 8.642 | 0.121 | 0.243 |
| 000031.SZ | 3,720 | 248 | 3,214 | 258 | 28.059 | 0.010 | -0.006 |

Relative to the **ten-fitting-day global StandardScaler** mean/std, per-stock mean feature centers shifted as follows (spread, top1, top5 expressed in units of global training standard deviation):

| Stock | Fit-period standardized center | Diagnostic-period standardized center |
| --- | --- | --- |
| 000012.SZ | -0.44779, 0.05489, 0.32124 | -0.27227, 0.05867, 0.08274 |
| 000025.SZ | -0.85987, -0.02358, 0.07169 | -0.8159, 0.07755, 0.3361 |
| 000031.SZ | 1.23251, -0.03376, -0.38831 | 1.46545, -0.10656, -0.28238 |

We observe both **cross-stock differences and modest within-stock temporal changes**. These are *associations*, not proof of data leakage, overfitting, or true economic depth imbalance.

## Frozen model parameters and coefficient caveat

Training-fitted scaler mean: [15.5863504, 0.0740046, 0.107803]; scale: [8.5113329, 0.6038489, 0.402715], in original feature order (spread bps, level1 imbalance, level1–5 imbalance). Both models have **the same fitted feature scaling**, reflecting fit-only data.

| Model | Class weight | Optimizer iterations | Standardized intercepts, class 1/2/3 |
| --- | --- | --- | --- |
| W_BALANCED | balanced | 7 | -0.0636627, 0.2930613, -0.2293986 |
| W_UNWEIGHTED | none | 12 | -1.1881594, 2.6404088, -1.4522494 |

Coefficients, in fixed feature order per class (up / stationary / down) are archived as aggregate model parameters:

```json
{
  "W_BALANCED": {
    "classes": [
      1,
      2,
      3
    ],
    "standardized_feature_coefficients": [
      [
        0.1977203,
        0.4992454,
        -0.1822807
      ],
      [
        -0.4976613,
        0.0079816,
        0.2039958
      ],
      [
        0.2999411,
        -0.507227,
        -0.0217151
      ]
    ],
    "standardized_feature_intercepts": [
      -0.0636627,
      0.2930613,
      -0.2293986
    ]
  },
  "W_UNWEIGHTED": {
    "classes": [
      1,
      2,
      3
    ],
    "standardized_feature_coefficients": [
      [
        0.1450555,
        0.5360032,
        -0.1974241
      ],
      [
        -0.4052192,
        0.0371161,
        0.2082952
      ],
      [
        0.2601637,
        -0.5731193,
        -0.010871
      ]
    ],
    "standardized_feature_intercepts": [
      -1.1881594,
      2.6404088,
      -1.4522494
    ]
  }
}
```

**These coefficients are not causal feature contributions**, market-mechanism explanations, stable effect estimates or trading execution signals.

### By-stock/day registered diagnostic detail

| Stock/date | Matched N | Weighted accuracy | Unweighted accuracy | Weighted stationary prediction % | Weighted macro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ@2022-01-25 | 918 | 75.93% | 94.66% | 79.19% | 0.3292 |
| 000012.SZ@2022-01-26 | 918 | 58.39% | 95.75% | 58.39% | 0.2958 |
| 000012.SZ@2022-01-27 | 929 | 69.11% | 95.80% | 70.51% | 0.3168 |
| 000012.SZ@2022-01-28 | 929 | 72.01% | 93.76% | 73.74% | 0.3545 |
| 000025.SZ@2022-01-25 | 718 | 85.79% | 96.10% | 88.86% | 0.3331 |
| 000025.SZ@2022-01-26 | 691 | 92.04% | 99.13% | 92.91% | 0.3195 |
| 000025.SZ@2022-01-27 | 700 | 91.71% | 97.71% | 94.00% | 0.3189 |
| 000025.SZ@2022-01-28 | 765 | 92.03% | 99.35% | 92.29% | 0.3356 |
| 000031.SZ@2022-01-25 | 918 | 8.61% | 89.11% | 0.11% | 0.1047 |
| 000031.SZ@2022-01-26 | 896 | 9.49% | 85.94% | 0.00% | 0.1115 |
| 000031.SZ@2022-01-27 | 907 | 10.03% | 85.23% | 0.00% | 0.1169 |
| 000031.SZ@2022-01-28 | 929 | 10.01% | 86.01% | 0.00% | 0.1278 |

## Outcome, limitations, next research gate

**Supported:** Changing only inverse-frequency class weighting radically changes how often the model calls up/down; when removed, the unweighted model mostly predicts stationary. The weighted cross-stock failure repeats on 000031.SZ even on an earlier internal fitting-date subset. Current spread/volume imbalance distributions differ by security and are plausibly associated with a pooled standardized model's failure.

**Not established:** That changing weights fixes economically relevant predictions, that any weight setting is a viable production model, that the stock-feature difference *causes* failure, that a source tick constraint/volatility regime fully explains the observations, that the effects generalize to untouched dates or markets, or that execution is profitable. Already-fit-date comparisons are **diagnostics, not validation-grade generalization claims**.

**Next case, not executed:** Define a *source-blind* first-ten-fit-only model-calibration and leave-one-stock-out analysis to disentangle possible volume/spread distribution effects, if useful. No repeated adjustments based on the just-inspected four diagnostic days, D010 six February confirmation days, original five February validation days, or the sealed final ten-day test. Maintain unchanged draft PR #7 and no broker/trading activity.

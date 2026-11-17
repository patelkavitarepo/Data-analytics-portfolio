# Project 007 — D009: first chronological prediction baseline study

**Status:** Completed training-only B0 and deterministic backward-only B1 against **validation**; final 10-date test remains **sealed**. November 11, 2026 (America/New_York). **Research scope:** historical, descriptive classification evaluation; NOT an investment/market-making strategy, executable alpha, or original FI-2010 Helsinki-label replication. The human lead approved "Let's get it Holmes" after D008; the methods, implementation and interpretation are AI-assisted.

## Pre-price freeze and source provenance

- Precommitted [CHRONOLOGICAL_PREDICTION_PROTOCOL.md](CHRONOLOGICAL_PREDICTION_PROTOCOL.md) specified the two baselines, source-clock rules, metrics, tie behavior, exclusion rules and holdout policy **before reading any new training/validation prices**.
- The preceding [metadata-only date run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43143127390) validated the common source calendar and produced [CHRONOLOGICAL_SPLIT_MANIFEST.json](CHRONOLOGICAL_SPLIT_MANIFEST.json), committed to Git **before baseline market-price evaluation**. Date-list SHA256: `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6`.
- Source: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0 noncommercial only with attribution**. Independent Shenzhen market 2022 source, not FI-2010 Helsinki 2010.
- Pinned publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`; exact stock members: `000012.SZ`, `000025.SZ`, `000031.SZ`. The three source-file SHA256 values match previously published source `SHA256SUMS` receipts. Each member was downloaded in bounded authenticated HTTP 206 byte ranges (~70.45 MB total) instead of downloading the full ~6.23GB TAR. Raw quote rows, vendor files and stock-level price sequences were **not committed**.
- **Previously examined discovery:** Jan 4/5/6/7/10, 2022, NOT holdout. **Training:** `2022-01-11` through `2022-02-14` (20 common source trading dates). **Validation:** `2022-02-15` through `2022-02-21` (5 dates). **Sealed final test:** `2022-02-22` through `2022-03-07` (10 dates).
- The final test has **not been scored, fitted, inspected for label prevalence, or used to select rules**. Technical caveat: whole stock Parquet member bytes were fetched for checksum verification, and the Parquet batch intersecting the validation boundary may have physically decompressed some later rows; all rows outside the frozen 20+5 permitted dates were discarded and **no final test values entered training/feature/target/scoring computations**. This is statistical test isolation, not byte-level secrecy.
- [Verified real training/validation GitHub Actions](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43143730597) and **135 synthetic tests passing on Python 3.11 and 3.12**. One-time source download CI to be disabled after documenting results.

## Registered population, predictors and outcome

- Operational source continuous-auction windows: **09:30–11:30 morning** and **13:00–14:57 (exclusive) afternoon**, source exchange local +08:00. The **14:57–15:00 closing call auction** is excluded in this new prediction population. This modification does **not** rewrite any previous D008 source label reports.
- Price/quote eligibility: positive, uncrossed top bid/ask; source `stale=False` and `missing_depth=False`; source-event time never after availability. Every feature is based only on current or earlier published quotes; no segment crosses a stock/date/session boundary, invalid quote or >30-second adjacent timestamp gap.
- **Target**: classify (arithmetic mean of next five valid midpoint snapshots − current midpoint) / current midpoint at ±0.2% as 1 up / 2 stationary / 3 down. Incomplete future targets excluded.
- **B0**: globally most frequent *training* class, ties preferentially 2 > 1 > 3; chosen class: **2 (stationary)**. Training label support: **1778 up / 50583 stationary / 1702 down**, 54,063 eligible of 61,329 source origins.
- **B1**: *unfitted* fixed backward-only rule from current midpoint relative to mean previous **five contiguous valid** source midpoints at fixed ±0.2%. B1 abstains without a complete valid five-quote history. It does not use target eligibility or any future label as a feature.
- Frozen metrics: accuracy, **three-class macro-F1** and **three-class balanced accuracy**; absent classes contribute 0 recall in fixed class summary. Heavy stationary dominance makes accuracy alone a poor diagnostic.

## Validation denominators and exclusions

| Population / status | Count |
| --- | ---: |
| Validation source quote origins | 15,345 |
| Eligible future-label origins | 13,315 |
| Out-of-continuous-auction origins | 1,110 |
| Invalid/stale origin quotes | 161 |
| Incomplete future windows | 759 |
| B1-covered eligible origins | **12,718 (95.52% of eligible)** |
| B1 abstentions among eligible | 597 |

## Fair same-origin baseline comparison (B1-covered subset only)

| Predictor | N | Accuracy | Macro-F1 | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| B0, majority on same covered rows | 12,718 | 94.15% | 0.3233 | 0.3333 |
| B1, past-only mean-trend | 12,718 | 89.83% | 0.3573 | 0.3571 |

**Additional unmatched coverage context:** On **all 13,315 eligible validation origins**, B0 predicts all and achieves accuracy **94.14%**, macro-F1 **0.3233**, balanced accuracy **0.3333**. Do **not** compare this full-coverage B0 score directly against B1's smaller subset as evidence of B1 superiority.

**Pooled descriptive tradeoff:** On identical covered rows, B1 gains **0.0340** absolute macro-F1 and **0.0238** balanced accuracy but **loses 4.32 percentage points of accuracy**. This is modest and cannot be interpreted as economic alpha or statistical significance.

### Minority classes: key caution

True support on the B1-covered sample: up **412**, stationary **11974**, down **332**. B1 recall: **6.07% up**, **95.04% stationary**, **6.02% down**. Thus minority-direction detection remains **very weak** despite pooled macro metric improvements.

B1 confusion matrix (true classes as rows, predictions as columns):

| True class | Pred up (1) | Pred stationary (2) | Pred down (3) |
| --- | ---: | ---: | ---: |
| Up (1) | 25 | 351 | 36 |
| Stationary (2) | 344 | 11380 | 250 |
| Down (3) | 74 | 238 | 20 |

### Per-stock matched-coverage comparison

| Stock | Eligible targets | B1-covered | B0 accuracy | B1 accuracy | B0 macro-F1 | B1 macro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 4,695 | 4,645 | 96.49% | 93.69% | 0.3274 | 0.3742 |
| 000025.SZ | 3,947 | 3,465 | 98.79% | 97.66% | 0.3313 | 0.3296 |
| 000031.SZ | 4,673 | 4,608 | 88.30% | 80.06% | 0.3126 | 0.3385 |

The pooled B1 macro-F1 improvement is **not consistent across securities**: 000025.SZ is slightly worse than B0 on both macro-F1 and balanced accuracy. The three stocks also differ substantially in label class prevalence, so pooled results alone hide meaningful heterogeneity.

### By-stock/date validation detail (descriptive, no IID inference)

| Stock/date | Eligible | B1-covered | B0 macro-F1, covered | B1 macro-F1, covered |
| --- | ---: | ---: | ---: | ---: |
| 000012.SZ@2022-02-15 | 939 | 929 | 0.3269 | 0.3353 |
| 000012.SZ@2022-02-16 | 939 | 929 | 0.3241 | 0.3838 |
| 000012.SZ@2022-02-17 | 939 | 929 | 0.3252 | 0.4077 |
| 000012.SZ@2022-02-18 | 939 | 929 | 0.3297 | 0.3264 |
| 000012.SZ@2022-02-21 | 939 | 929 | 0.3308 | 0.3286 |
| 000025.SZ@2022-02-15 | 832 | 747 | 0.3315 | 0.3293 |
| 000025.SZ@2022-02-16 | 789 | 707 | 0.3333 | 0.3329 |
| 000025.SZ@2022-02-17 | 719 | 587 | 0.3322 | 0.3310 |
| 000025.SZ@2022-02-18 | 727 | 593 | 0.3325 | 0.3314 |
| 000025.SZ@2022-02-21 | 880 | 831 | 0.3278 | 0.3247 |
| 000031.SZ@2022-02-15 | 933 | 918 | 0.3141 | 0.3417 |
| 000031.SZ@2022-02-16 | 933 | 918 | 0.3211 | 0.3399 |
| 000031.SZ@2022-02-17 | 935 | 925 | 0.3155 | 0.3201 |
| 000031.SZ@2022-02-18 | 933 | 918 | 0.3084 | 0.3221 |
| 000031.SZ@2022-02-21 | 939 | 929 | 0.3036 | 0.3428 |

## Scientific interpretation and next decision gate

**Supported:** A fixed backward-looking midpoint heuristic can very slightly improve pooled macro-F1 and balanced accuracy over a constant-majority predictor, but most up/down observations remain unrecognized. The tradeoff costs total accuracy and is not uniformly replicated across stocks. This is an **out-of-date-block validation result**, distinct from an untouched final test.

**Not supported:** That the trend signal is reliably predictive across markets, profitable, executable, significant under serial dependence, or transferable to FI-2010. The targets overlap (next-five snapshots); stock/date outcomes cluster, so naïve IID p-values, row-level bootstrap standard errors or causal explanations are inappropriate.

**Next gate, not yet executed:** Human review of whether these simple baselines warrant refining a **training-only** book-feature hypothesis (spread, imbalance, order flow), with explicit controls for validation re-use and class imbalance. The **ten final dates remain sealed** and must not be scored to tune or rescue a model. No paid market data, brokerage account, live trade, deploy, feature-model fit, holdout evaluation or merge has occurred.

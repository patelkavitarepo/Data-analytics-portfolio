# Project 007 — D012 prospective selective directional-alert study

**Source-verified November 12, 2026. Status: registered prospective fit + label-BLIND score calibration + one-time confirmation completed; both final tests protected.** Human continuation: "let’s get that bread". Model decisions, design, calculations and interpretations are AI-assisted. **No model promoted, no trading, no executable alpha or P&L claimed.**

## Executive finding: the alert filter failed to deliver usable precision

Two fixed 3-class book-liquidity logistic regressions, trained with **class weighting balanced versus no weights**, were given identical **2% per-stock score-calibration budget** without inspecting calibration future-target labels. On the later April 21–27 confirmation, both issued substantially more directional alerts than the calibration budget might suggest and **approximately 84% of issued directional alerts were incorrect**.

On the **same 13,819 confirmation origins**, with source-valid current five-level depth, five prior contiguous quote observations and verified future k=5 price-movement labels:

| Frozen model | Alerts | Correct | False | Directional precision | Alerts / 1,000 | False / 1,000 | Up recall | Down recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Balanced logistic (W) | 919 | 150 | 769 | 16.32% | 66.50 | 55.65 | 5.14% | 5.57% |
| Unweighted logistic (U) | 882 | 144 | 738 | 16.33% | 63.83 | 53.40 | 5.44% | 4.89% |

**W_BALANCED:** alert rate 6.65% of confirmation observations, against the intended **2% per-stock calibration-score cutoff**. **W_UNWEIGHTED:** 6.38%. A calibration alert fraction is **not a guaranteed later-period cap**; this descriptive drift is an important negative result. It does not by itself establish which market feature or external mechanism changed.

The two models have nearly identical confirmation directional precision (**16.32% vs 16.33%**), despite significantly different class-weight training objectives. Using a very conservative alert filter did **not** solve the false-positive problem or recover meaningful directional recall.

**Descriptive references on the identical sample:** B0 fit-majority accuracy **79.77%**, three-class macro-F1 **0.2958**; B1 fixed past-five trend accuracy **69.01%**, macro-F1 **0.3668**. Alert "no signal" is abstention and should not be compared directly to a stationary classification without explicit proxy assumptions.

## Strict preregistration / immutable data lineage

- [D012 frozen protocol](SELECTIVE_ALERTS_PROTOCOL.md) was committed **before** the first source read of newly selected price/depth columns. Immutable source: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0 noncommercial with attribution**, pinned publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`. Exact original three stock member SHA256s reverified from publisher `SHA256SUMS`:
  - `000012.SZ.parquet`: `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`
  - `000025.SZ.parquet`: `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`
  - `000031.SZ.parquet`: `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`
- Separate [metadata-only date selection run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43237166900) froze [new chronological date manifest](FRESH_SELECTIVE_DATE_MANIFEST.json) **before** model-price reads. Date-list SHA256: `fe19d601c74f3276e13d8fda3e03ebebcc548bcdb1a2b748138c2d7040d7f3da`. Source calendar contained **484** common observed dates across three stocks, with 444 after March 7.
- New fit **2022-03-08–2022-04-06**, 20 dates; unlabelled calibration **2022-04-07–2022-04-20**, 10 dates; one-time confirmation **2022-04-21–2022-04-27**, 5 dates; **new sealed final** `2022-04-28` through `2022-05-16`, 10 dates.
- Original D009 February 22–March 7 future block remains **unscored**, but it precedes this later March–April model fit and therefore **cannot** serve as this model's prospective final test. It was never treated as such. **The new later April 28–May 16 sealed block also remains unscored.**
- [Successful source-verified GitHub Actions](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43237929585), the first and only *registered scored* confirmation. **168 synthetic unit tests passed** on both Python 3.11 and 3.12. The special source-reading CI job was removed after success, leaving synthetic-only routine CI.
- **70,447,590 bytes** bounded HTTP 206 stock-member data for checksum verification, rather than the complete ~6.23GB source archive. The entire individual selected Parquets are downloaded for hash checking, and the Arrow batch at the date cutoff may physically decompress final-date rows, but **no original legacy or new sealed final date rows were admitted into features, future-target labels, model training or scoring**. This is *statistical* isolation, not byte-level secrecy. No raw vendor prices, quote snapshots, individual predictions or stock-level sequences were committed.

## Model, target, coverage, and no-peeking rules

- Target: existing **k=5 next-valid-snapshot arithmetic midpoint mean** relative to current midpoint, ±0.2% threshold, class 1 up, 2 stationary, 3 down. Source flags, stock, day, 09:30–11:30 morning / 13:00–14:57 afternoon windows and max30-second continuous quote segments restrict labels. Closing auction excluded.
- Model inputs: **current best spread bps, displayed best-level bid-vs-ask volume imbalance, displayed first-five-level volume imbalance**, all from complete, valid five-level snapshot; source event timestamp no later than quote availability. No actual order message stream, execution fill or trade aggressor flags exist here.
- Two fixed training-only `StandardScaler + LogisticRegression(C=1, lbfgs, max_iter=400, seed=7007)`, differing **only** in class_weight balanced versus none; no trained time-varying features, per-stock models, grid search, or selected probability threshold.
- Fit-only **54,290** complete-book label-eligible examples, training majority class **2**; target counts: up **3,930**, stationary **46,768**, down **3,639**.
- Calibration 10-date quote input **never passed through future label construction** and did not require true classes. Eligible calibration features must have **five previous contiguous valid same-stock/day/session quotes**.
- For each stock and model, cutoff: **98th percentile (higher interpolation) of its calibration score** `max(p_up,p_down)/(p_stationary+1e-12)`, alert only when current score **strictly exceeds** that cutoff. `predict_proba` values are model scores, **not empirically calibrated probabilities**. Ties can produce fewer than 2% alerts in calibration. The cutoff was fixed prior to confirmation scoring.
- On confirmation, no-alert is **abstention**, not a predicted stationary label. Alerts are up/down, evaluated only where a verifiable target exists; same-source-window B0/B1 outcomes and proxy metrics are separately labeled as such.

### Label-free stock calibration evidence

| Frozen model | Stock | Calibration eligible *current/past* rows | Score cutoff (higher p98) |
| --- | --- | ---: | ---: |
| W_BALANCED | 000012.SZ | 9,390 | 1.88134016 |
| W_BALANCED | 000025.SZ | 8,977 | 1.71470105 |
| W_BALANCED | 000031.SZ | 9,389 | 4.44242021 |
| W_UNWEIGHTED | 000012.SZ | 9,390 | 0.14798194 |
| W_UNWEIGHTED | 000025.SZ | 8,977 | 0.13696671 |
| W_UNWEIGHTED | 000031.SZ | 9,389 | 0.31666292 |

Every `calibration_target_labels_calculated` flag in the original runner receipt is **false**. The source-run audit explicitly asserts both old/new reserved test blocks stayed unscored.

## Per-stock confirmation breakdown

| Stock | Model | Matched N | Alerts | Correct | False | Precision | False alerts / 1,000 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | Balanced logistic (W) | 4,645 | 422 | 62 | 360 | 14.69% | 77.50 |
| 000012.SZ | Unweighted logistic (U) | 4,645 | 412 | 60 | 352 | 14.56% | 75.78 |
| 000025.SZ | Balanced logistic (W) | 4,529 | 265 | 43 | 222 | 16.23% | 49.02 |
| 000025.SZ | Unweighted logistic (U) | 4,529 | 245 | 42 | 203 | 17.14% | 44.82 |
| 000031.SZ | Balanced logistic (W) | 4,645 | 232 | 45 | 187 | 19.40% | 40.26 |
| 000031.SZ | Unweighted logistic (U) | 4,645 | 225 | 42 | 183 | 18.67% | 39.40 |

A per-stock cutoff controls calibration scores rather than future alert frequency. Stock-specific confirmation alert rates differed materially: under the balanced model, 000012.SZ had **90.85 alerts per 1,000**, 000025.SZ **58.51**, and 000031.SZ **49.95**. No stock met a reliability criterion for trading, and stock heterogeneity remains a research limitation.

### Per-stock/date descriptive alerts (not IID significance)

| Stock/date | Model | Matched N | Alerts | False | Precision |
| --- | --- | ---: | ---: | ---: | ---: |
| 000012.SZ@2022-04-21 | Balanced logistic (W) | 929 | 66 | 62 | 6.06% |
| 000012.SZ@2022-04-21 | Unweighted logistic (U) | 929 | 62 | 58 | 6.45% |
| 000012.SZ@2022-04-22 | Balanced logistic (W) | 929 | 53 | 51 | 3.77% |
| 000012.SZ@2022-04-22 | Unweighted logistic (U) | 929 | 49 | 47 | 4.08% |
| 000012.SZ@2022-04-25 | Balanced logistic (W) | 929 | 57 | 52 | 8.77% |
| 000012.SZ@2022-04-25 | Unweighted logistic (U) | 929 | 56 | 51 | 8.93% |
| 000012.SZ@2022-04-26 | Balanced logistic (W) | 929 | 63 | 49 | 22.22% |
| 000012.SZ@2022-04-26 | Unweighted logistic (U) | 929 | 62 | 49 | 20.97% |
| 000012.SZ@2022-04-27 | Balanced logistic (W) | 929 | 183 | 146 | 20.22% |
| 000012.SZ@2022-04-27 | Unweighted logistic (U) | 929 | 183 | 147 | 19.67% |
| 000025.SZ@2022-04-21 | Balanced logistic (W) | 918 | 24 | 18 | 25.00% |
| 000025.SZ@2022-04-21 | Unweighted logistic (U) | 918 | 23 | 17 | 26.09% |
| 000025.SZ@2022-04-22 | Balanced logistic (W) | 873 | 39 | 34 | 12.82% |
| 000025.SZ@2022-04-22 | Unweighted logistic (U) | 873 | 32 | 28 | 12.50% |
| 000025.SZ@2022-04-25 | Balanced logistic (W) | 907 | 45 | 35 | 22.22% |
| 000025.SZ@2022-04-25 | Unweighted logistic (U) | 907 | 43 | 32 | 25.58% |
| 000025.SZ@2022-04-26 | Balanced logistic (W) | 902 | 76 | 68 | 10.53% |
| 000025.SZ@2022-04-26 | Unweighted logistic (U) | 902 | 72 | 64 | 11.11% |
| 000025.SZ@2022-04-27 | Balanced logistic (W) | 929 | 81 | 67 | 17.28% |
| 000025.SZ@2022-04-27 | Unweighted logistic (U) | 929 | 75 | 62 | 17.33% |
| 000031.SZ@2022-04-21 | Balanced logistic (W) | 929 | 28 | 23 | 17.86% |
| 000031.SZ@2022-04-21 | Unweighted logistic (U) | 929 | 28 | 23 | 17.86% |
| 000031.SZ@2022-04-22 | Balanced logistic (W) | 929 | 46 | 36 | 21.74% |
| 000031.SZ@2022-04-22 | Unweighted logistic (U) | 929 | 42 | 33 | 21.43% |
| 000031.SZ@2022-04-25 | Balanced logistic (W) | 929 | 42 | 38 | 9.52% |
| 000031.SZ@2022-04-25 | Unweighted logistic (U) | 929 | 39 | 35 | 10.26% |
| 000031.SZ@2022-04-26 | Balanced logistic (W) | 929 | 53 | 41 | 22.64% |
| 000031.SZ@2022-04-26 | Unweighted logistic (U) | 929 | 53 | 42 | 20.75% |
| 000031.SZ@2022-04-27 | Balanced logistic (W) | 929 | 63 | 49 | 22.22% |
| 000031.SZ@2022-04-27 | Unweighted logistic (U) | 929 | 63 | 50 | 20.63% |

## Fixed-class diagnostic proxy confusion (do not confuse abstention with stationary)

### Balanced logistic (W) — three-class diagnostic proxy only

No-alert is **abstention**, not evidence of unchanged prices. The following table artificially maps no-alert to the stationary class **for comparison only**, not as an actual stationary forecast.

| Actual class | Alert up | No-alert (mapped to stationary) | Alert down |
| --- | ---: | ---: | ---: |
| Up | 68 | 1208 | 48 |
| Stationary | 345 | 10352 | 326 |
| Down | 50 | 1340 | 82 |

Proxy macro-F1 0.3422, balanced accuracy 0.3487, accuracy 76.00%.

### Unweighted logistic (U) — three-class diagnostic proxy only

No-alert is **abstention**, not evidence of unchanged prices. The following table artificially maps no-alert to the stationary class **for comparison only**, not as an actual stationary forecast.

| Actual class | Alert up | No-alert (mapped to stationary) | Alert down |
| --- | ---: | ---: | ---: |
| Up | 72 | 1210 | 42 |
| Stationary | 373 | 10384 | 266 |
| Down | 57 | 1343 | 72 |

Proxy macro-F1 0.3411, balanced accuracy 0.3484, accuracy 76.18%.

## Interpretation and scientific stop conditions

**What is supported:** A score-threshold filter can dramatically restrict the number of raw model directional calls, but the independently frozen 2%-calibration-cutoff design **did not maintain 2% alerting in a later five-date source period**. Neither class-weight configuration produced acceptable precision or directional recall in this example. On identical observations, weighted and unweighted model alert precision were virtually indistinguishable; both yielded many false alarms. This is evidence that controlling historical alert frequency does **not** establish a stable directional warning system.

**What is not established:** Stable statistical calibration across dates, useful out-of-sample price forecasting, economically meaningful directional prediction, causality of score drift, viable real-world entry/exit timing, fill/queue likelihood, brokerage costs, risk-adjusted profitability or modern live execution edge. These source snapshots are sampled and clustered, and labels overlap. No naive IID confidence intervals/p-values are inferred.

**Next gate (not executed):** Require materially higher per-stock precision with substantially fewer false signals **on genuinely later, preregistered data**, and assess quote-latency, execution feasibility, fees and slippage separately before any financial interpretations. Do not tune this score cutoff against the five D012 confirmation days. **The new final ten days remain sealed and must not be opened to rescue the experiment.** Project 007 PR #7 remains draft and unmerged; neither model has been selected or deployed.

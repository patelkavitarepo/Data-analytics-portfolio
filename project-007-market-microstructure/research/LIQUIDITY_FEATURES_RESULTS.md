# Project 007 — D010: first snapshot-liquidity model on TRAINING-ONLY dates

**Verified November 12, 2026. Status: first registered, source-authenticated internal-training comparison completed; no model promoted or heldout test accessed.** AI-assisted analysis in response to the human lead's directive: "Alright Holmes lets keep it moving." This is historical noncommercial classification research, **not** a trading strategy, financial return forecast, executable fill model, or original FI-2010 Helsinki dataset reproduction.

## The central finding

A fixed three-feature class-balanced logistic regression (**B2**) substantially improved *pooled balanced accuracy and directional recall* relative to B0/B1, but produced many false directional predictions and **performed catastrophically on one of the three stocks**. It is **NOT a robust classifier**, was not selected for promotion and must not be described as a promising trading signal without significant separate evidence.

On the exact **15,524 identical quote origins** for which B0, B1 and B2 all have usable features and valid targets:

| Metric | B0 majority | B1 backward trend | B2 snapshot liquidity |
| --- | ---: | ---: | ---: |
| Accuracy | 92.31% | 86.85% | 58.05% |
| Fixed three-class macro-F1 | 0.3200 | 0.3725 | 0.3405 |
| Three-class balanced accuracy | 0.3333 | 0.3730 | 0.5199 |
| Recall: up (class 1) | 0.00% | 7.58% | 45.62% |
| Recall: stationary (class 2) | 100.00% | 93.31% | 58.83% |
| Recall: down (class 3) | 0.00% | 11.00% | 51.50% |

Pooled B2 balanced accuracy 0.5199 exceeds B1 0.3730, but B2 macro-F1 0.3405 is **worse** than B1 0.3725 and B2 accuracy drops to 58.05%. B2 directional positive-prediction precision is only **8.51% for up** and **8.66% for down**: most directional alerts in this sample are false positives.

The B2 fixed three-class confusion matrix (true classes by row, predictions by column) makes the failure concrete:

| True class | Predicted up | Predicted stationary | Predicted down |
| --- | ---: | ---: | ---: |
| Up | 271 | 165 | 158 |
| Stationary | 2798 | 8431 | 3101 |
| Down | 115 | 176 | 309 |

In particular, B2 incorrectly predicted 5,899 of 14,330 true-stationary rows as directional movements.

## Source, license, and preregistration chain

- [Noncommercial Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) (Quant Arena / LaPlace's Eye / Einsia AI, hosted as Ashitemaru), **CC BY-NC 4.0**. These are Shenzhen **snapshot** quotes, *not event-by-event order messages*, not 2010 Helsinki FI-2010 publisher labels.
- Registered source revision: `fa85d7b95e56e81317ac349f52e916ca482f0f68`. Publisher `SHA256SUMS` verified all three exact members:
  - `000012.SZ.parquet`: `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`.
  - `000025.SZ.parquet`: `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`.
  - `000031.SZ.parquet`: `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`.
- [D009 canonical source-date manifest](CHRONOLOGICAL_SPLIT_MANIFEST.json) unchanged; date-list SHA256 `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6`. Entire source-member bytes fetched only to verify publisher SHA256 via bounded HTTP 206 TAR ranges (70,447,590 bytes total), not whole 6.23GB archive. Original raw snapshots, stock price sequences, model prediction rows and vendor Parquet files **were not committed or redistributed**.
- [D010 fixed experiment protocol](LIQUIDITY_FEATURES_PROTOCOL.md) was committed **before** this source run. No grid search, selection after seeing scores, retuning or post-hoc threshold optimization occurred.
- **D010 fitting dates:** 2022-01-11 to 2022-01-28 (14 source trading dates; last day prior to the holiday break). **One internal confirmation:** 2022-02-07 to 2022-02-14 (6 trading dates). These are the *same 20 training dates allocated by D009*, not a new independent external test set. Previously D009 examined pooled class counts of all 20 dates, so even this internal split should not be advertised as completely virgin/untouched research data.
- **The original D009 five-date validation (February 15–21) and sealed final ten-date test (February 22–March 7, 2022) were NOT used for D010 source-feature, target, parameter selection, or prediction scoring.** The full Parquet member bytes were downloaded for SHA256; a row batch could physically decompress bytes over a later-date boundary, but **no later rows were converted to a feature, label or score**. This is statistical holdout isolation, not byte-level encryption or proof of no read.
- [Verified successful source-run evidence](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43230081435); **150 synthetic tests passed on both Python 3.11 and 3.12** in routine GitHub CI; the empirical runner used pinned Python 3.12, pyarrow==19.0.1 and scikit-learn==1.6.1. Real source member hashes and date counts verified before model fitting. No code or data in FI-2010 reserved days was opened.

## Fixed model definition and leakage guards

All observations retain the source `available_at` timestamp and may use only current/prior snapshots. The **target is unchanged**: future arithmetic mean of five consecutive, valid quote midpoints compared to the current midpoint at ±0.002, with classes 1 up, 2 stationary, 3 down. Cross-security/date/morning-afternoon labels, gaps >30 seconds, stale/missing book data, and incomplete futures are excluded. Source continuous-auction phases **09:30–11:30** and **13:00–14:57 (exclusive)** in exchange-local +08; closing auction excluded.

B0 is selected by the **first 14 fitting days' majority** across three stocks (tie priority 2/1/3). Class selected: **2 stationary**. Training eligible support: up **1,156**, stationary **35,676**, down **1,074**, 37,906 eligible of 42,915 source quote origins.

B1 is the previously frozen *unfitted* previous-five valid midpoint trend, abstaining if history is unavailable. No fitting or future/current-day aggregate leakage.

B2 uses precisely the *current* snapshot's **(i) clipped best bid/ask spread in bps, (ii) displayed level-one bid-vs-ask volume imbalance, and (iii) displayed first-five-level volume imbalance**. Positive, ordered/uncrossed price ladders and genuine nonnegative integer volumes are required for all five levels on both sides; stale and missing-depth source flags must be false; `source_event_time <= available_at`. A `StandardScaler` and one three-class `LogisticRegression(C=1,class_weight='balanced',solver='lbfgs',max_iter=400,random_state=7007,multinomial)` were fit on fitting dates only. It converged in **7** iterations. No features are inferred from future snapshots, and no imputation or class-threshold tuning was performed.

The source provides **periodic depth snapshots**, not the event stream needed to reconstruct authentic order submissions, removals, aggressor-initiated trade flow, order priority or queue fills. No such claims are made.

## Source denominators, feature coverage and class prevalence

| Source group | Number |
| --- | ---: |
| First 14-date fit period — all quote origins | 42,915 |
| Fit-period future-label eligible | 37,906 |
| Fit-period eligible with full 5-level B2 depth | **37,906** |
| Six-date internal confirmation — all quote origins | 18,414 |
| Confirmation future-label eligible | 16,157 |
| Confirmation eligible with full five-level B2 depth | 16,157 |
| Confirmation eligible with B1 previous-five-quote history | 15,524 |
| **Fair, matched B0/B1/B2 comparison** | **15,524** |

B2's five-level depth requirements did **not** reduce coverage further among future-label eligible observations in this particular historical source; all 16,157 target-eligible confirmation origins also had source-valid five-level depth. However B1's lagged history requirement reduces the fully matched population to 15,524. **Do not compare unmatched coverage metrics as if they used equal denominators.**

Original source exclusion reasons during internal confirmation: incomplete_future: **769**; invalid_or_stale_quote: **156**; outside_continuous_auction: **1,332**. These totals reconcile to source observations and are not stationary labels.

### Per-stock source-row and eligibility counts

| Stock | 14-fit source rows | Fit eligible targets | 6-confirmation source rows | Confirmation eligible | Full-depth confirmation eligible |
| --- | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 14,305 | 13,133 | 6,138 | 5,634 | 5,634 |
| 000025.SZ | 14,305 | 11,718 | 6,138 | 4,895 | 4,895 |
| 000031.SZ | 14,305 | 13,055 | 6,138 | 5,628 | 5,628 |

## Cross-stock stress test (matched same-origin population)

| Stock | Matched N | B0 accuracy | B1 accuracy | B2 accuracy | B0 macro-F1 | B1 macro-F1 | B2 macro-F1 | B2 balanced accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 5,574 | 93.04% | 87.66% | 80.73% | 0.3213 | 0.3732 | 0.3478 | 0.3604 |
| 000025.SZ | 4,387 | 99.13% | 98.04% | 90.65% | 0.3319 | 0.3301 | 0.3251 | 0.3634 |
| 000031.SZ | 5,563 | 86.19% | 77.22% | 9.60% | 0.3086 | 0.3584 | 0.1124 | 0.4632 |

**Critical failure:** On 000031.SZ, B2 accuracy was 9.60% and macro-F1 0.1124. It predicted *zero* of the 4,795 true-stationary observations as stationary; the model predicted directional classes for all of them. Although its directional recall is comparatively high there, those directional calls have a devastating false-positive cost. Other stocks also failed to outperform B1 macro-F1 consistently. **Do not promote B2 or claim that its higher pooled balanced accuracy establishes reliable directional forecasting.**

### Per-security/date internal confirmation metrics (not independent tests)

| Symbol/date | Same-origin N | B1 macro-F1 | B2 macro-F1 | B2 balanced accuracy |
| --- | ---: | ---: | ---: | ---: |
| 000012.SZ@2022-02-07 | 929 | 0.3316 | 0.3938 | 0.3911 |
| 000012.SZ@2022-02-08 | 929 | 0.3292 | 0.3346 | 0.4108 |
| 000012.SZ@2022-02-09 | 929 | 0.3734 | 0.3037 | 0.4489 |
| 000012.SZ@2022-02-10 | 929 | 0.3878 | 0.3325 | 0.3303 |
| 000012.SZ@2022-02-11 | 929 | 0.3748 | 0.3286 | 0.3316 |
| 000012.SZ@2022-02-14 | 929 | 0.3375 | 0.3494 | 0.3484 |
| 000025.SZ@2022-02-07 | 657 | 0.3300 | 0.3471 | 0.3668 |
| 000025.SZ@2022-02-08 | 743 | 0.3324 | 0.3176 | 0.3041 |
| 000025.SZ@2022-02-09 | 871 | 0.3314 | 0.3225 | 0.3137 |
| 000025.SZ@2022-02-10 | 669 | 0.3323 | 0.3280 | 0.3229 |
| 000025.SZ@2022-02-11 | 675 | 0.3265 | 0.3120 | 0.3326 |
| 000025.SZ@2022-02-14 | 772 | 0.3278 | 0.3197 | 0.3733 |
| 000031.SZ@2022-02-07 | 929 | 0.3721 | 0.1323 | 0.4381 |
| 000031.SZ@2022-02-08 | 929 | 0.3483 | 0.1489 | 0.4975 |
| 000031.SZ@2022-02-09 | 918 | 0.3109 | 0.1124 | 0.4698 |
| 000031.SZ@2022-02-10 | 929 | 0.3757 | 0.0787 | 0.4578 |
| 000031.SZ@2022-02-11 | 929 | 0.3824 | 0.1043 | 0.4286 |
| 000031.SZ@2022-02-14 | 929 | 0.3328 | 0.1198 | 0.5112 |

## Interpretation and next gate

**Supported:**
1. A fixed training-only classifier using displayed spread/depth features can detect more future directional labels *in this small confirmation period* than an always-stationary or backward-trend heuristic, but with many false alarms.
2. Pooled balanced accuracy alone can conceal a practically catastrophic per-security regime, especially under training inverse-class weighting and strong stationary imbalance. The specific cause of the cross-stock failure remains **unproven**; it is a hypothesis to investigate separately, not a supported causal inference.
3. Class support, decision coverage, confusion matrix, per-stock/day evaluation and explicit untouched future-test policies are indispensable.

**Not supported:** Existence of executable trading alpha, interpretable economic depth signal, classification superiority on macro-F1, stable cross-stock generalization, or any trade execution effect. Overlapping five-quote labels and stock/day dependence rule out naive IID significance.

**Next research step (NOT YET EXECUTED):** On the **14 fit dates only**, diagnose whether volume-imbalance feature scales, stock-specific depth patterns, class-weighting and calibration explain the B2 collapse. Use source-blind fixed hypotheses, training-block-only comparisons and no repeated tuning against the six examined internal confirmation dates or original five validation dates. Preserve the final ten-date sealed test for one later frozen evaluation. No additional later-date price analysis, model changes, trading or merging has been authorized in this D010 outcome.

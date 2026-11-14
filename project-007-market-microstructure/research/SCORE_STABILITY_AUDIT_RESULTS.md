# Project 007 — D013 score-stability / eligibility-denominator audit: COMPLETED

**Source-authenticated November 12, 2026. AI-assisted retrospective explanatory analysis of ALREADY OPEN D012 dates, not an independent new holdout or newly successful predictor.** [Frozen D013 audit protocol](SCORE_STABILITY_AUDIT_PROTOCOL.md) was committed before this additional source access. [Successful one-time GitHub Actions audit](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43262562364). Source-reading job is temporary and must be removed after this audit.

## Finding

D012's roughly 6.4–6.7% alerting during April 21–27 was **not explained away by the mismatch between label-blind calibration eligibility and future-target-matched confirmation eligibility**. With the identical *current/past-only* decision eligibility rule in both calibration and confirmation, the fixed balanced model emitted **923/14,001 = 6.5924%** alerts, and unweighted **886/14,001 = 6.3281%**, against **553/27,756 = 1.9924%** in calibration for EACH model. No cutoffs were changed.

The D012 future-target-matched subset had 13,819 observations. On those exact same origins, the source audit **independently reproduced** the original **919** balanced and **882** unweighted alerts; all six per-stock source cutoffs reproduced to the eight decimal places originally published. Among the 182 extra confirmation decision-ready but not future-target-verifiable observations, **only four** crossed either model's threshold. Thus denominator selection only slightly changed the published percentage; score-tail shift under a consistent current/past eligibility definition is real **for these frozen fitted models and periods**. It does not identify a causal mechanism or prove persistent out-of-time predictability.

## Frozen source and design

- [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), Quant Arena / LaPlace's Eye / Einsia AI, **CC BY-NC 4.0 noncommercial research with attribution**. Exact earlier-pinned revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`; SHA256-verified original `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet` against published `SHA256SUMS`. All 484-stock common date inventories and source member row counts rechecked.
- Exact [D012 45-date metadata-only manifest](FRESH_SELECTIVE_DATE_MANIFEST.json) `fe19d601c74f3276e13d8fda3e03ebebcc548bcdb1a2b748138c2d7040d7f3da`. Fit **Mar 8–Apr 6**, label-BLIND calibration **Apr 7–20**, explanatory confirmation **Apr 21–27**, sealed final **Apr 28–May 16** (2022). The D009 Feb 22–Mar 7 final also remained unscored.
- Re-created D012's original `StandardScaler+LogisticRegression` (scikit-learn **1.6.1**, C=1, lbfgs, max_iter=400, seed=7007), class-weight balanced vs none, original spread and two displayed-depth-imbalance snapshot features, and original `max(p_up,p_down)/(p_stationary+1e-12)` score. **54,290** original training feature/label-eligible rows exactly reproduced. The original fit-only class support printout counts other target-eligible rows and is NOT the distribution of those 54,290 book-complete fit cases.
- Label-blind calibration used only current and five contiguous valid past quotes. No calibration future-target labels were computed. Confirmation decision-time eligibility **used precisely this same gate**, independently verifying its equivalence to B1 past-history coverage. A retrospective matched subset additionally required an eligible future target, never to decide whether to alert. No threshold retune, alternative training configuration, refit on confirmation, added feature, or per-origin source export.
- Whole selected source member blobs were accessed to authenticate publisher hashes; a boundary Parquet batch could decompress sealed-date bytes, but **no sealed final record entered features, labels, scores or reports**: statistical rather than physical data segregation.

## A. Aligned alert-frequency and score-tail shift

| Fixed model | Label-blind calibration decision eligible | Calibration alerts | Current/past-only confirmation eligible | Confirmation alerts | Cal. rate | Conf. rate | D012 matched confirmation (alerts/N) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Balanced | 27,756 | 553 | 14,001 | 923 | 1.9924% | 6.5924% | 919/13,819 (6.6503%) |
| Unweighted | 27,756 | 553 | 14,001 | 886 | 1.9924% | 6.3281% | 882/13,819 (6.3825%) |

Both model classes reproduced all **per-stock calibration cutoff values to eight decimal places** and all D012 target-matched confirmation alert counts. Difference between 14,001 and 13,819 is 182 decision-time eligible observations lacking the frozen D012 future-label evaluation eligibility. Their extra alerts = 4 in either model.

### Stock-specific decision-time rate and 98th-percentile diagnostic score

The score 98th percentile in the *new period* is descriptive only, **not** a replacement cutoff.

| Stock | Frozen W cutoff (cal p98) | Confirm W score p98 | W cal rate | W confirm rate | U cal rate | U confirm rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 1.88134 | 3.19792 | 1.9915% | **9.0735%** | 1.9915% | **8.8605%** |
| 000025.SZ | 1.71470 | 2.51378 | 1.9940% | **5.7471%** | 1.9940% | **5.3134%** |
| 000031.SZ | 4.44242 | 6.13378 | 1.9917% | **4.9414%** | 1.9917% | **4.7923%** |

The equivalent unweighted score-p98s moved **0.14798 → 0.23378**, **0.13697 → 0.19236** and **0.31666 → 0.42400**, respectively. These distributions use model scores, **not independently calibrated event probabilities**.

## B. Five-date temporal concentration on the aligned 14,001 population

| Date (2022) | Eligible current/past origins | W alerts | W rate | U alerts | U rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Apr 21 | 2,811 | 118 | 4.20% | 113 | 4.02% |
| Apr 22 | 2,783 | 138 | 4.96% | 123 | 4.42% |
| Apr 25 | 2,790 | 144 | 5.16% | 138 | 4.95% |
| Apr 26 | 2,800 | 193 | 6.89% | 188 | 6.71% |
| Apr 27 | 2,817 | 330 | 11.71% | 324 | 11.50% |

Alert rates rose across these five already-examined dates on both models, peaking on April 27. **This is only five clustered dates; no claim of a persistent trend or IID statistical significance.**

**000012.SZ on April 27:** W model **186/939 = 19.81%** current/past-eligible observations crossed its original fixed threshold, compared with original D012 **183/929 = 19.70%** matched origins. W score p98 that day was **6.47392**, versus that stock's frozen calibration cutoff **1.88134**. Its median best-level imbalance was **−0.3670**, five-level imbalance median **0.0615**, spread median **18.37 bps**. The score/feature co-movement is not proof of cause.

## C. Session effects and descriptive feature changes

| Confirmation session | Decision-ready origins | W alerts/rate | U alerts/rate |
| --- | ---: | ---: | ---: |
| Morning continuous session | 7,128 | 524 / **7.35%** | 505 / **7.08%** |
| Afternoon continuous session | 6,873 | 399 / **5.81%** | 381 / **5.54%** |

These are unadjusted session aggregates. Stock/day composition and serial dependence prevent reading this as a market-session causal effect.

Median spread bps (same decision-time-eligible population), calibration → confirmation:
- `000012.SZ`: **14.55 → 17.14**
- `000025.SZ`: **7.58 → 9.20**
- `000031.SZ`: **22.81 → 25.41**

Median *five-level displayed-volume imbalance* did not move uniformly across the panel: `000012.SZ` **0.278 → 0.190**, `000025.SZ` **0.156 → 0.117**, `000031.SZ` **0.209 → 0.285**. Spread widening and imbalance changes are **descriptive associations**, not established drivers of false alerts. The two different class-weight models show similarly elevated above-cutoff fractions, which does not by itself establish common alert overlap at an observation level.

## Interpretation and integrity

**Supported:** A genuine fitted-score-tail distribution change on equivalent decision-time source populations, concentrated by date and stock, accompanied by changes in observed book-spread and imbalance summaries. Correctly comparing the two eligibility gates did **not** rescue the original fixed 2% score-budget behavior. All reproduced D012 directional-alert outcomes remain negative; no model promoted.

**Not supported:** An explanation in terms of a particular market event, genuine latent regime, causal order flow, transferable probability calibration, stable uncertainty, high confidence directional detection, market-making edge, fills, order submission, execution cost, slippage or P&L. Quote horizons overlap within stock/date; do not treat 14,001 rows as independent replicates.

**Future trust gate:** Before considering any directional warning model as credible, define event/value and harm/cost in advance, select an alert rule on genuinely *new* development dates (never repeatedly retune using Apr 21–27 or reserved final dates), show materially improved day/stock-cluster-robust directional precision at an acceptable false-alert rate and nontrivial up/down recall, demonstrate per-stock/per-session alert-volume stability relative to decision-time denominators, then pass a separate genuinely downstream test **one time**. A trading claim would additionally require latency, fill feasibility, spreads/fees/impact, proper risk controls and trade P&L evidence. No universal percentage threshold can be declared without the decision context.

**Audit provenance:** [successful source run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43262562364); **174 synthetic tests on each of Python 3.11 and Python 3.12** on updated branch; ephemeral source-reader removed after recording results. Raw vendor prices and per-origin predictions never committed. Draft PR #7 remains unmerged. Neither historical final holdout scored.

# Project 007 — D010: Three-stock / five-day label-construction replication

**Run date:** November 11, 2026. **Status:** empirical *descriptive* panel completed; independent label verification passed. **Research track:** Quant-Arena Shenzhen market quotes, **NOT FI-2010 original Helsinki data**. The user selected the predeclared investigation; all code, analysis, and provisional interpretations here are AI-assisted, not claims written by the human lead.

## Source, license, provenance and exact selection

- Source: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), publicly released by Quant Arena / LaPlace's Eye / Einsia AI, hosted as `Ashitemaru/Quant-Arena-Public-L1`; published under **CC BY-NC 4.0, noncommercial use with attribution**.
- Dataset version: immutable Hugging Face revision **`fa85d7b95e56e81317ac349f52e916ca482f0f68`**; plain TAR `quant-arena-public-l1-v1.tar`. Dataset documents 15-second Level-2 snapshots, 45 columns and 289 Shenzhen equities during 2022–23.
- Locked deterministic stock selection from `research/NEXT_PANEL_PROTOCOL.md`: existing example **000012.SZ** plus **the first two lexicographically smallest distinct valid stock filenames actually in the archive**: **000025.SZ** and **000031.SZ**. Neither substitute stocks nor handpicked best-performing labels were used.
- Locked dates: first five chronologically observed sessions for each stock: **January 4, 5, 6, 7, 10 of 2022**. The earliest five *observed* sessions are not separately certified to be complete exchange sessions.
- Source checksum gate: HTTP 206 exact byte ranges; TAR header checksum validation; publisher `manifest.json`; per-stock full-file SHA-256 matched `SHA256SUMS` within the pinned source archive. Only selected three Parquet members downloaded. **Whole 6.23 GB archive was neither downloaded nor SHA256 verified.**
- Stock member checksums:
  - `000012.SZ.parquet`: `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`
  - `000025.SZ.parquet`: `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`
  - `000031.SZ.parquet`: `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`
- Network transfer: **70,447,590 bytes**. The verified file contents were held in temporary runner storage and deleted; **no original quote rows or vendor Parquet files committed to GitHub**.
- [Successful run, source logs and aggregate report](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43105937543). Python 3.11 and 3.12 synthetic CI passed **99 tests**. The panel used `research/run_quant_arena_panel_once.py` and independently double-calculated all prospective label origins using `microstructure/stockday_oracle.py`.

## Definitions fixed before opening additional stocks

At each source best-quote observation, define `mid=(best_bid+best_ask)/2` and compare it with the **arithmetic mean of the next k valid midpoints in the same contiguous stock/day segment**, not with the final future midpoint alone. Labels use class **1 up**, **2 stationary**, **3 down** for returns `>= +0.002`, strictly between `-0.002` and `+0.002`, and `<= -0.002`. Horizon grid `k=1,2,3,5,10` sampled snapshots. Gaps over a *provisional* 30-second cutoff, stale/missing/one-sided/locked/crossed books and insufficient futures interrupt segments; no fill/interpolation or cross-day target is permitted. Threshold sensitivity at k=5 was predeclared: 0.001, 0.002, 0.004. All shares below use **eligible label observations**, not all source rows.

## Main real result: ±0.2% at five-snapshot horizon

| Stock | Source rows across 5 dates | Up | Stationary | Down | Unlabelled | Eligible | Stationary / eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 000012.SZ | 5,078 | 122 | 4,438 | 126 | 392 | 4,686 | **94.71%** |
| 000025.SZ | 5,077 | 58 | 4,267 | 39 | 713 | 4,364 | **97.78%** |
| 000031.SZ | 5,078 | 308 | 4,107 | 271 | 392 | 4,686 | **87.64%** |
| **Pooled (row-weighted)** | **15,233** | **488** | **12,812** | **436** | **1,497** | **13,736** | **93.27%** |

The **10.13 percentage-point** spread between the highest and lowest stock stationary rates occurs under the identical fixed horizon/threshold, so a uniform label rule does *not* determine equal class prevalence for every stock. However, this result alone does **not** identify the cause: source price behavior, quote quality, tick-size/price scale, stock volatility, selection and data filtering could all contribute.

### Explicit incomplete-label attribution

| Stock | Invalid/stale quote origins | Insufficient contiguous future | Total unlabelled at k=5 |
| --- | ---: | ---: | ---: |
| 000012.SZ | 289 | 103 | 392 |
| 000025.SZ | 353 | 360 | 713 |
| 000031.SZ | 289 | 103 | 392 |
| **Total** | **931** | **566** | **1,497** |

The higher missing-label count for 000025.SZ means the eligible denominator differs by stock. Do **not** interpret discarded future windows as actual flat prices. Quality counters overlap and cannot be added as mutually exclusive categories.

### By-date confirmation and known source gaps

All three security files selected the same five observed dates. The publisher's source documentation expressly cautions about shortened public quote sessions on **2022-01-06 and 2022-01-10**, and our verified row counts reflect this: the otherwise 1,023-row daily grid had **999 rows on January 6** for all three stocks, and **1,009–1,010 rows on January 10**. These are observed source coverage differences, not proof of market halts, illiquidity or a bad feed.

At k=5, ±0.2%, the stock-day stationary rates ranged as follows:
- 000012.SZ: **93.50%–97.13%** across five days.
- 000025.SZ: **96.51%–99.33%** across five days.
- 000031.SZ: **83.83%–89.34%** across five days.

This is descriptive **between-stock and between-day heterogeneity** in a *single early-week panel*; no statistical independence claim is made.

## Predeclared threshold sensitivity at k=5

| Neutral band | Eligible | Up | Stationary | Down | Unlabelled | Stationary / eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ±0.1% | 13,736 | 1,379 | 10,984 | 1,373 | 1,497 | **79.97%** |
| ±0.2% | 13,736 | 488 | 12,812 | 436 | 1,497 | **93.27%** |
| ±0.4% | 13,736 | 72 | 13,636 | 28 | 1,497 | **99.27%** |

A wider neutral interval *mechanically* marks more outcomes as stationary. This is an effect of **our chosen label definition** in the observed price dataset; it cannot quantify what caused FI-2010's day-eight shift.

### Across the primary ±0.2% horizon grid

| Horizon in 15-second snapshots | Up | Stationary | Down | Unlabelled | Eligible | Stationary / eligible |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 343 | 13,461 | 328 | 1,101 | 14,132 | 95.25% |
| 2 | 310 | 13,398 | 265 | 1,260 | 13,973 | 95.88% |
| 3 | 332 | 13,288 | 271 | 1,342 | 13,891 | 95.66% |
| 5 | 488 | 12,812 | 436 | 1,497 | 13,736 | 93.27% |
| 10 | 716 | 12,025 | 639 | 1,853 | 13,380 | 89.87% |

Because the eligible population changes across horizons, a simple comparison of percentages may combine both time-horizon changes and which observations remain eligible.

## Independent integrity and reproducibility

The deliberately slower independent quote algorithm checked **all 15,233 origins across all five primary horizons**, including the final-k exclusion decisions and future indices: **76,165 comparisons with zero disagreements**. It also checked three predeclared threshold settings at k=5 (**45,699 additional comparisons**, including a repeated primary-threshold pass), again with no mismatches. Two Python-version test jobs passed 99 synthetic tests each. These checks establish implementation agreement *conditional on source data and documented parsing assumptions*, not exchange-truth certification.

## Scientific answer and remaining limitations

**What the experiment supports:** The classification neutral threshold strongly influences observed class proportions. With the same threshold and horizon, class balance differs substantially across three source-identifiable stocks; excluding missing or invalid futures is important. These findings make it inappropriate to attribute a label distribution entirely to a market regime or entirely to preprocessing with no supporting controls.

**What remains unknown:** Whether the publisher's original FI-2010 labels were generated without stock/day-boundary leakage; the Shenzhen panel cannot resolve 2010 Helsinki source semantics. Its 15-second sampling differs from FI-2010's event-based processed representations. Stock-price scales/tick sizes, source staleness, gaps and exchange structure complicate comparisons. A 3-stock/5-day descriptive panel cannot establish forecasting ability, trading profits, fill probabilities or present-day strategy performance. Samples are serially dependent/overlapping, so no naïve observation-level p-values, IID confidence intervals or causal attribution are offered.

## Proposed next step (not executed)

Investigate **label sensitivity to the 30-second gap cutoff** and quality flags (without altering the preregistered main result), then consider a separate training-only baseline on later source dates using a genuinely new, frozen split design. Preserve additional dates as reserved and do not claim the current same-period descriptive panel is an out-of-sample predictive test.

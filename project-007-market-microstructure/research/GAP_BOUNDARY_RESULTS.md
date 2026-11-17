# Project 007 — D007: provenance-verified midday gap-boundary investigation

**Completed November 11, 2026.** Human lead: "Let’s keep at it Holmes" after D006 source-quality experiment. The source, hypotheses, implementation and interpretations here are AI-assisted, and do not represent the human lead as author of quantitative findings.

## Executive finding

**All fifteen long source-timestamp gaps (>120 seconds) in the frozen three-stock / five-day panel are EXACTLY 5,400 seconds**, from **11:30:00 to 13:00:00 Asia/Shanghai**, one per stock per selected trading day. All fifteen match the predeclared lunch-window heuristic. This precisely matches Shenzhen Stock Exchange's **scheduled midday nontrading recess**. [SZSE English trading-hours overview](https://www.szse.cn/English/services/trading/tradOverview/); [2019 SZSE trading times investor education](https://investor.szse.cn/knowledge/stock/deal/t20191204_572383.html). Alignment strongly supports intentional trading-session boundaries; it cannot prove that other short gaps or publisher defects are absent.

**The important validation:** Source best bid/ask immediately before and after **all 15** lunch gaps passed strict best-price validity and were **not flagged stale or missing-depth**. Nevertheless, the original **30-second maximum gap** blocked every label from crossing lunch. Removing **only** the time-gap restriction, while preserving source-quality flags and top-of-book validity, created **74 artificial across-lunch labels** (and 74 newly eligible origins). Removing the time-gap safeguard **and** ignoring both flags created **75 across-lunch labels**, demonstrating that one additional near-boundary quote restriction had separately prevented a window. **These no-gap alternatives are deliberately unsafe counterfactuals, not recommendations.**

## Predeclared protocol, unchanged source and rights

Methods were committed in [GAP_BOUNDARY_PROTOCOL.md](GAP_BOUNDARY_PROTOCOL.md) **before** source acquisition. All work uses the noncommercial **CC BY-NC 4.0** [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), distributed by Quant Arena / LaPlace's Eye / Einsia AI. This is **historical Shenzhen 2022 order-book quote data, NOT FI-2010 Helsinki 2010**.

- Immutable publisher dataset git revision: `fa85d7b95e56e81317ac349f52e916ca482f0f68`.
- Same three publisher-SHA256-verified member files as prior research:
  - `000012.SZ.parquet`: `97602d7dbf87e4baf23a22280f1395b4b856c41be2bef14269d487ad51a9d4af`.
  - `000025.SZ.parquet`: `4ed88ea4f1e5f4223fe86ea6dd7be084b22e76a62315f09bf397d13ecb006654`.
  - `000031.SZ.parquet`: `3a2a91d1afe97be65ead7d25072cc740f6800b534e36407848e1d51c06e5fbd8`.
- Identical first five observed dates per stock: **January 4, 5, 6, 7 and 10, 2022**; **15,233 quote rows** total; dates after Jan 10 were used only for date-only chronology metadata, **not** price-target analysis.
- Selective checksum-controlled HTTP 206 TAR requests transferred **70,447,590 bytes**, not the full ~6.23 GB archive; full-archive SHA256 was not verified. Temporary stock files were deleted after checking. No original vendor bid/ask prices or Parquet rows were committed.
- Primary label rule unchanged: `k=5` successive valid snapshots, mean future best midpoint relative to origin midpoint; ±0.2% class thresholds. No interpolation, no cross-stock/day labels, 30-second maximum adjacent interval and full source flags.
- [Successful source-run evidence](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43136010196); **110 synthetic tests passed** on both Python 3.11 and 3.12. Full independent per-origin checks: **15,233 × 3 = 45,699**, **zero disagreement**.
- No predictive model, return forecast, queue execution test, transaction-cost estimate, live trading or FI-2010 reserved-fold inspection occurred.

## Exact timestamp facts

| Stock | Long gaps >120s | Pre-recess edge | Post-recess edge | Duration each | Match frozen 11:28–11:30:30 / 12:59–13:02 heuristic |
| --- | ---: | --- | --- | --- | ---: |
| 000012.SZ | 5 | 11:30:00 | 13:00:00 | 5,400 seconds | 5/5 |
| 000025.SZ | 5 | 11:30:00 | 13:00:00 | 5,400 seconds | 5/5 |
| 000031.SZ | 5 | 11:30:00 | 13:00:00 | 5,400 seconds | 5/5 |
| **Total** | **15** | | | | **15/15** |

Each row represents the first five selected trading days, **one long gap per day**. At all 30 gap endpoints (before and after), original `stale=False`, `missing_depth=False`, and `bid>0, ask>bid` held. The source data records a nontrading interval; consecutive rows should **not** be interpreted as continuously tradable merely because both prices are valid.

## Frozen reference and unsafe no-gap diagnostics

The original **strict 30-second / all-flags-respected** baseline was checked per stock against the previous report *before* auditing the gaps:

| Scenario | Eligible (out of 15,233) | Stationary | Stationary / eligible | Newly eligible versus strict | Previously eligible labels changed | Actual across-lunch labels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Strict G30/F0 — reference** | **13,736** | **12,812** | **93.2732%** | 0 | 0 | **0** |
| **No max gap, flags still honored** | 13,810 | 12,873 | 93.2151% | **+74** | **0** | **74** |
| **No max gap, both flags ignored — unsafe** | 14,432 | 13,472 | 93.3481% | **+696** | **0** | **75** |

*The labels were never generated by actual trading across the recess; the two counterfactuals simply let the retrospective formula use quotes from both sides of a nontrading interval.* No max-gap changes produce outcomes with radically different **wall-clock horizons** than the intended five 15-second snapshots.

The **+696** versus the original reference is the combined effect of **+621** stale-flag-relaxation labels from D006 and **+75** cross-lunch labels from removing the gap rule. The two mechanisms are complementary in this sample; **do not** treat the resulting 14,432 labels as additional valid trading observations.

### Which stock and session contributed?

| Stock | Strict eligible | No-gap, flags honored eligible | Newly eligible via lunch | No-gap, both flags ignored eligible |
| --- | ---: | ---: | ---: | ---: |
| 000012.SZ | 4,686 | 4,711 | +25 | 4,811 |
| 000025.SZ | 4,364 | 4,388 | +24 | 4,810 |
| 000031.SZ | 4,686 | 4,711 | +25 | 4,811 |
| **Total** | **13,736** | **13,810** | **+74** | **14,432** |

In the strict-flag, no-gap mode, each daily lunch gap produced five additional across-recess labels **except January 10 for 000025.SZ**, which produced four. Under the both-flags-ignored stress setting, each of the 15 gaps produced five crossing labels, for **75** total. The single suppressed case is consistent with an adjacent source-quality barrier; this aggregate test does not independently establish whether it was solely stale, solely missing depth, or both without a dedicated per-origin provenance inspection.

**No class assignment among previously eligible origins changed** in either no-gap stress setting, nor did their future-target indices. This is a window-eligibility effect, not evidence that all existing labels were wrong.

## What was and wasn't falsified

**Supported:** The fifteen longest discontinuities are scheduled midday session breaks. Explicit temporal segmentation matters: the 30-second reference rule prevented construction of targets across a **90-minute exchange closure**, even though the boundary prices themselves looked valid. All existing reported strict-label counts remain intact; the independent algorithm agrees for every origin in the three checked configurations.

**Not supported:** That scheduled recesses exhaust the source's missingness; that ignoring quote flags or time-gap rules is safe; that pre- and post-recess quotes should be compared as consecutive continuous-market samples; that these labels reveal tradable alpha or executable spreads; or that this independent Shenzhen sample validates original FI-2010 Helsinki label construction.

**Recommended invariant before eventual predictive modeling:** Explicitly tag session segments (morning continuous auction vs afternoon continuous auction), in addition to stock/date, and require every target window to stay entirely within one segment. Treat that as an engineering design requirement to verify with independent tests before any future holdout or model fitting. Time-gap thresholds are valuable but should not be the **only** defense against known session breaks.

This report is descriptive and does not authorize further data acquisition or open future-date labels. Original FI-2010 reserved days 9 and 10 remain unread.

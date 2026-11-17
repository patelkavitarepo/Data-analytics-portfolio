# Project 007 — D007 preregistered source-gap boundary investigation

**Frozen November 11, 2026 before opening source data for this investigation; executed afterward without changing any source, sample or diagnostic rule.** Attribution-bearing results: [GAP_BOUNDARY_RESULTS.md](GAP_BOUNDARY_RESULTS.md). Human direction: "Let’s keep at it Holmes" following our verified D006 quote-gap/flag audit and recommendation to examine the fifteen large within-stock/day gaps. This proposal and any ensuing interpretation are AI-assisted. No model selection, strategy, trade, merge, or FI-2010 holdout access is authorized.

## Question

Previous D006 source-only research on Quant-Arena Public L1 identified **15 within-stock/day availability timestamp gaps greater than 120 seconds**, five per stock, while cutoff changes of 15/30/60/120 seconds changed zero labels. Are these gaps aligned with the Shenzhen Stock Exchange's scheduled **11:30–13:00 local midday break**, rather than unscheduled missing intervals? Do invalid/stale quotes *also* prevent labels from spanning these long gaps?

## Source and pre-fixed sample

Same noncommercial **CC BY-NC 4.0** dataset and original source revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`, same authenticated members `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet` (publisher SHA256 in [GAP_FLAG_SENSITIVITY_RESULTS.md](GAP_FLAG_SENSITIVITY_RESULTS.md)), and same first five observed dates **January 4, 5, 6, 7, 10, 2022**. No later-date price columns, different symbols, 2024+ samples, or original Helsinki FI-2010 records will be opened. Perform bounded HTTP 206 source-member selection, validate publisher checksum, and discard temporary vendor files.

**Official reference for source-time semantics:** [Shenzhen Stock Exchange trading-hours overview](https://www.szse.cn/English/services/trading/tradOverview/) and [2019 SZSE investor education trading-times explanation](https://investor.szse.cn/knowledge/stock/deal/t20191204_572383.html): continuous auctions **09:30–11:30** and **13:00–14:57**, with midday recess from 11:30 to 13:00, Asia/Shanghai time.

## Frozen diagnostics (before source read)

- Enumerate *all* successive within-stock/day availability gaps **>120 seconds**; no sorting, interpolation or vendor-row modification. Report for each only symbol, selected date, start clock, end clock, elapsed seconds, and whether either edge has a nonvalid top book, stale flag or missing depth. Do not emit bid/ask prices or raw quote rows.
- A gap is **consistent with scheduled midday recess** if the earlier timestamp is between **11:28:00 and 11:30:30** (inclusive) and the later timestamp is between **12:59:00 and 13:02:00** (inclusive). This is a pre-fixed heuristic designed to allow the 15s sampling grid and minor delays; it does **not** establish the trading venue's event semantics by itself. Report every gap that fails the heuristic as an unexplained source discontinuity. Independently verify exact distribution of durations and whether gaps >120 match the previously recorded **15**. No gaps may cross trading dates.
- Preserve the previously published baseline: original strict-quality k=5, **±0.2%**, 30-second gap with **15,233 total rows**, **13,736 eligible**, **12,812 stationary**; verify each stock's exact frozen counts first, and independently verify every origin/target/exclusion decision.
- Deliberately **unsafe counterfactual** sensitivity: compare original 30-second strict flags with **no maximum adjacent gap** at (a) original strict flags and (b) both stale/depth flags ignored, while still requiring real, positive, uncrossed best bid/ask and same stock/day. Count newly eligible labels, classes changed among previously eligible, and explicitly count *any* label whose future indices straddle a >120-second gap. These are only construction diagnostics, never endorsed data preparation or executable quotes. Independently verify both counterfactual calculation paths against the separate slow oracle. This no-gap test is exploratory **after D006**, but its exact rules are frozen before this new source read.
- A gap may be surrounded by invalid quotes; we must distinguish **temporal boundary** from **price validity** and **source quality flags**. Report which barriers prevent spans in each counterfactual. Report per-stock/day counts, no hypothesis tests treating overlapping outcomes as IID, no model fitting.
- Interpret only within the source and time range. An exact lunch-time match is strong evidence of planned data-collection discontinuity, **not** proof that no other missing data exist. The Shenzhen 2022 analysis cannot authenticate FI-2010 Helsinki 2010 label handling.

## Result gates

Do not promote any gap attribution or label comparison until verified source SHA256, date count and primary labels reconcile to prior published receipts. Record limitations and data license. Keep daily rows and price bytes outside GitHub; source-reading job is single-use and must be removed after receipt. Draft PR remains unmerged.

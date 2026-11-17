# Project 007 — D009: FI-2010 dataset-construction audit

**Status:** Authenticated-source historical *descriptive* audit. AI-assisted investigation after human lead D002: **"I would like to investigate the datasets construction."** This report does **not** assert that preprocessing caused the day-eight result or that a market regime changed. No feature-based models fitted; no reserved folds opened.

## Sources and reproducible evidence

**Primary research paper:** Ntakaris, Magris, Kanniainen, Gabbouj and Iosifidis (2018), *Benchmark dataset for mid-price forecasting of limit order book data with machine learning methods*, *Journal of Forecasting*, https://doi.org/10.1002/for.2543, especially Sections 3.3–3.4, Figure 2, Eq. (7) and Eq. (8). Dataset publisher: https://metax.fairdata.fi/v3/datasets/73eb48d7-4dbc-4a10-a52a-da745b47a649 — Open / CC BY 4.0.

**Actual data examined:** DeepLOB researcher-hosted `data.zip`, 56,278,154 bytes, SHA256 `7a5564290a504bdc104dccaf44aa6c0b3857bf1db6b0517b9b88577c2def3e5f`. Only `Train_Dst_NoAuction_DecPre_CF_7.txt` (training days 1–7) and `Test_Dst_NoAuction_DecPre_CF_7.txt` (day eight) were opened. Bytes matched the pinned prior acquisition. Days nine and ten were **not opened or evaluated**. Byte equivalence of the research-hosted ZIP with the original Fairdata deposited archive remains unverified.

**Code:** `microstructure/fi2010_construction.py` reads **all five publisher-supplied label rows** directly from those files, independent of our original one-horizon baseline reader. It does not reconstruct prices or buy/sell orders. `research/run_fi2010_construction_once.py` runs against a checksum-pinned ephemeral source and calculates descriptive statistics. [Source/data run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43094493112). The synthetic test suite passed **67 tests** on Python 3.11 and 3.12 during this investigation. The first real audit attempt rejected scientific-notation labels; the parser was fixed to use exact Decimal conversion. No altered source data were used.

## Verified publisher construction choices

1. **Sampling:** The event-driven raw feed is downsampled to a processed representation; the accessible benchmark has only publisher-preprocessed snapshots. Its target horizons are **1, 2, 3, 5 and 10 processed observations**, not seconds, nor directly those many raw order messages. The primary paper discusses event-based sampling and 10-order-event sampling.
2. **Classification rule:** For horizon `k`, Eq. (8) uses the average of the next `k` future mid-prices relative to the current mid-price, i.e. `(sum(mid[i+1:i+k+1])/k - mid[i])/mid[i]`. It is **not** merely the last future midpoint compared with today's midpoint. Class 1 denotes an averaged increase ≥0.002 (up); class 3 a decrease ≤−0.002 (down); class 2 is stationary otherwise.
3. **Trading-hour filtering:** The authors selected approximately 10:30–18:00 Helsinki local trading hours, removing auction-adjacent market activity. Historical exchange time conventions should not be inferred from the published data matrix.
4. **Representation/normalization:** This investigation uses **NoAuction / DecPre**: published 144-dimensional representations (basic depth and derived features) with decimal-precision transformation. These data are not original exchange ITCH messages. The source publisher explicitly states that public normalization prevents reconstructing the original Nasdaq data. Normalization rules and precomputed labels may have broader scope than a prospective training fold; their exact fit/input boundaries have **not been certified** from released data.
5. **Cross-validation:** Publisher documents day-based anchored evaluation: `Train_CF_7` contains first seven days and `Test_CF_7` contains the next, eighth day. No assumptions are made about stock/time identity of individual rows within the pooled matrix.

## What our own files show: class 2 (stationary) across all five horizons

| Horizon (sampled representations) | Train days 1–7 stationary % | Day 8 stationary % | Day 8 − train (percentage points) |
| --- | ---: | ---: | ---: |
| 1 | 60.53 | 73.22 | **+12.69** |
| 2 | 49.41 | 65.31 | **+15.90** |
| 3 | 41.80 | 59.61 | **+17.81** |
| 5 | 31.67 | 51.24 | **+19.58** |
| 10 | 19.41 | 38.69 | **+19.28** |

Sample counts are 254,750 training observations and 55,478 day-eight observations for every horizon; records are not independent IID observations. No p-values, standard errors or significance tests are asserted.

**Empirical reading (not human-supplied interpretation):**
- The stationary share declines with longer `k` **within both periods** under the fixed 0.2% threshold. Thus horizon definition/threshold choice is crucial for how many observations become class 2.
- **The increase on day eight exists for all horizons**, so it is **not** just an artifact of having selected the fifth-row, five-observation horizon. This does not rule out a dataset-construction issue.
- On day eight, at horizon five, five equal **consecutive observation-order** segments have stationary shares **37.21%, 45.28%, 61.19%, 50.17%, and 62.37%**. These are **NOT** five time intervals and **NOT** five distinct stocks; the public processed matrix does not supply those identities. Treat any explanation based on time of day, particular stock, or market regime as untested.

## What is falsified, plausible, or unresolved

**Falsified as a complete explanation:** "The day-eight stationary jump is only a coding mistake in selecting the five-observation label row." Parsing and published horizon-row assignments were checked; the increase occurs across all label rows.

**Plausible but not established:** The fixed classification threshold mechanically changes the class balance as forecast horizon increases; unequal source stock/event mixtures, preprocessing, data selection or different source-day price behavior could alter day-eight class balance. The present audit cannot isolate causal shares.

**Still unresolved:** Whether publisher-provided labels near a day boundary use price observations from a following day; whether pre-normalization statistics depend on future folds; exact session/stock separators and raw timestamps; whether original Fairdata files are byte-identical to this public researcher-hosted ZIP. **Do not describe this benchmark evaluation as leakage-certified.**

**Prohibited inference:** Comparing the 51.24% *hindsight day-eight* majority to the training-only constant baseline is not a deployable model. No execution-cost, queue position, P&L, contemporary-performance or alpha inference is warranted.

## Proposed next investigative gate (not yet a user decision)

Seek raw or minimally transformed official mid-price sequences with reliable per-stock and per-day boundaries, if available and licensed. Only then can we independently regenerate labels and test the exact 0.002 rule, boundary handling, and class mix by stock/day. If unavailable, treat publisher labels as unverifiable downstream annotations and explicitly state that as a permanent limitation of FI-2010.

Until resolved, **do not promote a feature-based model comparison, inspect days nine or ten, or merge PR #7**.

# Project 007 — Original per-stock/per-day midpoint acquisition investigation

**November 11, 2026. Status: original sequences not acquired.** This is an acquisition-source review, not a substitute for raw data and not an empirical re-labeling result.

## What we need

To investigate whether the public FI-2010 labels cross stock or session boundaries, obtain **source-identifiable** order-book best quotes from the Helsinki exchange for FI-2010's five symbols (KESBV, OUT1V, SAMPO, RTRKS, WRT1V) on **June 1–14, 2010 (10 trading days)**, with:
- Original security identifiers and exchange trading date.
- Strictly ordered event or snapshot time at the available resolution, including duplicate-time ordering rules.
- Original, *unmodified*, positive best-bid/best-ask prices and ideally sizes and trading status.
- Definition of sampling: every 10 exchange events? beginning or end of batch? Per stock or global? price before/after event?
- Explicit trading-session and symbol transition markers, price units and timezone.
- Permission for local analysis and for publication of attribution-bearing aggregates and derived labels, and provenance file manifest/hash and vendor information.

A closing-price series, consolidated OHLCV bars or a separate stock market dataset is **not a valid reconstruction** of the FI-2010 benchmark's original midpoints.

## Source routes investigated (ranked)

### A. Original authors / dataset custodians — highest semantic fidelity, access must be requested
- Dataset: https://etsin.fairdata.fi/dataset/73eb48d7-4dbc-4a10-a52a-da745b47a649
- Source paper, Section 3.3: https://doi.org/10.1002/for.2543
- Authors explicitly state the public benchmark was normalized under Nasdaq agreement to prevent reconstructing original data. Thus CC BY 4.0 on the *published benchmark* **does not grant entitlement to original non-public exchange messages or raw quotes**.
- Request either **licensed raw per-stock/day quotes**, or (if originals are restricted) a **nonreconstructive validation artifact**: per-stock/day boundaries, per-stock/day class counts by horizon, label boundary rules, pseudonymous stock/day IDs, and a reference code snippet for computing Eq. (8).
- The article lists corresponding author Adamantios Ntakaris; use the verified publisher correspondence link. Do not invent an address.

### B. Aalto University Datahub — preserved 2010+ source, external access not presumed
- https://datahub.aalto.fi/en/data-sources/nasdaq-nordic-equity-totalview-itch-market-feed
- Their archive describes Nasdaq Nordic/Baltic ITCH source feeds from **2010-present**, capable of full-book reconstruction; academic use free **at Aalto**. Entry specifically lists access for **Aalto users/students/staff**. Current user eligibility for access is unknown; it is not an open public download.
- Datahub contact: **datahub@aalto.fi** (published on that service's record). Ask whether an external independent research project may receive a restricted 10-day, five-symbol derived best-quote extract under approval and citation/publication terms.

### C. Nasdaq Nordic HistoricalView — authoritative venue, likely commercial access
- https://www.nasdaq.com/products/data/nordic-baltic/historicalview
- Official Nasdaq feed/product offers tick/order logs; older history may be requested from **datasales@nasdaq.com**. Pricing, 2010 historical coverage for those dates and permitted redistribution/derived artifacts are **not confirmed**.
- Obtain a quote and usage terms **before** ordering or incurring costs. No paid action taken.

### D. Original publisher Fairdata metadata and files — check archive manifest before any assumptions
- Official dataset metadata: https://metax.fairdata.fi/v3/datasets/73eb48d7-4dbc-4a10-a52a-da745b47a649
- Record confirms public **CC BY 4.0 for deposited data**; it does NOT show that a separately licensed original-ITCH download exists in this dataset.
- A metadata-only program `probe_stock_day_sources.py` was committed to inspect file/directory indexes without raw-data acquisition. API file-list availability should be recorded when successful. Until then, original raw sequences remain unverified.

## Rejected or distinct leads

- [FI-2010 DeepLOB research archive](https://github.com/zcakhaa/DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books/tree/master/data): valid for publisher-processed 149-row matrices and preliminary benchmark-label analysis; **does not carry verified original symbol/date/elapsed-time sequences**. Already used, hashes and baseline in `EMPIRICAL_DAY8.md`.
- [Former simaki/fi2010 CSV](https://dm13450.github.io/2023/11/25/Free-Finance-Datasets-for-Quants.html): 2023 research blog referred to a file with `STOCK`/`DAY` columns, but author updated July 2024 that the original account/repo was deleted. This is **unavailable and not source-authenticated**; no reliance on it as unmodified Nasdaq data.
- [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1): an independently useful alternative with actual stock symbols, dated quotes and a public **CC BY-NC 4.0** release (289 Shenzhen stocks, 2022–23, ~6.23GB tar). **It is a different exchange, time, sampling and licensing regime**. It can enable a new label-boundary methodology study, but **cannot validate FI-2010's published labels**. No archive downloaded.
- US-Lobster samples and NASDAQ US ITCH are a different market/day and cannot verify the Helsinki 2010 labels. Provider terms are separate.

## Acceptance gates

1. Original issuer and vendor license confirmed, with explicit local use and publication rights.
2. Manifest: each file named by stock and session, immutable SHA256 and a verified official/authorized source.
3. Timestamp monotonicity and tie ordering, valid prices, missing/locked/crossed and halted cases reported rather than silently dropped.
4. Complete trading-day boundaries; no forward target is permitted to cross a symbol or date boundary.
5. Independently regenerate labels from original best-quote midpoint with the publisher's **mean of future k midpoints** and the ±0.002 threshold for each k in {1,2,3,5,10}. Record how publisher handles final k observations per stock/day.
6. Independently compare regenerated counts on **training days 1–7 first**. Do not open reserved days nine or ten. Only separately investigate day eight when original-label matching is established.
7. If original prices cannot be released, seek authors' **nonreconstructive** label-generation/fold-boundary attestation, and retain the FI-2010 labeling uncertainty permanently.

## State of the case

**Not acquired:** raw Nasdaq Helsinki stock/date quotes. No company affiliation, third-party enrollment, licensing entitlement, fee or outreach submission is assumed. No raw/derived vendor data was published or committed. **We must not claim FI-2010 label boundaries are verified.**

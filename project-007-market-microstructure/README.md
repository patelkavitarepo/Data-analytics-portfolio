# Project 007 · Market Microstructure Research Lab

**Status: FI-2010 historical training-majority baseline successfully acquired, computed and independently verified; no feature-based model, execution result or trading profit claimed.** Human-led research with AI-assisted implementation. New draft branch; other projects remain unchanged.

## Research objective

Investigate how displayed liquidity and order-flow information relate to subsequent price changes, and whether predictive information remains useful when queue position, fill uncertainty, fees and latency are considered. This project is the first stage of a connected research program: 007 order-book dynamics, 008 inventory-aware market making, and 009 institutional optimal execution.

## What is implemented

A Python standard-library-only streaming audit for local paired LOBSTER message and book CSVs, including exact decimal timestamp parsing, original event order, post-event snapshot alignment, documented fixed-point prices, occupied-level sorting, event-type counts, halt-state exclusion and duplicate-snapshot checks, equal-time event preservation, non-destructive locked/crossed quote reports, prefix-only disclosures and SHA256 of both local inputs. An independent second-pass diagnostics tool computes descriptive five-minute liquidity summaries only after a complete-file audit, and checks that the input hashes remain unchanged. Synthetic unit tests verify hand-calculated results and failure handling. The audit does NOT reconstruct the exchange book, produce future price labels, train models or simulate fills.

## Run tests (Python 3.11 or 3.12)

From this project directory:

    python -m unittest discover -s tests -v

## Locally audit files (only if your applicable terms allow this use)

Get paired files directly through the official provider's sample page, not from an unverified mirror. Keep them in a local ignored data folder. The program never downloads data itself. Example for one-level files:

    python -m microstructure --messages data/AMZN_message_1.csv --orderbook data/AMZN_orderbook_1.csv --levels 1 --max-events 10000 --output artifacts/local-audit.json

For an **entire paired file** instead of a bounded prefix, substitute `--full-file` for `--max-events 10000`. Both options are mutually exclusive. Whole-file validation checks both files' entire lengths; a prefix does not.

File names above are placeholders: use the names actually inside the provider package. The output is local metadata, not a published study. Pass `max_events=None` to the Python API to audit the entire pair; the CLI defaults to a bounded prefix unless `--full-file` is supplied. A passing prefix is NOT full-file validation. No raw sample, vendor-derived report, or screenshots should be committed pending rights review.

## Phase 1A: local descriptive liquidity diagnostics (code ready, no empirical claims)

Run only with **authorized locally supplied** paired files, from this project directory:

    python -m microstructure.diagnostics --messages data/AMZN_message_1.csv --orderbook data/AMZN_orderbook_1.csv --levels 1 --bucket-seconds 300 --output artifacts/local-diagnostics.json

The output contains event-weighted spread and top-of-book imbalance summaries, counts of up/down/unchanged backward-looking mid-price changes, and anomaly tallies. The code first runs a complete paired audit. Outputs are restricted to JSON files under this project's git-ignored `artifacts/` directory; these local files are NOT authorization to redistribute vendor-derived information. The CLI does not create forward labels, train models, or simulate orders. Actual filenames, vendor rights, and source approval still need separate verification.

## Phase 1B: independent verification (synthetic tested)

The report verifier uses a **separate parsing and aggregation path** (including Decimal-based ratio arithmetic) to recalculate both overall and every time-window metric. It checks full-file hashes, event counts, halted and abnormal states, bid/ask spreads, imbalance, backward-looking midpoint directions, and exact window boundaries. The independent verifier refuses a shortened prefix report, corrupted report fields, and changed source data. Input and outputs must remain local; verification does **not** grant access or publication rights, or establish predictive validity.

From this project directory, after generating an approved local diagnostics JSON:

    python -m microstructure.independent_verify --messages data/AMZN_message_1.csv --orderbook data/AMZN_orderbook_1.csv --report artifacts/local-diagnostics.json --output artifacts/local-verification.json

The audit and diagnostic CLIs require JSON outputs inside the project's ignored `artifacts/` directory. No vendor downloads happen in CI.

## Phase 1C: synthetic-only forward-label prototype

The `microstructure.chronology` module adds **in-memory only** prototype labels and embargoed session partitioning, without reading actual provider files. It uses strictly later timestamps and elapsed-time horizons, never crosses trading sessions, and refuses labels that would cross halts or invalid snapshots. Up, down, and unchanged midpoint outcomes are distinct, and missing targets retain their exclusion reasons. Synthetic seeded differential tests independently enumerate future targets and check for future-feature leakage.

**These are candidate rules, not approved real-data labels or a trained strategy.** No project has been promoted from discovery to predictive modeling. Horizon and multi-day train/validation/holdout settings must be signed off after suitable authorized real data and human interpretation.

## FI-2010 multi-day benchmark: real historical baseline now verified

The 10-day FI-2010 public research benchmark is a **separate** dataset family, not a LOBSTER event stream. It ships normalized/preprocessed 149-row matrices (144 features, five publisher-supplied label rows); published label horizons are 1, 2, 3, 5, and 10 sampled observations, not elapsed seconds or raw exchange event counts. The official Fairdata API confirms **Open / CC BY 4.0**. The researcher-hosted archive was downloaded and SHA256-pinned. Byte identity with the originally deposited publisher file is not independently established. Read [source/rights review](research/FI2010_SOURCE_REVIEW.md) before any download or public empirical score.

A training-prior-only **constant majority-class baseline** was run on real CF7 training data (254,750 observations, days 1–7) and the day-eight file (55,478 observations), scoring **26.20% accuracy / 0.1384 macro-F1**. Independent recalculation directly from ZIP label rows verified the class counts and exact score fractions. Days 9–10 remain reserved and unread. This is a preliminary benchmark, not evidence of alpha, label-boundary independence, executable profit, or approved model evaluation.

For local reproduction, obtain the attributed researcher-hosted archive (SHA256 and link in [EMPIRICAL_DAY8.md](research/EMPIRICAL_DAY8.md)), retain the original files in ignored `data/`, and run:

    python -m microstructure.fi2010_baseline --train data/Train_Dst_NoAuction_DecPre_CF_7.txt --day8 data/Test_Dst_NoAuction_DecPre_CF_7.txt --horizon 5 --output artifacts/local-fi2010-day8.json

Only the named fold and ignored output are supported. The standalone reproducible, pinned source procedure is [run_fi2010_once.py](research/run_fi2010_once.py); routine CI **never** fetches market data. For evidence, read [Day-eight research results](research/EMPIRICAL_DAY8.md) and [official license review](DATA_RIGHTS.md).

## D009: dataset-construction audit (new real descriptive evidence)

Following the human research lead's D002 decision to investigate the dataset's construction, a separate checksum-pinned runner read all **five publisher label horizons** from actual FI-2010 train CF7 and day-eight CF7. The stationary class is **12.69 to 19.58 percentage points more prevalent** on day eight across horizons 1, 2, 3, 5, and 10; it also declines with longer forecast horizon within each period under the fixed 0.2% threshold. Day-eight observation-order quintiles for horizon five range from 37.21% to 62.37% stationary; these are not clock-time or per-stock breakdowns. The code and **67 synthetic tests** passed on Python 3.11/3.12; the one-shot research-data job was removed after audit.

**This is not proof of a flawed dataset or a changed market regime.** The published source labels cannot yet be independently reconstructed at stock/day boundaries; upstream preprocessing and boundary handling remain unverified. No predictive model has been fitted and days nine/ten remain unread.

Read the complete [construction investigation](research/CONSTRUCTION_AUDIT.md), [human decision log](research/DECISIONS.md) and [source-verified baseline](research/EMPIRICAL_DAY8.md).

## D003: original stock/day midpoint source investigation

The human lead requested a source-authentic set of **per-stock, per-day best bid/ask quotes** to investigate FI-2010 label construction. The original exchange prices are not present in the published normalized files; a separate source license and permission may be needed.

An acquisition review identifies: (1) FI-2010 authors/Fairdata, (2) Aalto's Nasdaq Nordic ITCH archive (available to Aalto users; external use requires approval), and (3) Nasdaq Nordic HistoricalView (historic files via sales). The previous `simaki/fi2010` CSV with claimed stock/day columns has been deleted by its author and was not provenance authenticated. An unrelated CC BY-NC 4.0 stock-and-day book-quote dataset is only an **alternative experiment**, not a way to confirm FI-2010 label provenance.

**No true original Helsinki 2010 stock/day quote sequences have been obtained; no fee or access request was submitted.** See [source acquisition investigation](research/ORIGINAL_MIDPRICE_SOURCES.md) for contacts, links, rights and rigorous future acceptance gates. A metadata-only Fairdata probe is committed but results remain pending and are not treated as evidence of an available raw-data file.

## D004: noncommercial source-identifiable quote fallback (in development)

Research communication with the FI-2010 custodians may help but is **not a prerequisite** for continued analysis. While the original Helsinki 2010 quotes remain inaccessible, a distinct, noncommercial source has been selected for independent label-construction validation: [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1). It contains 289 Shenzhen equities across 2022–2023, book prices in CNY, reported 15-second snapshots, stock identifiers, availability timestamps and source quality flags. The declared license is **CC BY-NC 4.0**; its original version/manifest and actual row schema still require validation. This is NOT data from FI-2010.

The separate `microstructure/stockday_labels.py` prototype calculates the relative change between the origin midpoint and the **arithmetic mean of the next k valid midpoints**, using ±0.002 thresholds. It explicitly forbids crossing stock, trading date, stale/invalid quotes or >30-second availability gaps (a provisional setting for 15-second input). It calculates contiguous segment midpoints and prefix sums in linear time; source ingestion has now been completed on the actual authenticated single-stock two-day pilot, with no predictive fitting. `tests/test_stockday_labels.py` contains synthetic stock/day/gap edge cases.

A publisher-revision-pinned selective TAR reader has now successfully authenticated **000012.SZ.parquet** through the source's `SHA256SUMS`, transferring **25.7 MB** instead of the full **6.23 GB** release. It selected the earliest two stock trading days, **2022-01-04 and 2022-01-05** (2,046 quote observations), and reconstructed the five label horizons without fitting a model. Source quality exclusions were kept separate from stationary labels. See the attributed [first empirical report](research/QUANT_ARENA_EMPIRICAL_PILOT.md) and [successful Actions run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43100987354). The 92-test suite passed on both Python versions. Routine CI is synthetic-only; empirical access requires an explicit one-time trigger. See [separate-source protocol](research/ALTERNATE_STOCKDAY_TRACK.md).

## Independent quote-label verification — second empirical pass

An independently implemented quadratic oracle, distinct from the optimized rolling-average implementation, is now available at `microstructure/stockday_oracle.py`. A strictly predefined sensitivity check compares 0.1%, 0.2% and 0.4% thresholds at k=5 **descriptively**, while preserving the original ±0.2% registered labels. Per-day class counts and source-quality flags are reported separately. The expanded **95 synthetic tests pass** under Python 3.11 and 3.12. The independent oracle has not yet been validated on the real quote file; a separately gated source run is the next check.

## Next checkpoints

1. For FI-2010, retain CC BY attribution and verify any remaining publisher-binary equivalence questions; separately resolve rights before any LOBSTER provider acquisition.
2. Investigate precomputed FI-2010 label timing and possible train/day-boundary contamination without looking at reserved days; keep the LOBSTER paired-event study separate.
3. Human decision D002 prioritized investigating the dataset's construction; review [D009 findings](research/CONSTRUCTION_AUDIT.md) and unresolved per-day/per-stock label-boundary checks before selecting any feature-based model.
4. Compare constant/majority baseline, imbalance sign, then a simple model only if enough permitted historical days exist.
5. Add latency/fill simulation later, never reporting simulated returns as live results.

Methods: [research protocol](research/PROTOCOL.md) · [human decisions](research/DECISIONS.md) · [rights gate](DATA_RIGHTS.md).

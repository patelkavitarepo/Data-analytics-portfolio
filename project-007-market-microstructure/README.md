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

An independently implemented quadratic oracle, distinct from the optimized rolling-average implementation, is now available at `microstructure/stockday_oracle.py`. A strictly predefined sensitivity check compares 0.1%, 0.2% and 0.4% thresholds at k=5 **descriptively**, while preserving the original ±0.2% registered labels. Per-day class counts and source-quality flags are reported separately. The independent slow oracle has **successfully matched all 10,230 row-level decisions** (2,046 origins × five horizons) on actual quote data, with zero disagreements; the second real-data run and predeclared threshold sensitivity are documented in [the updated two-day report](research/QUANT_ARENA_EMPIRICAL_PILOT.md).

## D005: predeclared three-stock/five-day panel — completed

Our original source-identifiable two-day quote validation now has an expanded, deterministic **three-stock / five-day** replication on [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1), a **CC BY-NC 4.0 noncommercial** dataset entirely distinct from FI-2010. Source revision and per-file SHA256 checks were verified, and **70,447,590 bytes** transferred selectively rather than downloading the full archive. The frozen stock-selection rule yielded **000012.SZ, 000025.SZ, 000031.SZ**, with the first five observed source sessions (January 4, 5, 6, 7, 10, 2022). All three files remain out of Git.

The result: at the primary ±0.2% threshold and k=5 quote snapshots, **12,812 of 13,736 eligible labels were stationary (93.27%)**, across **15,233** raw quote observations and **1,497** explicitly unlabelled origins. The stock-level stationary percentages differed: **94.71%, 97.78%, 87.64%**. A predetermined threshold sensitivity check at k=5 yielded **79.97% stationary at ±0.1%**, **93.27% at ±0.2%**, **99.27% at ±0.4%**, illustrating that neutral-band definition matters; the remaining cross-stock differences are not explained by using different thresholds.

An independent slower implementation matched **all 76,165** primary-horizon origin/target/exclusion decisions (15,233 rows × five horizons), plus the three sensitivity passes at k=5, with **zero disagreements**. The publisher documents truncated observations on January 6 and 10; missing targets were not interpolated. **99 synthetic tests passed** on Python 3.11 and 3.12. See [detailed attributed result](research/THREE_STOCK_PANEL_RESULTS.md) and [verified GitHub Actions job](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43105937543).

The [preregistered plan](research/NEXT_PANEL_PROTOCOL.md) is retained separately as evidence of the frozen selection and labels. These are descriptive label-construction findings, **not** FI-2010 original-label verification, market predictions, investment advice or executable trading alpha.

## D006: quote-gap and quality-flag robustness — empirically verified

The human lead asked to investigate how stale/missing quotes and the existing 30-second gap cutoff affect our three-stock/five-day historical label construction. We froze eight scenarios in [GAP_FLAG_SENSITIVITY_PROTOCOL.md](research/GAP_FLAG_SENSITIVITY_PROTOCOL.md) before fetching any new data. The same three Quant-Arena Public L1 members were re-authenticated against the same pinned source SHA256 hashes; no new stock/date or later price outcome was opened.

- **G15, G30, G60, G120:** identical k=5, ±0.2% origin eligibility, targets and classes in this panel. There are 15 source timestamp gaps over 120 seconds, but varying the tested tolerance created no label changes. This does **not** establish that bridging gaps is always safe.
- **FD / ignore missing-depth only:** no change, because every missing-depth source row had an invalid/absent best price already excluded by the hard price rule.
- **FS / FSD / deliberately ignore stale:** eligible target count increases from **13,736 to 14,357** (+621), with stationary share moving only from **93.2732% to 93.4039%**. No already eligible class changes; these are **unsafe diagnostic counterfactuals**, NOT endorsed data-cleaning methods.
- Stock ranking remains **000025.SZ > 000012.SZ > 000031.SZ** in stationary share across all eight scenarios.
- Independent slow oracle verified **121,864 origin/target/exclusion decisions without mismatch**. **105 synthetic tests passed** on Python 3.11 and 3.12. Source data were only accessed in an ephemeral one-time CI job, then the job was removed and normal CI returned to synthetic-only.

Read [the D006 real-data report](research/GAP_FLAG_SENSITIVITY_RESULTS.md), [predeclared protocol](research/GAP_FLAG_SENSITIVITY_PROTOCOL.md) and [GitHub Actions evidence](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43110070553). The public source remains noncommercial **CC BY-NC 4.0** and is **not** the source for FI-2010's inaccessible Helsinki labels.

## D007: the fifteen long source gaps were scheduled midday recesses

Following the human lead's instruction to continue investigating, we preregistered a direct **timestamp and label-window boundary** check in [GAP_BOUNDARY_PROTOCOL.md](research/GAP_BOUNDARY_PROTOCOL.md), then reauthenticated the exact same **three Quant-Arena Public L1 files** under their pinned SHA256s (noncommercial CC BY-NC 4.0), without accessing any new stock/date market prices.

All **15** >120-second within-stock/day source gaps were **exactly 5,400 seconds, 11:30:00–13:00:00 Asia/Shanghai**, one per stock/date, matching the [Shenzhen Stock Exchange lunch recess](https://www.szse.cn/English/services/trading/tradOverview/). The immediate before/after quotes were valid and unflagged, so only the temporal continuity condition prevented target windows from spanning the nontrading break. With no maximum time gap, **74** across-lunch labels appeared despite full quote flags; with flags deliberately ignored too, **75** appeared. The strict 30-second reference still has **13,736** eligible labels and **zero** cross-lunch windows. No previously eligible class changed. All **45,699** independent oracle checks agreed, with **110 synthetic tests** passing on Python 3.11/3.12.

Detailed attribution, source-integrity receipts, counterfactual caveats and per-stock/day breakdown: [D007 verified gap-boundary report](research/GAP_BOUNDARY_RESULTS.md), [successful empirical GitHub Actions](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43136010196). The temporary vendor access job was removed after success. We will require explicit **morning/afternoon session boundaries** in any future predictive labeling design rather than relying solely on a numerical timestamp gap.

## D008: session-aware target labeling independently verified

The human lead continued from D007's proof that the long quote gaps were exactly SZSE midday recesses. We preregistered explicit stock/date/**morning-vs-afternoon** segmentation and built a separate `microstructure/session_labels.py` plus a deliberately independent per-origin `microstructure/session_oracle.py`. The original label generator remains unchanged. See [D008 preregistered protocol](research/SESSION_AWARE_PROTOCOL.md).

The **same** SHA256-verified three-stock, five-day noncommercial source panel was reprocessed. All **15,233** quotes were accounted for; **909 observations** (303 per stock) were outside the adopted 09:30–11:30 / 13:00–15:00 exchange-local operational windows, but they had **already been excluded** from the original strict k=5/±0.2% labels. Therefore the published **13,736 eligible / 12,812 stationary (93.2732%)** baseline was preserved with **zero class changes**. Even with the numeric gap cutoff deliberately removed, explicit-session labels produced **zero cross-lunch targets**, compared with **74 false crossing targets** in D007's older, non-session-aware no-gap stress. The 30-second cap remains our primary rule.

An independent source-quote oracle agreed on **30,466** original rows × scenarios checks, zero mismatches, and **121 synthetic tests passed** on Python 3.11 and 3.12. The publisher source release remains CC BY-NC 4.0 and no raw vendor quotes are in GitHub. Complete source-integrity, exclusions and scientific limitations: [D008 result](research/SESSION_AWARE_RESULTS.md), [verified empirical GitHub Actions](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43138003201). Temporary vendor-intake CI has been removed, returning to synthetic-only routine checks. Note that the closing call auction at 14:57–15:00 is a distinct trading phase and is not claimed to be equivalent to continuous trading.

A [new chronological prediction research design](research/CHRONOLOGICAL_PREDICTION_PROTOCOL.md) is now documented: 20 later common trading dates for training, 5 for validation, 10 sealed final holdout after the already inspected discovery dates. **Design only:** no later-date market-price reads, predictive fit, evaluation, trading or merge.

## D009: chronological B0/B1 prediction validation — completed, sealed final test intact

The human lead authorized moving into the **first carefully separated, noncommercial prediction baseline comparison** on the authentic, source-SHA256-verified Quant-Arena Public L1 (CC BY-NC 4.0) quotes. The study design was frozen in [CHRONOLOGICAL_PREDICTION_PROTOCOL.md](research/CHRONOLOGICAL_PREDICTION_PROTOCOL.md) **before** newly selected market prices were read. A separate [metadata-only audit](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43143127390) confirmed **484 stock-common observed dates**, and the date manifest was committed as [CHRONOLOGICAL_SPLIT_MANIFEST.json](research/CHRONOLOGICAL_SPLIT_MANIFEST.json) (SHA256 `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6`) before model evaluation.

- **Previously analyzed discovery:** January 4–10, 2022 (five source dates), not an untouched test.
- **Training:** 20 source dates, January 11–February 14. Source origins **61,329**, eligible future-label targets **54,063**; up **1,778**, stationary **50,583**, down **1,702**.
- **Validation:** five source dates, February 15–21. Source origins **15,345**, eligible targets **13,315**. B1 had sufficient strictly past-only quote history for **12,718** (95.52%); B0 predictions used the **training-only** majority class **2**.
- **Fair matched-coverage validation:** B0 accuracy **94.15%**, three-class macro-F1 **0.3233**, balanced accuracy **0.3333**; B1 five-previous-quote trend accuracy **89.83%**, macro-F1 **0.3573**, balanced accuracy **0.3571**. B1 detected only ~6% of actual up/down targets, and one of three stocks did not share the pooled macro-F1 improvement.
- Continuous-auction modeling policy excludes 14:57–15:00 closing call auction and respects explicit morning/afternoon segmentation, original source validity and max 30-second gaps; never interpolates quotes or uses future information for features.
- **Sealed, unscored final test:** ten dates, February 22–March 7. Their target labels, prevalence and predictive results were NOT analyzed, used to tune parameters, or published. The entire source Parquet files were downloaded for hash verification; a decoded batch may physically overlap the sealed boundary, but **no heldout row was admitted to modeling computations**. This is statistical isolation, not byte-level secrecy.

See the complete [D009 validation report](research/CHRONOLOGICAL_BASELINE_RESULTS.md), [successful real-data job](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43143730597), and model/source tests in `tests/test_chronological_baselines.py`. **135 synthetic tests passed** on Python 3.11 and 3.12. One-shot source data CI removed; routine CI synthetic-only. No advanced model trained, no stock prediction system deployed, no fill/execution model, no trading profitability or FI-2010 Helsinki label-identity claim. PR #7 remains draft and unmerged.

## Next checkpoints

1. For FI-2010, retain CC BY attribution and verify any remaining publisher-binary equivalence questions; separately resolve rights before any LOBSTER provider acquisition.
2. Investigate precomputed FI-2010 label timing and possible train/day-boundary contamination without looking at reserved days; keep the LOBSTER paired-event study separate.
3. Human decision D002 prioritized investigating the dataset's construction; review [D009 findings](research/CONSTRUCTION_AUDIT.md) and unresolved per-day/per-stock label-boundary checks before selecting any feature-based model.
4. Compare constant/majority baseline, imbalance sign, then a simple model only if enough permitted historical days exist.
5. Add latency/fill simulation later, never reporting simulated returns as live results.

Methods: [research protocol](research/PROTOCOL.md) · [human decisions](research/DECISIONS.md) · [rights gate](DATA_RIGHTS.md).

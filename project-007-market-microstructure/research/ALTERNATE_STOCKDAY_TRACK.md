# Project 007 — independent stock/day label-construction route

**Status (November 11, 2026): fallback source identified, selective acquisition not yet verified.** This is a **separate methodology experiment**, not a replication of FI-2010’s Helsinki exchange data or proof of its published labels.

## Original unresolved question

FI-2010's authors supply normalized, pooled, pre-labeled matrix files. We know the paper's approximate sampling and published 0.2% labeling rule, but cannot independently recover the original June 2010 Helsinki per-stock/day mid-price observations. The preferred original source is documented in `ORIGINAL_MIDPRICE_SOURCES.md`. Correspondence with the custodians is optional, not a gate for continuing.

## Alternate public research source

- **Dataset:** Quant-Arena Public L1, https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1
- **Maintainer:** Quant Arena (LaPlace's Eye / Einsia AI); publisher card and benchmark documentation https://quant.lab.einsia.ai/arena/doc
- **Declared coverage:** 289 Shenzhen A-share securities, 484 trading days (2022–2023), approximately 131.9 million rows; 10-level quote snapshots sampled to a 15-second time grid.
- **Format:** 6.23 GB plain tar, stock-specific Parquet files, SHA256 manifest and per-file checksums inside. Published card says date+symbol and `available_at` / `source_event_time`, top-level bid and ask prices, `stale` and `missing_depth` flags; exact schema must be inspected on genuine local files rather than inferred from documentation (the benchmark's public DataSpec uses different identity names).
- **License:** CC BY-NC 4.0. Attribution and *noncommercial use restriction* apply. The FI-2010 dataset's CC BY license does NOT grant permission to use Quant-Arena data commercially. The current experiment is strictly noncommercial/educational.
- **No original mid-price equivalence:** Different market (Shenzhen, not Helsinki), stocks, dates, quote cadence and license. Results cannot validate FI-2010's original labels, regime explanation or trading returns.

## Selective-first intake, never assume a full download

1. Probe **only 4096 bytes** of the public TAR using HTTP `Range`; require explicit HTTP **206 Partial Content** and a valid TAR header. If server ignores Range, stop the attempt rather than download 6.23 GB.
2. If range works, design a bounded per-file extraction and verify a stock-specific Parquet against manifest SHA256. Do not use a transient URL as a stable file provenance identity; retain publisher commit/version, archive SHA256 and per-file checksum.
3. Inspect exact columns, price decimals, stock/date fields, monotonicity, exchange timezone and `available_at` semantics; flag 15s gaps and noncontinuous quote periods.
4. Limit the first pilot to **one stock and one or two complete trading days**, with no exploratory model fit, fees, returns, or holdout data. Do not publish raw quotes.
5. Regenerate labels for k={1,2,3,5,10} using the arithmetic average of the *next k midpoints* relative to the origin; ±0.002 three-class threshold. Require all targets to be in the same contiguous valid stock/trading-date segment; exclude incomplete windows, stale/locked/one-sided quotes and gap breaks.
6. Run hand-calculated synthetic oracles and report exclusion counts, class composition and sensitivity to gap/threshold choices. Report class proportions as descriptive outcomes, not alpha.

## Prototype in repository

`microstructure/stockday_labels.py` is an **input-independent label construction helper**, not a verified adapter for Quant-Arena Parquet files. It consumes explicit quote records, verifies chronological ordering and stock/date identity, and uses a linear-time rolling midpoint sum. Default >30-second consecutive quote gaps interrupt segments; the 30-second choice is a provisional conservative engineering rule for nominal 15-second sampling, not an empirical market finding. `tests/test_stockday_labels.py` uses only synthetic observations.

**Admission status:** no real Quant-Arena samples have yet been downloaded or processed into the helper, and no real source validation or empirical class ratios can be claimed from this prototype. If selective byte access fails, the next choice is an independently licensed smaller per-stock/day dataset, not a forced 6.23 GB download or unverified mirror.

## Phase A1 implementation — selective source admission, local Parquet adapter

The human lead chose to begin the second option while the original Helsinki custodians' responses remain uncertain.

**Acquisition algorithm:** `microstructure/selective_tar.py` uses HTTP Range requests against the **full immutable publisher Git revision** returned by the Hugging Face metadata API. It requires HTTP 206, exact Content-Range and byte-count matches, valid standard TAR header checksums and an expected release-directory prefix. It scans headers only and skips payloads, then selects the publisher's documentation example stock **000012.SZ** (chosen before seeing any label outcome) plus `manifest.json` and `SHA256SUMS`. Only if the published checksum list identifies a unique file SHA256 does the selective runner extract that **one** Parquet member, verify its SHA256 and reject unexpected size and transfer budgets. Unsupported TAR extensions, HTTP 200 full responses, altered byte ranges and absent manifest hashes **fail closed**. This is a *partial-archive* source-file verification, not a SHA256 verification of the full 6.23GB TAR.

**Deterministic two-day pilot:** `research/run_quant_arena_stockday_once.py` selects the stock's earliest two distinct observed dates chronologically (not the days yielding good predictions). The separate local-only `microstructure/quant_arena_pilot.py` demands Parquet symbol, `available_at`, `source_event_time`, best bid/ask and `stale`/`missing_depth` columns, confirms exchange-local +08:00 timestamps, rejects source event timestamps after availability, and does not sort, fill or resample rows. It treats null quality flags as unusable, uses strict boundary/gap exclusions, runs 1/2/3/5/10-observation midpoint-mean labels and reports **aggregate classes and missing-target reasons only**. It never fits a classifier or infers returns.

**Schema discrepancy:** The Hugging Face dataset card says **45 columns**, while Quant Arena's public benchmark documentation says **44 fields** and references different identity fields. We must inspect the **actual authenticated Parquet schema** before interpreting these data and may need a documented adapter for the true publisher release. Do NOT silently rename or reinterpret fields.

**Provenance and rights:** CC BY-NC 4.0 applies to this second source, and the publisher's release is distinct from FI-2010. `pyarrow==19.0.1` is a research-only import dependency for the one-off job; the repository's synthetic test suite remains standard-library-only. No vendor raw data should enter Git.

**Current stage:** Code and synthetic safeguards are committed. A one-off GitHub Actions job was submitted to attempt remote selective access, but GitHub's Actions runner queue had not started it at the time of this update; **no actual Parquet row or empirical class count has yet been verified**. An HTTP 200, unavailable RANGE service, unexpected manifest structure, or source schema mismatch will be reported as a blocker rather than worked around with unverifiable data. A genuine source result may be reported only after job output and independent test validation.


## A2 — Verified engineering gate and source integrity improvements

Following the user's approval to proceed, the research importer and TAR range parser were strengthened:
- Require an authenticated **full 40-character revision** from the official Hugging Face dataset metadata API, and use that same revision throughout archive range requests. The abbreviated `fa85d7b` history prefix is not accepted as the sole immutable identifier.
- Validate a stock member's SHA-256 against the archive's documented `SHA256SUMS` file rather than guess the structure of `manifest.json`; still require that manifest to be present and syntactically valid. This establishes selected-member integrity against a publisher checksum, **not** the whole-archive checksum.
- Reject unsorted or duplicate source timestamps even after the selected two days and require **actual** booleans for quote quality flags.
- Add synthetic tests for malformed TAR headers, HTTP 200 servers ignoring Range, source-version pinning, checksums, quote timestamps, market-day boundaries and missing-quality flags.

**Confirmed test result:** 92 synthetic unit tests passed on Python 3.11 and 3.12 in [GitHub Actions run 43100635223](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43100635223). The one-time empirical pilot did **not** execute in that run; do not claim a real Quant-Arena file or computed label distribution based on these test results.

The next one-off attempt will be opt-in by a distinctive PR title gate, so ordinary pushes never download a multi-gigabyte market archive automatically.

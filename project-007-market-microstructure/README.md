# Project 007 · Market Microstructure Research Lab

**Status: research foundation only; no licensed market sample audited, prediction fitted, or trading result claimed.** Human-led research with AI-assisted implementation. New draft branch; other projects remain unchanged.

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

## Next checkpoints

1. Confirm applicable source and use rights for research, aggregate publication and GitHub. Do not bypass this gate just because the code can read local files.
2. Perform full-file paired QC and independent spot-checks on authorized sample data.
3. Show descriptive evidence to the human lead for interpretation; finalize horizon and time splits before fitting.
4. Compare constant/majority baseline, imbalance sign, then a simple model only if enough permitted historical days exist.
5. Add latency/fill simulation later, never reporting simulated returns as live results.

Methods: [research protocol](research/PROTOCOL.md) · [human decisions](research/DECISIONS.md) · [rights gate](DATA_RIGHTS.md).

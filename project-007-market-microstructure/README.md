# Project 007 · Market Microstructure Research Lab

**Status: research foundation only; no licensed market sample audited, prediction fitted, or trading result claimed.** Human-led research with AI-assisted implementation. New draft branch; other projects remain unchanged.

## Research objective

Investigate how displayed liquidity and order-flow information relate to subsequent price changes, and whether predictive information remains useful when queue position, fill uncertainty, fees and latency are considered. This project is the first stage of a connected research program: 007 order-book dynamics, 008 inventory-aware market making, and 009 institutional optimal execution.

## What is implemented

A Python standard-library-only streaming audit for local paired LOBSTER message and book CSVs, including exact decimal timestamp parsing, original event order, post-event snapshot alignment, documented fixed-point prices, occupied-level sorting, event-type counts, halt handling, equal-time event preservation, non-destructive locked/crossed quote reports, prefix-only disclosures and SHA256 of both local inputs. Synthetic unit tests check failure handling and basic quantities. The audit does NOT reconstruct the exchange book, produce future price labels, train models or simulate fills.

## Run tests (Python 3.11 or 3.12)

From this project directory:

    python -m unittest discover -s tests -v

## Locally audit files (only if your applicable terms allow this use)

Get paired files directly through the official provider's sample page, not from an unverified mirror. Keep them in a local ignored data folder. The program never downloads data itself. Example for one-level files:

    python -m microstructure --messages data/AMZN_message_1.csv --orderbook data/AMZN_orderbook_1.csv --levels 1 --max-events 10000 --output artifacts/local-audit.json

File names above are placeholders: use the names actually inside the provider package. The output is local metadata, not a published study. Omit max_events from code (or pass None to the Python API) only when independently validating the whole file; the CLI intentionally runs a bounded prefix. A passing prefix is NOT full-file validation. No raw sample, vendor-derived report, or screenshots should be committed pending rights review.

## Next checkpoints

1. Confirm applicable source and use rights for research, aggregate publication and GitHub.
2. Perform full-file paired QC and independent spot-checks on authorized sample data.
3. Show descriptive evidence to the human lead for interpretation; finalize horizon and time splits before fitting.
4. Compare constant/majority baseline, imbalance sign, then a simple model only if enough permitted historical days exist.
5. Add latency/fill simulation later, never reporting simulated returns as live results.

Methods: [research protocol](research/PROTOCOL.md) · [human decisions](research/DECISIONS.md) · [rights gate](DATA_RIGHTS.md).

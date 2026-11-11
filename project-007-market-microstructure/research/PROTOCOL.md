# Preregistered research protocol — Project 007 (proposal, not scored)

## Primary question

Do limit-order-book imbalance features help anticipate subsequent mid-price movement, and does any apparent predictive advantage survive implementation constraints?

## Phase 0: engineering evidence (implemented)

Use original paired CSV rows in file order. Do not sort events, correct invalid quotes, deduplicate identical timestamps, or interpolate missing events. Verify row pairing, schema, nondecreasing time, levels and fixed-point units. Trading-halt messages must duplicate the preceding supplied book; suspend normal quote summaries until a trade-resumption marker. Report anomalous/locked quotes rather than erasing them. One event maps to its post-event snapshot. Audit only; no strategy or profit metrics.

## Phase 1: empirical discovery (blocked pending appropriate data permissions)

Start with the official LOBSTER AMZN one-level sample, June 21, 2012, held locally and never committed. Log official URL, actual file hashes, parsing boundaries, event counts, missingness, halt windows, empty-sided quotes, quote locking, and time ties. Follow with the five-level sample for depth sensitivity if permitted. One day is a demo, NOT a train/test split sufficient to support market-generalizable claims.

## Phase 2: signal definition and falsification (not implemented)

Candidate feature: best-level depth imbalance I_t = (bid_size_t - ask_size_t)/(bid_size_t + ask_size_t), defined only when both are positive and quotes uncrossed. Candidate target: signed change in mid-price after a prespecified later, strictly later timestamp (and report zero/no-change as its own category). Do not label using the snapshot that generated I_t. Separate a pre-registered constant/majority baseline, naive imbalance sign and a simple logistic model. A random IID split is not acceptable; group by trading session, use strict chronological evaluation, embargo at least the prediction horizon, and use day-block uncertainty. If insufficient days are licensed, label all performance exploratory only.

## Phase 3: execution relevance (not implemented)

A separate fill/queue/latency model must be falsifiable. Historical snapshots cannot establish our counterfactual market impact or true queue position. Any simulated profit is simulation output, never realized performance.

## Promotion gates

1. Explicit source provenance, authorized acquisition/use, and separate public-output/redistribution review.
2. Complete paired-file audit and independent spot checks.
3. Human interpretation of initial observations and signed-off time/label/split policy.
4. Only then conduct predictive comparisons and execution experiments; retain all failed hypotheses.

## Known failure modes

Time ties, unequal message/snapshot count, HALT markers, empty-side dummy levels, filtered event ranges, queue-position blindness, fees, latency, spread-crossing, session leakage, overlapping labels and historical-regime shift. Do not use a shuffled event split, deploy a dashboard with invented real-data findings, or convert machine-learning classification accuracy into P&L.

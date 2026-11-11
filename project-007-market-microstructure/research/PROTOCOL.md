# Preregistered research protocol — Project 007 (proposal, not scored)

## Primary question

Do limit-order-book imbalance features help anticipate subsequent mid-price movement, and does any apparent predictive advantage survive implementation constraints?

## Phase 0: engineering evidence (implemented)

Use original paired CSV rows in file order. Do not sort events, correct invalid quotes, deduplicate identical timestamps, or interpolate missing events. Verify row pairing, schema, nondecreasing time, levels and fixed-point units. Trading-halt messages must duplicate the preceding supplied book; suspend normal quote summaries until a trade-resumption marker. Report anomalous/locked quotes rather than erasing them. One event maps to its post-event snapshot. Audit only; no strategy or profit metrics.

## Phase 0B: descriptive diagnostics implementation (synthetic tested; real-data use blocked)

Run a **complete** paired file audit before descriptive windows. In strictly original event order, produce event-weighted 5-minute means of spread (integer price difference / 10,000) and best-level depth imbalance; count eligible, one-sided, crossed/locked and halted event observations, plus *backward-looking* changes in midpoint from the immediately preceding eligible event, resetting state across invalid books and halts. Do not silently fill inactive time buckets. Verify full-file hashes between audit and diagnostics passes. No forward target, P&L, order fill or model fit is in this phase.

## Phase 0C: independent report verification (synthetic tested; real-data use blocked)

Verify a complete descriptive report against the original paired files with an independent CSV decoding and Decimal depth-ratio calculation. Check both SHA256 inputs before and after, overall counts and anomaly categories, each window boundary and event-type frequency, spread, imbalance and backward midpoint changes. Refuse tampered fields and source mutation. This checks arithmetic consistency, **not** correctness of source data, exchange-reconstruction fidelity, market predictability, publication rights, or a successful strategy.

## Phase 1: empirical discovery (blocked pending appropriate data permissions)

Start with the official LOBSTER AMZN one-level sample, June 21, 2012, held locally and never committed. Log official URL, actual file hashes, parsing boundaries, event counts, missingness, halt windows, empty-sided quotes, quote locking, and time ties. Follow with the five-level sample for depth sensitivity if permitted. One day is a demo, NOT a train/test split sufficient to support market-generalizable claims.

## Phase 1C: synthetic-only future-label chronology laboratory (prototype, not approved empirical design)

A standalone in-memory `chronology.py` prototype takes explicitly synthetic post-event snapshots. It proposes a strictly positive **elapsed-time** horizon, and the first subsequent **strictly later timestamp** at or after the elapsed-time threshold as the target; equal-time events remain in event order but cannot be targets. The target is within the same trading session and contiguous eligible active segment. Halts, one-sided/locked/crossed books, and unusable states interrupt the segment. No incomplete future target is inferred or filled; every origin emits a record with either up/down/unchanged or an explicit exclusion reason. The only modeled feature is imbalance computed at the origin, not on the target.

A provisional chronological **session-level** partition function produces disjoint train/embargo/validation/embargo/holdout groups and refuses one-day samples, duplicates and unallocated sessions. The session list must contain actual supported market sessions in empirical work; synthetic calendar days in tests are NOT an exchange calendar. A one-session embargo is a conservative prototype for a within-session elapsed horizon and does not by itself solve all leakage or cross-sectional dependence.

**Crucial:** Neither the candidate horizon, target policy nor split sizes are approved for empirical analysis. They require the human lead's interpretation and sufficient authorized multi-day data. No model fit, prediction score, return series, forecast or backtest is part of this prototype. Seeded synthetic tests include a separately implemented quadratic-search oracle for target selection and a mutation check that future quote changes cannot modify origin features.

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

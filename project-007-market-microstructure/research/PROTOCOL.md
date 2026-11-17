# Project 007 research protocol — engineering prototypes and one historical FI-2010 baseline

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

## Phase 1D: separate FI-2010 benchmark (real, baseline-only evaluation completed)

FI-2010 is a preprocessed ten-day five-stock benchmark, not an event-message reconstruction input. It contains 144 normalized features and five publisher-derived label rows (horizons 1, 2, 3, 5, 10 sampled observations; class 1 up, 2 stationary, 3 down) in a 149-by-N matrix. The anchored-fold convention uses the first k days for training and day k+1 for test. A strictly simple initial baseline reads `Train_Dst_NoAuction_DecPre_CF_7.txt` (days 1–7) and `Test_Dst_NoAuction_DecPre_CF_7.txt` (day 8) only. All rows and numeric labels are validated; output is train-prior constant prediction and day-8 accuracy/macro-F1. Days 9/10 stay reserved and unread. No raw-spread, order-flow, elapsed-time, fill or P&L inference is authorized by normalized features.

The official Fairdata API confirmed **Open / CC BY 4.0** licensing; the DeepLOB researcher-hosted archive was downloaded with a pinned SHA256 and its CF7 train/day-eight files validated. Results: 254,750 training observations; 55,478 day-eight observations; constant class 1 from training; day-eight accuracy 26.20% and macro-F1 0.1384. A **separate raw-ZIP label-row parser** independently verified counts and exact score fractions. Day-nine/day-ten files were never opened. The researcher archive's binary identity with the original Fairdata distribution, and whether publisher-generated training labels overlap the day-eight outcome period, **remain unverified**. See `EMPIRICAL_DAY8.md` and `FI2010_SOURCE_REVIEW.md`.

## Phase 1E: historical source-label construction (real descriptive audit, no model)

After human decision D002 to investigate dataset construction, we inspected the original Ntakaris et al. labeling, normalization and anchored-fold methodology and read **all five publisher label rows** (horizons 1/2/3/5/10) from checksum-pinned train-days-1–7 and day-eight CF7 files. Paper Eq. (8) uses the *average* of the next k mid-prices relative to the origin, with a single ±0.002 threshold for all horizons. We counted an increase of **12.69–19.58 percentage points** in stationary labels on day eight across every horizon. We also reported day-eight equal-*observation-count* quintiles and did not call them stock groups or clock-time bins. Full evidence, limitations and attribution: `CONSTRUCTION_AUDIT.md`.

A changed label distribution does **not** establish a change in market liquidity or a preprocessing error. All published targets are supplied by the data authors; per-stock/day boundaries, upstream scaler fit period and whether last training labels use the following day's outcomes are **not independently certified**. The user has not approved predictive model selection. Days nine and ten remain reserved and unread.

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

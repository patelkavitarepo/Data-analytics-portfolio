# Project 007 — D013 score-stability and selection-denominator audit

**Status: DESIGN FROZEN FOR REVIEW; NO D013 SOURCE RUN, NO NEW TEST EVALUATION, NO MODEL OR CUTOFF CHANGE.** This is an AI-assisted diagnostic follow-up to the negative D012 experiment, not a new independent validation. D012 confirmation outcomes were already inspected, so all analysis of those dates is **retrospective and explanatory**, even if this checklist is written before another provider-data read.

## Question and crucial comparability check

D012 used each stock's 98th-percentile **label-free current/past-eligible** calibration score as a strict alert cutoff. The reported later 6.65% (weighted) / 6.38% (unweighted) alert rates were measured over a **future-label-eligible, past-history-covered** confirmation subset. Thus 2% versus 6% is not, by itself, an exact equal-denominator score-distribution comparison. Future-target eligibility can select particular origins. We must disentangle (a) true score-tail drift in an identically defined decision-time population from (b) changes caused by retrospectively requiring a known target.

**Frozen diagnostic comparison A — genuinely comparable:** calibration versus confirmation, both based strictly on the same source-valid current/depth and five-contiguous-prior-quote eligibility, *without requiring any future target*. Evaluate model scores and cutoff exceedance on this same definition. Only calibration and confirmation dates are compared; do not examine any final date.

**Descriptive comparison B — selection effect:** within already-open confirmation dates only, compare the all-current/past decision-time population to the narrower D012 source-valid and future-target-verifiable matched subset, **without using the target class to alter or tune any decision**. Report numerators and denominators for both. This does not give permission to construct calibration future labels.

## Locked source, model, and calendar

- Existing D012 source: Quant-Arena Public L1 (Quant Arena / LaPlace's Eye / Einsia AI), **CC BY-NC 4.0, noncommercial only, attribution required**, original three already pinned member checksums at publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`.
- Existing immutable manifest: `FRESH_SELECTIVE_DATE_MANIFEST.json`, cohort SHA256 `fe19d601c74f3276e13d8fda3e03ebebcc548bcdb1a2b748138c2d7040d7f3da`.
- Recreate precisely the frozen D012 fit-only logistic pipelines on **Mar 8–Apr 6, 2022** with the same three snapshot features, standardization, target, source validity, three stocks, seed, library-version checks and class weights. Do not fit a novel model.
- Preserve D012 label-blind calibration on **Apr 7–20**, identical 98th-percentile *higher* and strict `score > cutoff` policy; independently verify D012 published per-stock score cutoffs before any reporting.
- Reuse **Apr 21–27** only for score auditing and explanatory aggregate diagnostics. Do not change models, cutoffs, labels, feature rules, securities, or score definition, and do not call it another holdout.
- **DO NOT** access model features, target labels, predictions, score summaries or other price-dependent data from D012 **Apr 28–May 16** sealed dates, D009 **Feb 22–Mar 7** final dates, or FI-2010 reserved dates. Source-member hash verification may read complete bytes and a boundary batch may decompress, but no disallowed row can enter observations. Raw vendor quotes and per-origin scores are never committed.

## Audit outputs fixed before D013 source access

For each frozen model and stock, report calibration and confirmation statistics separately, with **both** date-level and whole-period aggregation:

1. **Population accounting**: total source rows; source-valid current five-level depth; five-prior-history-eligible decision-time rows; future-target-eligible D012 matched confirmation rows; reasons for exclusions. The calibration population is strictly current/past; never compute or inspect its future targets.
2. **Raw score tails**: valid decision-time count, median, p90, p95, p98, p99, maximum of the unchanged `max(p_up,p_down)/(p_stationary+1e-12)` score; frozen cutoff; count/rate of strict exceedances. Calibration and confirmation must use the *same* eligibility definition and score formula. No new quantile cutoff may be issued.
3. **Time and stock concentrations**: each stock/day counts and rates above its *frozen* cutoff; split each day into Shenzhen continuous-auction morning versus afternoon using the existing session policy. Include April 27, 2022 for 000012.SZ as an **already-known exploratory focus** (D012 showed 183/929 matched alerts, not a fresh discovery).
4. **Input-distribution descriptors**: by stock/period/day/session, report aggregate median, p10, p90 and missingness for the original three input features (spread bps, best-level imbalance, five-level imbalance); compare to the unchanged fit-period feature distribution. Quantile differences indicate association, NOT causal attribution. No new predictors.
5. **Decision-time versus labelled-matched selection effect**: for each confirmation stock/day/model, report cutoff exceedance counts/rates on **all decision-time-eligible** origins and on the historical D012 target-verifiable matched subset, and describe their numeric difference. Report target-matching coverage; target values must not be used to optimize anything.
6. **Quality and robustness**: independent recomputation of aggregate counts, source hashes and manifest, sequence/session gating, frozen-cutoff equality, chronology and no calibration-future-label computation. Observations cluster in stock/day and overlap in future horizon; do not compute naive quote-IID significance tests or assert an independently replicated effect from five days.

Disallow any row-level quote, price sequence, learned coefficient of a different model, per-origin predicted probability, post-hoc threshold alternative, model selection or final-date score in the published results. No training/validation/confirmation/final boundaries may move. Both weighted and unweighted models must be reported, even if one looks better.

## Interpretation decision tree

- If decision-time-eligible confirmation exceedance remains well above the calibration exceedance, describe a **score-tail/population shift** for this frozen model under aligned eligibility; examine which stocks, days, sessions and features co-move with it without attributing causality.
- If the aligned exceedance rate is near calibration but the target-verifiable subset exceeds it, treat **future-target selection** as a major contributor to the reported 6% figure. Do not assert score distribution changed substantially until conditional selection is examined.
- If both happen, report both explicitly; do not choose the more favorable explanation.
- If discrepancies appear in hashes, cutoffs or denominators, stop and correct accounting only, not the fitted model or earlier D012 outcomes.

## What would constitute trustworthy future directional alerts?

D013 cannot qualify or rescue either D012 model. A separate future research design would need: an explicitly stated end-user false-positive versus missed-event cost function; a threshold/model fixed **without using the already-open Apr 21–27 results**; reliable precision and recall with clustered day/stock uncertainty; stable alert volume under comparable source-time eligibility across days and stocks; improvement over a simple genuinely forward-dated baseline; and then separate latency, fill, spread, fees, market-impact and P&L evidence before a trading claim. No universal precision percentage is declared sufficient absent this decision context.

**Research stop:** a detected drift explanation alone is not model improvement. Keep both historical final tests untouched, PR #7 draft/unmerged, and all models unpromoted.

## Evidence status

This file is a prospective *audit procedure* for a retrospective/explanatory investigation of already-open development/confirmation dates. There are **no D013 empirical outputs yet**. Any source access must be separately run under temporary, auditable, source-authenticated workflow controls; temporary source-reading infrastructure must be removed afterward. Routine CI stays synthetic-only.

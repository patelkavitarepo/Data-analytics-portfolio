# Project 007 — D014 source-coverage postmortem (after fail-closed first empirical attempt)

**Status: retrospective coverage audit, registered after first D014 empirical run stopped on source eligibility. Not a preregistration of the original 10-day prediction evaluation.**

## Trigger and scientific integrity

The first one-time D014 real-source runner [GitHub Actions run 43275799910](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43275799910) authenticated 000012.SZ and then stopped while processing 000025.SZ: at least one observed source trading date returned zero decision-ready observations under **unchanged** complete-five-level-book and previous-five-contiguous-quote requirements. The exception was `D014 complete observed stock/day has no decision-ready scores`. It happened **before training, model scores or output comparisons were computed**. It did not generate an aggregate D014 result, evaluate any final holdout, select a cutoff or change the protocol.

The D014 rolling method explicitly requires a full 10-observed-day history with >=1 eligible score on **every** day, and must **fail closed** if this condition is unmet. A zero-coverage source day therefore cannot be patched using imputation, forward filling, dropping a poorly covered date, date/stock substitution, loosening quality constraints, or secretly switching to a shorter window.

## Narrow permitted diagnostic

In a separate source-verified ephemeral job:
- Reauthenticate the exact three publisher-verified Quant-Arena Public L1 Parquets, revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`, CC BY-NC 4.0 noncommercial; verify source-day counts and dates against **already-committed** D014 manifest `953b173e4b0ba4b6968ce6113e8345c85e942dbe6b46b31ca722968a98f208c8`.
- Admit only the frozen **20 warmup dates May 17–Jun 14 and 10 confirmation dates Jun 15–28, 2022** for quote/depth features. The earlier D009/D012 reserved tests and new D014 Jun29–Jul12 final remain statistically sealed; old March training data are irrelevant to this audit.
- Count, per stock/day, original source rows, source-valid complete snapshot features, valid past-five-contiguous-quote coverage, their **intersection** (decision ready), invalid/stale-source quote counts, and split by operational continuous session. If any day has zero eligibility, report its literal date and counts. Do not inspect target outcomes to explain source availability.
- **Never construct a future label on either warmup or confirmation**, fit or score any model, calculate a directional alert, choose a threshold or output raw source rows. No probabilistic claims or causal explanations from these counts. The new final date's source timestamps may be decoded in a boundary batch; never convert a final price/depth row to a feature or report.
- Treat an invalid history window as **unavailable** for rolling cutoff evaluation, not permission to modify a rolling-window length or reduce the stock panel. The source-coverage audit is descriptive only and cannot rescue D014 as a successful prediction study.

## Next decision

If no-ready source days occur, D014's preregistered full-panel adaptive-vs-static outcome is **blocked** under the exact rules; retain this as a negative feasibility finding. Plan a **new independent source-coverage-aware methodology** only under a new prospective design, not by modifying D014's first-confirmation criteria after inspection. The dataset's source-quality and sampling limitations should be treated as research findings, not faults to hide.

The original D014 cutoff rules, frozen dates and all sealed-test restrictions remain unchanged. No trading, market making or financial result may be inferred.

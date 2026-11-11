# Research decisions — Project 007

## D001 — November 11, 2026 — Research direction (human supplied)

The human lead chose market microstructure, market making, and execution algorithms, then explicitly selected a research-first approach: small real datasets, a scalable architecture, and rigorous validation.

No direction to trade live, buy subscriptions, merge branches, publish provider data, or declare profitable signals was supplied.

## AI-assisted implementation (not human findings)

The assistant proposed: begin with a streaming paired-message/snapshot schema audit, synthetic checks, local-only inputs, and a separately gated empirical stage. This proposal and its code are AI-assisted, not original human code. The human lead's subsequent interpretation is preserved in D002; it is not attributed to the assistant.

## D002 — November 11, 2026 — Human decision after the first historical baseline

**Actual human lead's direction:** "I would like to investigate the datasets construction."

**Context, not a user-authored causal explanation:** After the train-days-1–7 constant-majority baseline scored 26.20% accuracy on FI-2010 day eight, the lead was asked whether to prioritize genuine market behavior or possible dataset-construction effects in the large stationary-label increase. The lead selected investigating the dataset's construction.

**Authorized next task:** Audit how the publisher's sampling, label thresholds, preprocessing, and chronological folds relate to observed class proportions. Investigate source-label boundary contamination before fitting models. Do not attribute any specific data-construction flaw, market-regime interpretation, or empirical conclusion to the human lead. Do not access days nine and ten.

## Pending human interpretation

Present construction-audit evidence and invite interpretation of the remaining ambiguity. No predictive model selection, testing on reserved days or merger has been approved. AI-generated analysis, code, explanations and hypotheses must remain clearly labeled as assistance.

## D003 — November 11, 2026 — Human request to obtain source quote sequences

**Human directive:** "Alright Holmes lets try to obtain reliable per-stock, per-day mid-price sequences."

**AI-assisted acquisition response:** Prioritize the original five Helsinki securities across June 1–14, 2010 with authenticated stock/date/bid/ask and original sampling semantics. Inspect author, Fairdata, Aalto and Nasdaq HistoricalView sources; do not silently substitute US LOBSTER or a different stock exchange, invent stock/day identifiers, break access restrictions, incur paid costs, or claim FI-2010 original labels independently verified from processed data.

**Current state:** The original per-stock, per-day FI-2010 best-quote series has **not been acquired**. Source paths and open questions are in `research/ORIGINAL_MIDPRICE_SOURCES.md`. Preliminary Aalto/Nasdaq access restrictions apply; a metadata-only official source probe was prepared. Reaching out to custodians requires an externally sent request and any permissions they grant; no message has been sent here.

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

## D004 — November 11, 2026 — Human approval to start separate-source validation

**Human directive:** "Let’s start working on the second option while we wait for the reply."

This refers to a **separate, publicly distributed stock/day order-book quote dataset** (Quant-Arena Public L1) as an independent construction test, NOT evidence to retroactively verify FI-2010 labels or access original Helsinki Nasdaq quotes.

**AI-assisted implementation:** A selective HTTP Range/TAR scanner, a manifest-SHA256-gated single-stock Parquet importer, a source-identifiable two-day quote-label pipeline and synthetic tests have been proposed/committed. Stock `000012.SZ` is chosen in advance because the publisher names it as an example. The first two available source trading days are chosen chronologically, never based on label results. Noncommercial-only CC BY-NC 4.0 source terms are observed; no vendor bytes should be committed.

**Current evidence gate:** No genuine Quant-Arena stock Parquet has been authenticated or analyzed yet. The GitHub workflow is queued, not successful. Do not ascribe the source inspection design, technical assumptions, or future results to the human lead.

## D005 — November 11, 2026 — Human instruction to investigate the cross-stock question

**Human directive:** "Let’s investigate holmes."

The directive follows the discussion of a preregistered **three-stock, five-trading-day label-construction replication** on Quant-Arena Public L1. The human lead did not supply an explanation for the empirical differences, select stocks after seeing data, approve a model, or authorize any trading.

**AI-assisted investigation and outcome:** We followed `NEXT_PANEL_PROTOCOL.md`, selected source-verified stock files 000012.SZ, 000025.SZ, 000031.SZ and the first five observed dates of January 2022. The pinned, CC BY-NC 4.0 noncommercial source panel comprised 15,233 quote observations and yielded different stock-level stationary shares (94.71%, 97.78%, 87.64%) under identical predefined k=5 and ±0.2% labeling. The independent oracle verified 76,165 origin records across five horizons without mismatch. The threshold sensitivity was also performed as preregistered; no prediction model was fitted. See the attributed result and limitations in `THREE_STOCK_PANEL_RESULTS.md`.

**Interpretation limit:** Labels and stock effects both matter descriptively, but causal attribution to market structure, price behavior or data construction remains unresolved. The Shenzhen panel does not validate FI-2010's original Helsinki labels, nor establish trading profitability. PR #7 remains draft, unmerged.

## D006 — November 11, 2026 — Human direction: quote-quality sensitivity

**Human directive:** "Next challenge it is holmes."

In context, this accepts investigating how the three-stock/five-day descriptive labels respond to **missing quotes, stale/missing-depth flags and the existing 30-second maximum gap policy**. The human lead did **not** choose a new preferred data-cleaning policy, prediction model, or trading strategy; nor did they supply a causal explanation.

**AI-assisted protocol:** Before the expanded source-data run, freeze G15/G30/G60/G120 maximum adjacent-quote gaps and F0/FS/FD/FSD source-flag counterfactuals, retaining best-price positivity and ordered-book integrity in every case. All scenarios share the same pinned source revision, three files, first five dates and k=5/±0.2% label definition, and G30/F0 must reproduce the already-published stock counts exactly. Each origin is independently verified by a separate quote-label oracle, and differences in eligible labels and still-eligible classes are reported separately. See `GAP_FLAG_SENSITIVITY_PROTOCOL.md`.

**Boundary:** Ignoring source stale/missing-depth flags is a **diagnostic counterfactual only**, not an approved inference about real executable liquidity. Raw quotes and original flags must not be modified or published. No prediction models, profitability claims, FI-2010 holdout access or merging have been approved.

**AI-assisted empirical result (not human authored):** The predeclared eight-scenario sensitivity study passed on the original pinned three-stock/five-day source: the 15,233 input rows reproduced the strict reference exactly; all tested gap tolerances and missing-depth-only relaxation changed **zero** label assignments, while ignoring stale flags restored **621** formerly excluded labels and changed **zero** class assignments among previously eligible origins. Pooled stationary share shifted from **93.2732%** to **93.4039%** under this explicitly unsafe counterfactual. Stock ranking was unchanged. Two independent label calculators agreed on **121,864** decisions; **105 synthetic unit tests passed** on both Python versions. Full attribution and limits: `GAP_FLAG_SENSITIVITY_RESULTS.md`. Human interpretation and any future predictive-study approval remain pending.

## D007 — November 11, 2026 — Human continuation of gap-boundary inquiry

**Human directive:** "Let’s keep at it Holmes."

This followed the confirmed D006 quote-gap/flag sensitivity and our proposal to examine whether the **fifteen** long within-stock/day gaps correspond to scheduled Shenzhen lunch recesses and whether invalid quotes already block cross-recess labels.

**AI-assisted design (not a human-supplied conclusion):** Freeze the same authenticated Shenzhen stock/date population; enumerate all intervals exceeding 120 seconds; compare their timestamps with a predeclared 11:28–11:30:30 / 12:59–13:02 local-time lunch-window heuristic, and investigate whether strict quality flags versus a deliberately *unsafe* no-gap counterfactual produce any label windows across them. Strict k=5, ±0.2%, same-stock/day 30-second baseline and publisher SHA256s must reproduce exactly. Independent second label implementation must confirm all scenarios. All rules are in `GAP_BOUNDARY_PROTOCOL.md`, recorded before the new market-data run.

**Caveat:** Lunch-time alignment is evidence of a scheduled nontrading break, not proof that other missing data are absent. No request to trade, fit predictive models, open FI-2010 reserved days, or merge PR #7 was made.

**Independent AI-assisted result, not a human conclusion:** The same three publisher-SHA256-pinned stock files and five sessions were re-examined. All **15** original >120-second source gaps were **exactly 11:30:00–13:00:00 local, 5,400 seconds each**, consistent with Shenzhen's scheduled lunch closure. Neither source quote at any gap edge was stale, missing-depth or price-invalid. With original strict 30-second continuity, **zero** target windows crossed lunch; deliberately removing the time-gap limit created **74** artificial across-lunch labels with source flags respected, or **75** with both flags ignored. Previously eligible labels did not change class. **45,699** original-source origin checks agreed with the independent quote oracle, zero mismatches; **110 synthetic tests passed** on Python 3.11/3.12. See `GAP_BOUNDARY_RESULTS.md` for attribution, exact count reconciliation and scientific limits. This supports explicit session segmentation before any future predictive work.

## D008 — November 11, 2026 — Human direction to implement session-aware labels

**Human directive:** "On to the next Holmes."

Context: after verification that the original strict gap safeguard blocked **74** false retrospective targets spanning a scheduled 90-minute Shenzhen lunch closure, the next proposed step was to implement **explicit session-aware labels** and lay out a genuinely chronological predictive-study protocol. The lead did **not** provide a causal price explanation, authorize deployment or order a predictive model to be fit.

**AI-assisted work, frozen before fresh source access:** `research/SESSION_AWARE_PROTOCOL.md` defines operational morning 09:30–11:30 and afternoon 13:00–15:00 exchange-local (+08) source partitions. All source-valid future midpoint targets must remain within their own stock/date/morning-or-afternoon segment, with 30-second max gap, strict source quality flags, k=5 future-midpoint average and ±0.2% class thresholds. Out-of-session source quotes must not generate labels; closing call auction 14:57–15:00 remains a distinct microstructure phase and is flagged as a limitation. The old generator and its prior empirical receipts are preserved. Both optimized and separately implemented slow oracle versions are synthetic-tested. One-shot real-source reproducibility and sensitivity job may only read the **same** SHA256-verified three stock files and first five already inspected source dates.

**Next-stage design only:** `research/CHRONOLOGICAL_PREDICTION_PROTOCOL.md` outlines prospective 20/5/10 common-date train/validation/sealed-holdout partitions **after the already examined five days**, training-only baseline metrics and strong leakage controls. This is **not authorization to open later prices or fit or test models**. The D008 real-data session audit and human interpretation are required first.

**D008 empirical result (AI-assisted, not human-authored):** The same three authenticated Quant-Arena Public L1 files and **15,233** observed source quote rows were checked. Explicit morning/afternoon segmentation generated **13,736 eligible / 12,812 stationary** labels at k=5 and ±0.2%, exactly matching the frozen strict legacy count and all eligible class assignments. **909** source rows (303 per stock) were outside the new operational regular-session windows, but **all were already excluded** from labels by the strict legacy calculation; their reason became explicit `outside_session` rather than `invalid_or_stale_quote`. Turning off the numeric max-gap safeguard under the *new session-aware policy* produced **zero** across-lunch targets (contrasting with D007's **74** on the non-session-aware no-gap stress). Independent source quote oracle checked **30,466 origin/target/exclusion records**, zero mismatches; **121 synthetic tests passed** on Python 3.11 and 3.12. Full analysis: `research/SESSION_AWARE_RESULTS.md`. No future-date source prices opened, no predictive model fitted or tested, and PR #7 remains draft/unmerged.

## D009 — November 11, 2026 — Human authorization for chronological baseline phase

**Human directive:** "Let’s get it Holmes."

This followed the successful D008 session-aware label verification and the proposal for a first **genuinely chronological, noncommercial** baseline prediction experiment, with 20 training dates, 5 validation dates, and 10 sealed final-test dates after the already inspected five-day discovery period. The human did **not** select a model by observed performance, permit live trading, authorize merging or release the final holdout.

**Pre-price preregistration, AI-assisted:** The amendments in `CHRONOLOGICAL_PREDICTION_PROTOCOL.md` were committed before any D009 training/validation market-price access. The SZSE closing call auction (14:57–15:00) is excluded from this first continuous-trading prediction population; 09:30–11:30 and 13:00–14:57 are separate continuous operational segments. At k=5, ±0.2%, session and 30-second gap boundaries remain strict. B0 is training-only global majority (tie preference 2 > 1 > 3). B1 is a deterministic backward-looking origin-vs-mean-previous-five midpoint heuristic with the same ±0.2% threshold and abstention when five earlier valid contiguous quotes are unavailable. Scores are fixed three-class macro-F1, balanced accuracy, accuracy, confusion, coverage, by-stock/day and matched-coverage B0-vs-B1 comparison. There is no model tuning or use of validation labels to select a prediction rule.

**Source manifest frozen before model prices:** Three exact SHA256-verified Quant-Arena Public L1 Parquet members were inspected for **availability timestamps only**, confirming 484 shared observed dates; `CHRONOLOGICAL_SPLIT_MANIFEST.json` was committed with split SHA256 `50d134f5b85c18c38423d974fbdb3376a105870211b95377a3aec22f73a870d6` and metadata-only source evidence. Train January 11–February 14 (20 observed common dates), validation February 15–21 (5 observed common dates), sealed final test February 22–March 7 (10 observed common dates), all in 2022. The earlier Jan 4–10 discovery dates are **not** new holdout data. Data access remains noncommercial CC BY-NC 4.0.

**Holdout invariant:** The entire stock member must be downloaded to verify publisher SHA256; the Parquet row-batch reader may physically decode some post-validation rows at a batch boundary, but none are admitted into features, labels, fitting or scoring. We therefore claim *statistical evaluation isolation*, not cryptographic/byte-level nonaccess to final-holdout prices. Final ten days are not to be evaluated in this phase. One-off CI must be removed after execution and PR #7 stays draft.

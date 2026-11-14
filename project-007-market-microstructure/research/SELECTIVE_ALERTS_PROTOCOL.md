# Project 007 — D012 frozen selective-alert study (NEW chronological cohort)

**Registered November 12, 2026 before looking at any D012 post-March-7 quote prices; successfully executed without changing model/alert/date rules.** Verified findings: [SELECTIVE_ALERTS_RESULTS.md](SELECTIVE_ALERTS_RESULTS.md). Human direction: "let’s get that bread" after D011 repeated the severe direction-alert false-positive failure. AI-assisted design, not a promise of trading profits. This is a **new independent chronological development cohort**, not a retest of D009's validation or the 10-day legacy sealed block.

## Critical time-ordering decision

Our D009 legacy future test was February 22–March 7, 2022, and remains **unscored**. A model fitted on source days **after March 7** must never be evaluated on that *earlier* block as though it were future out-of-sample performance. D012 therefore **retires that earlier block as a possible D012 final test**, preserves it unscored for the D009 research lineage, and preregisters a **NEW downstream 10-date sealed test** after D012 model fitting, score-cutoff calibration and first confirmation. No results in this project prove any trading edge.

## Source, date-only selection, and no-peeking

- Original noncommercial [Quant-Arena Public L1](https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1) (Quant Arena / LaPlace's Eye / Einsia AI), **CC BY-NC 4.0 with attribution**; immutable publisher revision `fa85d7b95e56e81317ac349f52e916ca482f0f68`, exact original SHA256-verified `000012.SZ.parquet`, `000025.SZ.parquet`, `000031.SZ.parquet`. No stock substitution.
- Before seeing *any* D012 quote price/volume/quality/label, read **only source `available_at` timestamps** for all three members; find their sorted intersection of observed stock trading dates **strictly greater than 2022-03-07**. Freeze the **first 45** available post-legacy dates and commit their canonical SHA256 manifest before new data analysis. Require **20 fit + next 10 score-cutoff calibration + next 5 one-time confirmation + next 10 NEW sealed final**. Never substitute source dates based on performance, source class mix, or quality.
- The earlier D009 legacy test (Feb 22–Mar 7) remains unscored for any D012 procedure. D009 previously inspected discovery/train/validation dates and D010/D011 fit comparisons are *prior methodological work*, not data admitted into D012 model fitting or score-threshold calibration.
- Whole per-stock Parquet members must be downloaded for publisher SHA256; a Parquet record batch may physically decompress some later rows, but **only D012 first 35-date fit/calibration/confirmation rows** may be converted into quote features and labels. D012 final ten days are **not** admitted to model calculations. This is statistical evaluation isolation, *not cryptographic/byte-level secrecy*. The 10-date sealed final remains reserved pending a separate final-design decision.

## Frozen dataset and labels

- Source availability must be UTC+08. Current source event timestamp `<=available_at` and `stale=False, missing_depth=False`. Original `k=5` mean of next five same-stock/day/phase valid midpoint labels, ±0.002 class thresholds (up=1, stationary=2, down=3), 30-second max quote gap. Continuous auction morning 09:30–11:30 inclusive; afternoon 13:00–14:57 exclusive (closing call excluded). No cross-phase, stock/date, invalid quote or gap labeling.
- Features only at decision availability: spread bps clipped at 100, top-level bid/ask displayed volume imbalance, sum first-five-level bid/ask imbalance, requiring complete valid 5-level price/volume ladders. These are *snapshot* measures, not live order-flow or queue-position measurements. No future quote, future label, or completed-day aggregate may enter a model feature.
- Training only: use 20 fit dates to fit a global `StandardScaler` and **exactly two** three-class scikit-learn 1.6.1 `LogisticRegression(C=1.0, solver='lbfgs', max_iter=400, random_state=7007)`, one `class_weight='balanced'` (W) and one `class_weight=None` (U). All nonmissing target-eligible book-feature rows used for fitting. No grid search, per-stock models, feature expansion or coefficient selection.

## Frozen alert control (no calibration labels)

- Read the next 10 **calibration dates' current/prior quotes only** for the 3-source-feature vector and valid **five-prior-quote history**; **DO NOT compute or inspect the next-five-target class labels on calibration dates**.
- For each of two fit-only models, compute its 3-class `predict_proba` scores `(p_up,p_stationary,p_down)`. These model probabilities **are not independently calibrated empirical probabilities** and must never be described as such.
- Define the directional score `s=max(p_up,p_down)/(p_stationary+1e-12)` and a directional sign determined by `p_up>=p_down -> up`, else down; ties assigned up. Fixed one operating budget: **2% per stock**, with score cutoff equal to the *98th percentile*, method `higher`, of that stock's 10-date calibration scores over **current-source-valid and five-prior-history-valid** rows. Use `score > cutoff` to prevent >2% alerts on a fully tied score mass (ties may cause zero alerts). Source feature/availability controls, not future label availability, decide calibration eligibility. No calibration labels, no precision-based threshold optimization, no hand-adjustments after looking at outcomes.
- At confirmation time (the next 5 frozen dates), issue an up/down **alert** only when the current quote satisfies source quality / historical feature coverage and its directional score strictly exceeds the *already frozen stock-specific* cutoff; otherwise issue **no directional alert** (represented as class-2 for classification metrics, *not* a verified claim the quote is stationary). The decision never uses subsequent quotes or complete-day ranks. A target-eligible subset is used only for retrospective scoring.
- Two selectors (W vs U) have the identical **2% calibration alert budget** but may produce different alert counts in confirmation under temporal drift. Neither model is selected or promoted from this single confirmation.

## Registered scoring and red flags

On the **identical confirmation sample** of source/current-book-valid, B1 historical-quote-covered and next-five-target-eligible quote origins, report, pooled and per stock/day:
- Number of rows with a verifiable future label; source exclusions; matched coverage. **Directional alerts**, alert rate per 1,000 matched, true directional alerts, false alerts (all wrong alert direction, including up↔down), false alerts per 1,000, precision among predicted up/down, up/down recall, and 3-class confusion, macro-F1, balanced accuracy, accuracy.
- B0 fit-date majority and unchanged B1 past-only trend on exactly the same matched origins for fair descriptive comparison; B0 makes zero directional alerts if stationary majority. Warning: on this highly stationary label population, even a 2% budget can yield a poor directional precision; **do not claim any economic profitability**.
- Calibration counts and cutoff scores **by stock and model**, learned without target labels; no target labels on calibration dates may be evaluated. A 2% alert *calibration budget* is NOT an upper bound on confirmation alert rates. No naive IID significance: future-target windows overlap; securities and trading days cluster.
- No model or cutoff modification after seeing confirmation, no repeat scoring of held-out dates. If either model catches zero direction labels, report no useful detection rather than broadening budget or choosing another cutoff.

## Gate and artifacts

1. Freeze this protocol, implement code and synthetic tests (date/quote isolation, cutoff ties, no calibration-label access, sequential scoring, no future features).
2. Authenticate source for date-only inventory, freeze and **commit** D012 cohort manifest before access to new market-price/volume records.
3. Single source-verified train/calibration/confirmation CI run only; commit aggregate evidence and source licence. No provider row-level quotes, price sequences, vendor Parquet members, per-origin predictions or unlicensed data in GitHub. Remove temporary download job after success.
4. Preserve existing Project 007 PR #7 **draft and unmerged**. No trading, strategy deployment, reserved FI-2010 labels, or evaluation of either legacy or D012 new final holdout.

**Scientific stop condition:** A selective directional alert model must demonstrate high-enough precision across stocks and dates in a separately planned genuinely later final evaluation before practical use is contemplated. Improving alert frequency alone or reducing alerts via a deterministic budget is not evidence of predictive skill.

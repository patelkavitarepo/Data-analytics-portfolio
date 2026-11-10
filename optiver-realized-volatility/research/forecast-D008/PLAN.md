# D008 proposed experiment: Daily Stock Volatility Prediction and Model Failure Analysis

**Status: awaiting lead approval before model implementation.** The lead chose
the scope and retained Plotly. The explicit methods below are AI recommendations,
not additional human decisions or empirical forecasting findings. No model has
been fitted for this plan. Advanced reference selection/CVR weighting stays future work.

## Financial question and forecast timing

At the close of session t, can a simple stock-specific forecast improve on recent
historical volatility for the stock's **next five trading sessions**, and does
adding observed broad-market information help? Where do the forecasts fail?
An improvement is not presumed and is not a claim about trading profitability.
Daily close-to-close variation is not intraday realized volatility.

The target remains D002/D003's provisional definition:

```text
r_i,t = log(close_i,t / close_i,t-1)
y_i,t = sqrt(r_i,t+1^2 + ... + r_i,t+5^2)
```

Require five valid successive exchange-session returns (six closes), respecting
approved action-boundary and observation masks. No centering, annualization,
imputation, invented prices, new magnitude clipping or automatic anomaly removal.
Compute labels anew after loading **only** 2013–2015 return columns; never read the
existing precomputed future-target columns. Require target end no later than
December 31, 2015. Thus the last five origin sessions cannot receive labels here.

## Three deliberately limited comparisons

| Model | Specification | Purpose |
| --- | --- | --- |
| M0: historical volatility | `sqrt((5/20) * sum(last 20 observed squared daily returns through t))` | Parameter-free persistence baseline in the same five-session units |
| M1: stock-specific | Separate regularized linear regression (Ridge) per stock, predicting log positive five-session volatility | Learn stock-specific behavior without a large model search |
| M2: stock + market | Same per-stock Ridge family and own features, plus a small fixed set of broad-market features | Test incremental market information without selecting individual reference stocks |

Own features proposed for both learned models: volatility over the last 5, 20 and
60 sessions expressed in five-session units; today's signed log return;
cumulative signed log returns over 5/20 sessions; and the last 20 sessions'
downside share of squared returns. This last fraction is unavailable if its
denominator is zero, rather than assigned a made-up neutral value. These seven
inputs are fixed before examining forecast scores. No price-level, external news,
intraday, peer-CVR, future-label or retrospectively selected event feature.

Market features proposed: today's focal-excluded median signed donor return,
median absolute donor return, fraction down at least 1%, and trailing 20-session
variation of the focal-excluded median-return series. Use eligible conservative
donors in **both** response-policy experiments and exclude the focal stock.
Require at least 250 contemporaneous donors, following D004's disclosed operational
coverage guard. Never select donors based on future survival/relationship results.
The underlying vendor universe still has unresolved survivorship limitations.

All features stop at today's close. Complete required lookbacks and finite inputs
are mandatory; unavailable inputs produce an unavailable model forecast, not
imputation. Report lost coverage. A baseline using only 20 sessions may cover more
dates; show that coverage separately from the common comparison.

Proposed minimum fit support is **126 complete, matured training origins per
stock** (a practical roughly six-month guard, not proof of 126 independent samples
or a reference-reliability threshold). Do not fit tiny histories just to show more
stocks. Publish which stocks/origins fail this requirement and all coverage losses.
Establish headline stock eligibility using only pre-2015 training availability
under both policies, not stocks' subsequent performance or survival.

Standardize features using training-only means/scales. Compare the same small
Ridge strength grid `[0.1, 1, 10, 100]` for M1 and M2. Select one shared strength
per model family from 2014 internal tuning, not a separately optimized strength
for every stock. This controls the size of the search while coefficients remain
stock-specific. Train on log(y) for y>0 and exponentiate predictions, giving positive
forecasts. These are log-scale forecasts, not asserted unbiased means of y.

Preserve genuine zero targets: exclude them from log-target fitting and undefined
percentage-error calculations, disclose their counts, and include them in MAE/RMSE
where a forecast is available. Do not add an arbitrary epsilon. The positive learned
forecast cannot exactly represent zero; report that limitation. Missing targets
are never confused with zero targets.

## Chronological development and internal evaluation

1. **2013 through first-half 2014:** initial estimation history after feature warmup.
2. **2014 Q3 and Q4:** expanding chronological tuning folds. In each fold, training
   origins and their entire five-session labels must end **before** the first
   validation origin. Fit scaling and Ridge on that training slice only. Select
   strengths from the combined held-out tuning errors, with the declared metric.
   **Tuning labels must also finish before the first 2015 evaluation origin:**
   drop late-December tuning origins whose five-session outcomes extend into 2015.
3. **2015 Q1–Q4:** freeze features, strength choices and reporting rules before
   examining these forecasting scores. Refit once before each quarter using only
   then-observed, matured past labels. Earlier quarters' matured observations may
   enter later training, but their forecast errors cannot trigger retuning.
4. **2016–2018:** load no relationship observations, target columns or model scores.
   No forecasts/evaluation there until separate human approval.

The strict purge is `training target_end < first validation origin`; a nominal
calendar split of origin dates alone is insufficient. Features need no centered
windows or full-sample normalization. Do not randomly shuffle stock-date rows.
Historical cleaning remains retrospective: leakage-safe features/splits do not
make the original feed or future-informed QC flags certified real-time information.

**2015 is internal discovery evaluation, not a pristine unseen test.** Prior
D001–D006 descriptive work inspected 2013–2015. Keeping the forecasting plan fixed
before scores helps, but does not erase that knowledge. No final generalization
claim precedes the separately approved reserved-period evaluation.

## Metrics, cleaning comparison and uncertainty

- Primary: pooled **RMSPE on positive targets**, consistent with the original
  Optiver evaluation idea. Percentage errors heavily weight quiet targets; that
  is a disclosed metric property, not a reason to hide those observations.
- Secondary: MAE/RMSE in unannualized five-session volatility units, signed bias,
  baseline-relative improvement/worsening, and stock-balanced summaries. Report
  counts, quarter-level results and per-stock distributions alongside pooled values.
- Run the full experiment separately for narrow/conservative masks, retaining the
  same source and market donor policy. Headline comparison uses common eligible
  stock/origin/target observations across the three models and two policies.
  Also show each policy's available sample and the baseline's wider coverage;
  a smaller error on a smaller/easier sample is not automatically improvement.
- Report paired loss-difference uncertainty using whole-calendar blocks with all
  stocks resampled jointly. Proposed 20-session blocks with 60-session sensitivity
  are descriptive conventions, not a certified confidence guarantee. Examine all
  five non-overlapping-origin offsets as an overlap sensitivity, never choose the
  best offset. Five-session targets overlap, and hundreds of stocks on one day
  do not constitute hundreds of independent market episodes.
- No reference-stock ranking, reliability score, causal claim or requirement that
  M1/M2 outperform M0. Report worse performance and inconclusive comparisons.

## Failure analysis and finished-project deliverables

Inspect large **absolute** errors separately from large **relative** errors.
Compare under/overprediction, current broad-market declines versus other
conditions, prior volatility, stocks, quarters and masking coverage. Attribute a
failure to a data problem or economic event only with evidence; otherwise mark
the explanation unresolved. A future shock can be a retrospective explanation,
never an input supposedly available earlier. Preserve large errors and genuine
extremes; do not revise cleaning after looking at scores to flatter a model.

Produce versioned out-of-sample predictions and fit/feature/target provenance,
complete eligibility/exclusion reasons and a failure-case ledger. Automated tests
must cover target timing, quarter purging, training-only transformations, no
protected-period/target-column reads, positive forecasts, zero/missing handling,
  tuning-label maturity before 2015, common-sample comparisons and reproducibility.

After approval, implement these comparisons, test/debug, document results honestly
and build a Streamlit review dashboard with stock/date/model/policy filters,
predicted-versus-actual charts, baseline comparisons, coverage and failure cases.
Keep the original Optiver tools and all D001–D006 evidence accessible. Do not
overwrite the frozen foundation or modify Project 001. Present findings for lead
interpretation and review; no merge or reserved-period evaluation without approval.

**Approval requested now:** this limited three-model experiment and leakage controls.
This document is a proposal, not permission to start fitting models.

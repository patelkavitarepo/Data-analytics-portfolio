# Draft research protocol — AI recommendations, not human decisions

Status: data access blocked; no observations inspected. D001 records the human
hypothesis. Every methodological choice below is a recommendation for discussion,
not a completed experiment or an approved research decision.

## Financial problem

A market maker needs a near-term estimate of how much prices may move when
setting quotes, managing inventory, or limiting exposure. A model that treats all
stocks identically may miss stock-specific fragility; an entirely separate model
may have too little information about rare conditions. The research question is
whether selective sharing helps forecast the next 10-minute realized volatility
beyond what each stock's own observed history and a common market state provide.
No claim about improved trading P&L follows from a lower forecast error alone.

The hypothesis has at least three separable components:

1. Stocks have reproducible differences in baseline behavior or sensitivities.
2. Some relationships depend on observed conditions, rather than being constant.
3. Those conditional relationships improve held-out prediction after controlling
   for own recent volatility, shared market movements, and model complexity.

Evidence for 1 or 2 does not establish 3. Shared response can be explained by
common shocks, selection, changing measurement frequency, or normalization.

## What official documentation establishes (not empirical findings)

The data dictionary describes anonymized stock/window identifiers, top-two-level
order-book observations and aggregated executed trades. The official host Q&A
states that stocks share aligned windows: observed information covers the first
10 minutes and the target covers the next 10 minutes, without feature/target
overlap. `time_id` is a join key with shuffled chronology. These statements still
need schema and coverage checks against authorized local files. Sources are in
SOURCES.md; no published competitor scores or stock relationships inform our
experimental choices.

## Observable measurements and financial interpretations

For best bid b, best ask a, and displayed quantities qb, qa:

| Family | Measurement | What it could indicate | Important qualification |
| --- | --- | --- | --- |
| Liquidity cost | `(a-b)/((a+b)/2)`; mean, time-weighted mean, upper quantile | Higher cost of immediacy | Relative spread, not unnormalized cents or execution cost |
| Displayed liquidity | `qb1+qa1+qb2+qa2`; within-stock percentiles | Thin quoted depth | Only two levels; does not measure hidden liquidity or full impact |
| Pressure | `(qb-qa)/(qb+qa)`; signed and absolute versions | Asymmetric displayed supply/demand | Direction is distinct from magnitude; not a causal measure |
| Activity | book observations, inter-update gaps, observed coverage | Quote activity or sparse sampling | Data represent recorded seconds, not every individual message |
| Trading | summed shares, summed order_count, shares/order | Executed trading intensity and typical size | Prices are normalized: do not call price × size real dollar turnover |
| Price variation | midpoint and weighted-price realized volatility | Recent observed uncertainty | Event-sampled RV depends on observation frequency and microstructure noise |
| Late variation | RV of returns with both endpoints in last 120 seconds | Recent acceleration candidate | Compare with an equal-length earlier segment; not raw full-vs-short RV |
| Tail movement | largest absolute midpoint log return | Jump-like movements | A proxy, not proof of a news shock or a formal jump test |
| Market context | leave-one-stock-out median standardized spread, depth, RV | Broad liquidity/volatility state | The donor panel must be available at inference; not an external stress index |

The price used for WAP1 is `(b*qa + a*qb)/(qb+qa)`. For prices P, observed-window
RV is `sqrt(sum((log(P_t/P_(t-1)))**2))`, with returns reset inside each
stock/window. It is neither sample standard deviation nor annualized volatility.
No return connects separate `time_id` values. Zero total depth leaves WAP
undefined; the code never bridges gaps with fabricated WAP returns. Fewer than two
valid prices leaves RV undefined, not zero. Relative spreads make prices more
comparable, but share depth/activity still need stock-specific normalization.

The initial code includes both event-average and duration-weighted spread/depth.
Duration weighting assumes a recorded quote persists until the next update,
including the last quote through second 600; it does not backfill before the first
quote. This is an explicit measurement assumption to check against official data
semantics. The pipeline reports coverage and zero-depth counts and refuses
inconsistent books or duplicate stock/window/second records rather than silently
“cleaning” them. Missing trade records mean no recorded trades, not certainty of
market inactivity. No missing first book second is automatically treated as an
error, because host discussions document such cases.

## Initial exploration, after access and split approval

1. **Audit** file hashes, schemas, duplicate keys, missing fields, coverage by
   stock/window, quote consistency, zero depth, and timing gaps. Stop and discuss
   material anomalies. Do not silently exclude difficult stocks.
2. **Protect confirmation data before viewing charts:** choose a discovery set of
   whole `time_id` groups using identifiers only, record its manifest and decision
   ID, and reserve the remaining groups. The allocation is not yet chosen.
3. **Stock profiles:** on discovery windows only, show medians/IQRs and distributions
   of RV, spread, depth, imbalance, and activity. Compare both raw and stock-relative
   levels. Show coverage and missingness alongside every ranking. Raw differences
   may reflect exposure to different windows, so repeat on common windows.
4. **Conditional reactions:** after the lead defines the context and meaning of
   reaction, compare each stock's within-stock response shift between ordinary and
   stressed observations. Candidate responses are observed RV or future-target
   residuals from an own-stock baseline; they answer different questions. The
   latter uses discovery/training labels only and needs out-of-fold residuals.
5. Plot all-pair conditional similarity heatmaps **with sample counts** rather than
   showing only attractive pairs. Compare ordinary/high-context states, confidence
   intervals, and within-training discovery/replication subsets. Look for stability
   beyond a single threshold. No threshold, peers, or top-k have been selected yet.
6. Present the actual plots, measurement assumptions, and support counts in plain
   English. Ask the lead to interpret the evidence before offering AI interpretation.

The implemented initial command intentionally reads no target values. It produces
stock profiles and descriptive spread-versus-observed-RV charts. It does not
implement regime estimation, neighbor selection, or predictive training. The
conditional-similarity utility accepts explicitly supplied discovery context IDs
and returns correlation plus matched-window counts; it never chooses a context
or the best pair. This is a measurement tool, not a test of forecast improvement.

## Fair comparisons to propose after the first interpretation

Keep identical outer windows, own-stock features, tuning opportunities, and metrics.
For small stock samples, discuss shrinkage toward a pooled model explicitly.

| Comparison | Information available | What it tests |
| --- | --- | --- |
| Persistence | Own observed-window RV | Whether any learned model beats the simplest forecast |
| Individual | One model per stock; only own features | Stock-specific behavior without borrowed observations |
| Pooled-own | Shared training across stocks, own features, stock identity | Parameter sharing without other-stock inference inputs |
| Market-shared | Pooled-own plus leave-one-out market aggregates | Broad common conditions, without selected peers |
| Static peers | Same base plus fixed training-selected peers | Whether selective sharing helps without context gating |
| Context-aware | Same base plus context-specific training-selected peers or response weights | Increment beyond static peers and broad market state |
| Capacity control | Similarly complex own-only model and shuffled/random peers | Whether gain is simply flexibility or generic market information |

Start with simple regularized regressions (e.g. log-volatility with carefully
assessed retransformation) and/or modest tree models. Advanced boosting or gated
models come only after interpretation and lead approval. No model is trained now.

Two distinct “historical similarity” definitions deserve a lead decision:
feature-window reaction profiles avoid labels but may not predict the future;
training-only future-volatility response/residual profiles directly address the
target but require more careful nested estimation. Neither should be passed off
as the only possible interpretation of D001.

## Leakage-resistant test design to discuss

- Group every stock observation sharing `time_id` into the same split. Random
  stock/window row splitting lets the same event contaminate fit and validation.
- Use an untouched outer confirmation set and nested, group-aware inner validation.
  Fit stock scales, imputation, stress cutoffs, residual models, graph/peer selection,
  context gates, feature selection, and hyperparameters on training groups only.
  Refit the entire relationship-learning process inside each inner split.
- Historical neighbor labels and target encodings cannot be looked up for the
  current validation time_id. Training-row target encodings/residuals must be
  cross-fitted by whole time groups to avoid self-label feedback.
- At inference, only the feature-window inputs may be used. Other stocks' same-window
  features can be available under a batch-panel assumption; their targets cannot.
  Label this as a panel inference assumption and test missing/delayed peers. Current
  features may be aggregated using training-fitted scales; never refit on the full
  validation distribution, even without targets, for an inductive comparison.
- Standardize within stock using training-only quantities. Use a leave-one-out
  market context to reduce mechanical self-conditioning. Compare full-panel and
  restricted-panel settings; acknowledge selection bias from missing stocks.
- Do not infer chronological lags from numerical time_id order. Calendar dates,
  day boundaries, sectors, true prices, and chronological adjacency are not supplied.
  A grouped random-window score is an event-held-out experiment, **not** proof of
  future chronological robustness. Unknown adjacency/dependence cannot be fully
  purged or embargoed without reliable chronology; repeated grouped folds do not
  solve that limitation. Do not reconstruct identifiers from hidden price/tick
  artifacts as the primary research method.
- Same observed time windows across stocks induce a market factor. Correlations of
  raw RV can be high merely because all stocks were volatile together. Compare
  within-stock standardized changes and training-cross-fitted market/own-baseline
  residuals; do not infer contagion, causality, or stable sector links from correlation.
- Conditional subsets can be tiny and threshold searches create multiple-testing
  bias. Report support and uncertainty, limit the search in advance, compare to
  randomized controls, and confirm directions in held-out groups. Apparent changes
  in conditional correlation can arise from range restriction or conditioning on a
  shared outcome; stress must be defined from observed predictors, not target RV.

## Evidence of predictive usefulness (not yet computed)

Primary score: RMSPE = `sqrt(mean(((target-prediction)/target)**2))`. It weights
small targets heavily. Audit positive targets, reject invalid values explicitly,
and report error by target size, stock, observed context, coverage, and peer availability.
Do not hide large absolute-error cases behind a good percentage score. Positive
prediction handling and any transformations must be fixed before confirmation.

Compare paired squared percentage errors on the **same** outer stock/window rows,
aggregate by time_id, then quantify uncertainty with a time-group bootstrap as an
approximation (unknown serial dependence remains). Report both global RMSPE and
per-stock scores; the mean of stock RMSPEs is a different estimand. Predefine what
improvement is material. Model/seed variation, costs, instability, and non-improving
stocks matter. Ablations remove peer features or gating while holding everything
else comparable. Improved forecasting would support an incremental predictive
claim on this dataset, not prove causal shared vulnerability or a profitable strategy.

A null/negative result is useful: it may challenge the hypothesis, show insufficient
support, reveal noisy proxies, or show that own RV/common state already contains
the usable signal. Distinguish these possibilities through planned controls; do not
rename failure as success or move thresholds after viewing confirmation outcomes.

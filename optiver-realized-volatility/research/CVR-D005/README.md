# D005: Conditional Vulnerability Ratio — methodology for approval

**Status: proposed methods, not an implemented relationship-scoring system.**
The lead interpreted D004 cautiously and proposed CVR. That contribution is in
[DECISIONS.md](../DECISIONS.md#d005--2026-11-09--lead-interpretation-and-cvr-research-objective).
This document is AI-assisted mathematical investigation and recommendations.
No stock CVRs, new pair rankings, later-period relationship statistics or
predictive models have been calculated for this proposal. No approval is assumed.

The original question remains whether stocks have different vulnerabilities and
whether context-specific relationships can eventually improve forecasting beyond
own-stock and broad-market information. Dependence is only one step toward that
question; neither association nor replication proves predictive usefulness.

## 1. What the proposed ratio measures

Fix a market condition M and a **single paired eligible sample**: dates with a
known stress state for both A and C, valid historical baselines, and known M.
Let N be its size, nA and nC the stress counts, and n11 the joint-stress count.
Then, provided nA and nC are positive:

```text
pA = P(SA=1 | M), pC = P(SC=1 | M), p11 = P(SA=1, SC=1 | M)
CVR(A,C | M) = p11 / (pA * pC) = N*n11 / (nA*nC)
```

Thus **CVR(A,C | M) = CVR(C,A | M)**. The formula is conditional lift, also
historically called interest in association-rule research, rather than a new
directional dependence statistic [1]. The lead's proposed financial application
and research hypothesis are recorded as human contributions; mathematical novelty
is not claimed. Computing its two directions using different missing-data samples
or different focal-exclusion contexts could create spurious asymmetry.

- CVR=1 means the two binary states factorize in this sample/condition. Values
  above one indicate excess co-stress; below one indicate less co-stress. A sample
  estimate near one does not prove population independence or absence of other
  nonlinear relationships between the original continuous measurements.
- Its feasible range is `max(0,pA+pC-1)/(pA*pC)` to `1/max(pA,pC)`.
  Common stress states have a lower upper limit; rare states allow very large
  ratios. A fixed rule such as “CVR above two is strong” is inappropriate.
- If either marginal has no stress events, the estimate is **undefined**, not zero
  or one. No epsilon is silently added. Zero joint events with positive marginals
  yield an estimate of zero, but do not establish impossibility of future co-stress.
- Self-references are excluded: CVR(A,A)=1/pA. Same-issuer share classes are a known
  linkage/control, not evidence of independent cross-stock vulnerability discovery.
- The baseline pA includes dates when C is stressed. It is not an independent
  control group. Numerator and denominator must be estimated and resampled jointly.

Always show the entire two-by-two count table and directional companions:

| Companion | Use | Limitation |
| --- | --- | --- |
| P(A stressed given C stressed, M) | Probability relevant to using C as A's reference | Can be high solely because A is often stressed in M |
| P(A stressed given C not stressed, M) | Explicit comparison group | Undefined if no C-nonstress dates; still observational |
| Difference between those probabilities | Absolute percentage-point separation | Depends on stress definition and baseline rate |
| Ratio of those probabilities | Directional relative comparison | Unstable or infinite with a zero comparison rate |
| pA, pC, n11, all four counts and eligible N | Makes base rates and support visible | Counts of days are not counts of independent events |

**Synthetic example, not market findings:** on 50 dates, A is stressed 10 times,
C five times and both twice. CVR is two in either direction. But P(A|C)=40%
and P(C|A)=20%. Equal CVR does not imply equal usefulness as a reference.

## 2. Defining stress without future normal behavior

Proposed primary measurement is the absolute daily log return, `x_it=|r_it|`.
For session t, estimate an own-stock quantile from the **preceding H exchange
sessions, ending t-1**, then define `S_it = 1{x_it > Q_q(past x_i)}`. Use strict
exceedance with a documented quantile interpolation convention. No log-floor is
needed, which avoids D004's floor sensitivity; threshold crossings introduce
their own sensitivity and discard movement magnitudes.

The threshold is available before t; the state and through-close market context
are available only after t's close, subject to feed/quality limitations. This is
an end-of-day description, not an intraday warning. No full-sample ranking,
future centered windows, future target or stock's eventual sample maximum enters
the historical normal. Observed zero returns stay zero; missing values are unknown,
not nonstress. Flag degenerate/zero quantiles and quantile ties explicitly.

**Candidates for review, not adopted defaults:** q=0.90 versus 0.95 and H=60 versus
252 sessions. These represent a frequency-versus-extremity and adaptive-versus-
stable-baseline tradeoff, not numbers chosen to reproduce old pairs. For example,
a 95th percentile from 60 observations is informed by only about three upper-tail
observations. Minimum historical coverage and tail precision must be justified
before pair selection; D004's 40/60 guard is not automatically adequate here.
Use all past market states for own normal behavior, rather than a tiny history
consisting only of past decline dates. Conditional stress frequency need not equal
1-q during declines or in a nonstationary series.

Planned alternatives should be few and declared before results:

- Downside return magnitude: isolates losses, changing the economic question from
  large movement in either direction. Do not quietly equate these definitions.
- Own-history-normalized `log(high/low)`: captures intraday range, misses overnight
  jumps, requires OHLC eligibility and inherits adjustment/record limitations.
- Backward-looking five-session `sqrt(sum(r^2))`, ending t: measures sustained
  variation but creates overlapping states and additional serial dependence.
  This is different from the future five-session forecast target.

For an ordinary-versus-decline comparison, estimate CVR separately in the existing
near-flat ordinary condition and in declines, with identical stress definitions.
The difference or log-ratio of those CVRs is a context-specificity diagnostic,
with uncertainty, not a requirement that ordinary relationships be absent.

## 3. Separating broad stress from stock-specific information

Propose retaining D004's disclosed decline rule initially: at least 60% of at
least 250 eligible conservative donors fall at least 1% at the close. Exclude
**both** A and C from the common context and use that same context for both
marginals and both masking policies. No future-day market condition is available
as an input to a later forecast. This numerical rule remains a reviewable AI
choice, not a new human-approved stress definition.

Conditioning on a broad decline does **not** remove varying market severity,
heterogeneous market exposures, sector news or selection effects. A concrete
synthetic counterexample illustrates the issue:

| Severity stratum | Dates | A stress | C stress | Joint stress | Within-stratum CVR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mild | 1,000 | 100 | 100 | 10 | 1.00 |
| Severe | 1,000 | 800 | 800 | 640 | 1.00 |
| Pooled | 2,000 | 900 | 900 | 650 | **1.605** |

Both stocks are independent **within each stratum**, yet the pooled ratio
suggests excess co-stress because both react more in severe conditions. These
are invented mathematical counts, explicitly not estimates from our dataset.

A companion severity-standardized joint ratio is
`observed p11 / sum_s(w_s * pA_s * pC_s)`, with common paired stratum weights.
It equals one in this example. It has a different estimand from the original CVR;
report both, not a silent replacement. Use only predeclared observed donor-return
and donor-variation summaries; learn any cut points from discovery only. More
strata reduce confounding but make sparse cells worse. With 50 decline dates,
finely partitioned conditional independence is unlikely to be identifiable.
No causal adjustment or complete removal of common factors is claimed.

## 4. Possible reliability measures

Recommend an **evidence profile with explicit gates**, not arbitrary weights
collapsed into a score. All measures below are proposed, not implemented results.

| Dimension | Measure/check | Advantage | Weakness |
| --- | --- | --- | --- |
| Strength | CVR, directional probabilities, absolute probability difference; uncertainty | Separates relative association from absolute relevance | Binary thresholds lose severity information; rare events destabilize ratios |
| Evidence amount | Four counts, historical coverage, C-stress and co-stress dates, distinct contributing episodes | Shows what actually supports the claim | No universal count establishes sufficient information |
| Episode consistency | Per-episode tables, leave-one-episode-out effect range, largest episode's fraction of co-stress | Exposes a relationship driven by one crisis | Small episodes often cannot estimate their own CVR; blocks may remain dependent |
| Uncertainty | Joint episode/block resampling of the full table; interval width and undefined-replicate rate | Preserves within-block dependence better than independent-day resampling | Few blocks, nonstationarity and zero cells can defeat interval calibration |
| Measurement sensitivity | Fixed small grid of historical horizons, quantiles and economically different proxies | Makes operational-definition dependence visible | Requiring every proxy to agree confuses different risks; searching for a winning proxy overfits |
| Cleaning reliability | Both policies on own eligible dates and on common dates; evidence causes for supporting events | Separates observation loss from changes in stress classification | Missingness may depend on stress; common dates can still be a selected sample |
| Market explanation | Severity-stratified companion and ordinary/decline comparison | Challenges apparent relationships explained by market composition | Sparse support and unobserved exposures remain |
| Persistence | Frozen later-period replication with rolling past-only thresholds | Tests temporal transport rather than rediscovering the pair | Regime change, reduced power and previous full-source QC limit interpretation |

### Episode dependence, weighting and uncertainty

D004 observed **50 reference-calendar decline dates in 28 blocks**, not 50
independent crises; example pairs had 47–48 usable decline dates. These are
previous discovery counts, not new CVR findings. If each stock happened to be
stressed on 10% of 50 decline dates, independence would imply only 0.5 joint
events on average. That calculation is illustrative; the actual conditional
rates are unknown and may be much higher.

The user's probability formula naturally samples an eligible **day**. Keep this
as primary, and use equal-episode-weighted probabilities as a separately labeled
sensitivity. Long crises then receive less weight, changing the estimand. Do not
average unstable/undefined episode-specific CVRs or discard zero-event episodes.
Define episode boundaries from market conditions and calendar gaps before pair
inspection. D004's five-session grouping is a convention, not proof of independence.
Report contributing episodes and leave-one-out influence without pretending that
each episode individually has enough data to pass a significance test.

Block methods for dependent observations have established statistical foundations
under suitable assumptions [2]. Propose resampling whole temporal blocks/episodes,
all stocks together, preserving the joint state table and recomputing marginals.
Report sensitivity to a prespecified block convention. A block bootstrap does
not automatically give valid uncertainty in this short, nonstationary panel.
If precomputed states are resampled, uncertainty is conditional on the historical
threshold path; recomputing adaptive thresholds requires coherent chronology,
not shuffling sessions and pretending they form authentic prior histories.

Never silently discard resamples with undefined ratios. Report their frequency
and withhold a reliable interval when identification fails. If observed co-stress
is zero, a naive nonparametric bootstrap cannot manufacture unseen events and can
give a misleading zero-width interval. Independent-day binomial/Fisher calculations
can be sensitivity illustrations, not default valid financial inference.
Any Bayesian/pseudocount alternative must disclose its prior and prior sensitivity;
it cannot turn absent observations into empirical evidence. Circular shifts or
block permutations require credible conditional exchangeability; they may destroy
the common severity pattern that the null must preserve.

### Many pairs and earlier selection

D004 scanned 119,316 supported pairs and its 1,583 screen passes are selected
discovery outputs. They cannot be presented as independently predeclared CVR
discoveries. Either preregister a small, economically justified new candidate
family or treat a full CVR scan as exploratory with the complete tested family
and all selection variants disclosed. Keep fixed controls, including same-issuer
controls, separately identified.

Dependence-robust false discovery rate procedures, such as Benjamini–Yekutieli,
are possible but conservative [3]. **They require valid marginal p-values**:
adjustment does not repair invalid independent-day tests, repeated peeking or
an undisclosed search over definitions. Family-wise control with a joint maximum
statistic is an alternative only if a defensible joint null resampling scheme
exists. Without credible calibration, show descriptive uncertainty and withhold
“statistically confirmed” claims. Later replication must freeze the candidate
family and address its multiplicity rather than testing only successful pairs
until something passes.

## 5. Proposed evidence categories — no numerical gate adopted

Separate evidence sufficiency from its **direction** (positive, null-compatible,
negative or conflicting). Reliable evidence against positive association should
not be mislabeled as a weak positive relationship.

| Category for a positive reference-stock claim | Proposed interpretation |
| --- | --- |
| Insufficient evidence | Undefined quantities, too few informative episodes/events, uninformative intervals or material unresolved data support problems prevent a reliable assessment |
| Weak/provisional evidence | Estimable positive association is unconfirmed, imprecise, episode-dependent, measurement-sensitive or cleaning-sensitive; no forecasting reliance |
| Strong evidence of positive conditional association | Meaningful positive effect with defensible multiplicity-aware uncertainty, adequate precision and episode support, no single-block dependence, planned robustness checks and frozen later-period replication |

Strong association still does not mean causal or useful for forecasting. The
strong label is unavailable before later replication. Robust null/negative
evidence is reported explicitly and does not qualify a positive reference.

No “CVR above X,” minimum number of episodes, agreement percentage or weighted
reliability score is chosen to favor the previous examples. Before a final system,
the lead must approve the practical absolute effect worth pursuing, acceptable
uncertainty/error budget and what definition changes are materially different.
A conventional 95% interval is an option, not a magic reliability boundary.
Discovery-only power/precision calculations can show what the data could resolve;
they cannot supply the economic value judgment or justify tuning gates to pairs.
“Insufficient evidence” is an acceptable outcome of this dataset.

## 6. Cleaning, timing and evidence ledger

Keep the immutable source and D003 masks. Compare narrow and conservative
estimates using (a) each policy's available observations, (b) the common-date
intersection, and (c) counts of state flips on common dates due to different
historical quantiles. The last comparison matters even if today's return matches.
Report lost/retained stress events, coverage by stock/date/severity and episode,
and supporting-event cause IDs. Do not classify zero close changes as errors,
clip genuine extremes, invent prices or select the policy producing a higher CVR.

The estimand is conditional on **paired eligibility**. Missing not at random can
hide or exaggerate co-stress; intersection agreement cannot prove absence of bias.
Report differences, do not claim that conservative means correct. Retrospective
quality decisions must retain their evidence-availability time. D003's first-copy
repeated-record flags can require a later session; broader action/news information
also may not be available at the original close. An eventual real-time claim needs
an as-of quality reconstruction or explicitly retrospective scope. Neither
rolling quantiles nor a time split repairs a future-informed input mask.

## 7. Approval sequence and untouched later relationship period

1. **Now:** review this mathematical proposal; no final scoring or new pair results.
2. **If approved:** discovery-only feasibility work on 2013–2015. Audit possible
   stress definitions' historical coverage, event/episode counts and attainable
   precision without promoting/ranking pairs. Present the feasibility evidence
   and ask the lead to approve the operational definition and evidence gates.
3. Lock a versioned protocol: history/quantile, coverage convention, market context,
   episode definition, measures, candidate family, uncertainty/null assumptions,
   meaningful effect/precision, multiplicity, missingness and decision rules.
   Only then implement discovery relationship assessment. Record every deviation.
4. Freeze discovery candidates and rules before examining **2016–2018 relationship
   outcomes**. Conduct a separately approved one-time later replication. Past
   observed validation-period returns may update an already specified rolling
   historical quantile; future observations never do. At each date the candidate
   choice must have been available then. Do not retune after a failed replication.

The later period is preserved for relationship validation, not entirely untouched
data: earlier integrity work already inspected the whole source and constructed
retrospective masks. D004 used discovery only. No later-period relationships are
inspected for D005. The limited 2013–2018 source, changing stock membership,
survivorship, unresolved adjustment history and daily-only observations limit
transport to new market eras and prevent order-book/liquidity claims.

Same-time CVR does not establish a warning signal. A later, separately approved
experiment could compare `P(A future stress | C observed today, M today)` with
own-state/market baselines. That would be directional in time and is **not** the
same estimand as CVR here. Future five-session labels must mature before relationship
estimation at each origin, and overlapping train/validation labels must be purged.
Only a later authorized forecasting experiment can determine incremental utility
against own-stock-plus-market models. No predictive training is authorized now.

## Verification and sources

[verify_algebra.py](verify_algebra.py) reads no datasets, imports no project
analysis modules, trains nothing and produces no relationship scores. It checks
45,415 small synthetic contingency tables with positive marginals for symmetry,
the probability bounds and the equivalent count formula, plus the two explicitly
synthetic examples above. [math-checks.json](math-checks.json) records the actual
run. This validates algebra and examples, not empirical CVR reliability.

Run from this folder with Python 3.11/3.12:

```bash
python verify_algebra.py > /tmp/cvr-math-checks.json
diff -u math-checks.json /tmp/cvr-math-checks.json
```

1. Brin, Motwani, Ullman and Tsur (1997),
   [Dynamic Itemset Counting and Implication Rules for Market Basket Data](https://sigmodrecord.org/?download_id=7867&smd_process_download=1),
   especially the discussion of interest/co-occurrence versus directional measures.
   DOI: [10.1145/253260.253325](https://doi.org/10.1145/253260.253325).
2. Künsch (1989),
   [The Jackknife and the Bootstrap for General Stationary Observations](https://doi.org/10.1214/aos/1176347265).
   The stationary dependent-data setting motivates blocks; it does not certify
   our selected market episodes or finite-sample intervals.
3. Benjamini and Yekutieli (2001),
   [The control of the false discovery rate in multiple testing under dependency](https://cris.tau.ac.il/en/publications/the-control-of-the-false-discovery-rate-in-multiple-testing-under/),
   DOI: [10.1214/aos/1013699998](https://doi.org/10.1214/aos/1013699998).
   Dependence assumptions and the conservative general-dependence modification
   matter. No numerical false-discovery guarantee is claimed for this proposal.

Sources consulted for the methodological investigation. Their results are not
evidence that our stock pairs are related. Mathematical deductions, proposed
financial definitions and evidence categories are AI assistance for lead approval.

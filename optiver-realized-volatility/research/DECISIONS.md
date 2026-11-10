# Research decisions — lead researcher contributions

Only choices and interpretations actually supplied by the human lead belong in
this log. AI recommendations live in PROTOCOL.md and are not approvals.

## D001 — 2026-11-09 — Research direction (human supplied)

**Status:** established by the lead researcher.

**Hypothesis, in the lead's words:**

> Volatility forecasting models may perform better when they learn the individual
> vulnerabilities of each stock and selectively use information from other stocks
> that have historically responded similarly under specific market conditions.
>
> I believe that two stocks don’t need to behave similarly all the time to be
> meaningfully related. They may instead share vulnerabilities under particular
> circumstances.

**Research questions authorized by the lead:** identify observable stress,
liquidity, trading activity, and volatility indicators; investigate stock-specific
behavior and conditional similarities; design individual/shared/context-aware
comparisons; audit leakage, anonymization, and shuffled-window limitations.

**Constraints supplied by the lead:** do not presume the hypothesis is true;
never select relationships using validation future outcomes; show actual-data EDA
and charts before complex training; request the lead's interpretation before AI
interpretation; ask one meaningful question at a time; preserve Project 001 and
require approval before merging.

**Authorship:** the hypothesis, direction, research priorities, and collaboration
constraints above are human contributions. Code, tests, and draft methods in this
branch are AI-generated assistance, reviewed through Git. They are not represented
as code manually written by the lead.

## Initial pending questions — historical D001 checkpoint

- Authorized access route for official competition files.
- Discovery/confirmation window allocation and split approval.
- Operational definition of market stress/context.
- Meaning of “similar reaction” to prioritize.
- Which model comparisons, uncertainty standard, and minimum effect matter.
- Interpretation of empirical charts, model results, or final conclusions.

At that initial checkpoint, no empirical findings, stock relationships, or model
gains had been observed. Subsequent entries supersede those pending items only
where the lead actually supplied a decision.
Do not fill these entries retrospectively as if the lead had chosen them earlier.

## D002 — 2026-11-09 — Daily-data pilot approval (human supplied)

**Status:** approved by the lead. The Plotly `all_stocks_5yr.csv` dataset is the
foundation for a research pilot. The original D001 hypothesis remains unchanged:
stock-specific vulnerabilities and condition-dependent information sharing are
the research focus. This is a daily-frequency adaptation, not an Optiver dataset
replication. The official-Optiver-access question above is superseded for this
pilot; it is not retroactively recorded as resolved access to Kaggle.

**Provisional approval:** forecast volatility over five trading sessions, subject
to reviewing initial analysis. No final target transformation or split boundaries
have been approved.

**Authorized next step:** independently write/test data-integrity investigation
code; investigate missingness, OHLC contradictions, unusual moves and corporate
actions; distinguish verified corrections, unresolved anomalies and legitimate
unusual behavior; quantify possible cleaning-rule effects; explain target timing
and chronological validation; present evidence for review.

**Approval still required:** cleaning methodology before training any prediction
models. Do not automatically remove extreme observations, invent replacement
prices, modify Project 001, or merge without approval. No cleaning policy or
empirical interpretation in the report is attributed to the lead.


## D003 — 2026-11-09 — Provisional masking implementation (human supplied)

**Status:** the lead approved the proposed masking-and-evidence-ledger cleaning
methodology, subject to the conditions in this entry. D001's research hypothesis
and D002's provisional five-session horizon remain unchanged.

**Authorized work:** preserve the original data; implement masks rather than
deletions/replacements; distinguish confirmed record errors, suspicious records,
genuine moves and unresolved cases; maintain a complete reason/evidence ledger;
compare conservative masking with a narrower strongly-supported-error policy;
measure effects by stock, date and observed market conditions; distinguish
retrospective QC knowledge from prediction-time availability; implement/test and
document independently. Preserve genuine unusual market behavior.

**Explicit boundary:** no predictive model training and no merge. Present cleaning
results, limitations and the next proposed experiment for the lead's review.

**Not yet chosen by the lead:** the next economic context, definition of reaction,
primary forecasting policy versus sensitivity policy, learned model, date split
boundaries, or interpretation of the selection-bias audit. Technical definitions
of the comparison policies are AI implementation choices disclosed in the
cleaning report, not falsely attributed as separately specified human decisions.

## D004 — 2026-11-09 — Broad market declines first (human supplied)

The lead chose **broad market declines** as the first descriptive experiment.
Reasoning supplied by the lead: stocks with different normal behavior may share
vulnerabilities during particular stressful market conditions, and the existence
of those relationships should be investigated before prediction models.

Authorized comparisons: ordinary versus declining-market behavior, transparent
conditions without future observations, conditional changes in volatility,
separation of common-market response from stock-specific relationships, narrow
versus conservative masking/coverage, and plain-English evidence with charts.
Do not treat similar reactions as prediction or causation. Present evidence and
ask for the lead's interpretation **before AI conclusions**. No training or merge;
Project 001 remains unchanged.

The hypothesis in D001 remains unchanged. The operational thresholds, discovery
cutoff, measurements and support guards in `declines-D004/design.json` are disclosed
AI analytical choices fixed before inspecting this experiment's results, not
additional parameters falsely attributed to the lead. They are reviewable and
subject to the lead's interpretation and subsequent decisions.

## D005 — 2026-11-09 — Lead interpretation and CVR research objective

**Human interpretation of D004:**

> I believe the apparent relationships between stocks should be considered
> cautiously and investigated further before they influence forecasting decisions.
>
> A high correlation alone does not convince me that two stocks are meaningfully
> related. The sensitivity to different measurements, market episodes, and
> data-cleaning policies suggests that we need a way to evaluate the reliability
> of relationships.

**Human-supplied next objective:** develop a measurable, evidence-based method for
determining when another stock could be a potential reference stock. Investigate
the proposed Conditional Vulnerability Ratio:

`CVR(A,C) = P(A stressed | C stressed, market condition) / P(A stressed | market condition)`.

The lead requires own-history stress definitions using information available at
the observation time; conditional strength; consistency across episodes;
measurement and masking sensitivity; evidence quantity/quality; and persistence
in later unseen periods. Distinguish strong, weak and insufficient evidence.
Do not tune arbitrary thresholds or weights to make earlier examples reliable.
Preserve later-period data for independent validation. D001 remains unchanged.

**Authorized now:** mathematical feasibility research, possible reliability
measures, advantages/weaknesses, and a proposed methodology for review.

**Approval boundary:** ask the lead to approve methodology before implementing a
final relationship-scoring system. No predictive model training, Project 001
changes or merge. Future incremental forecasting comparisons are an eventual
objective, not present training authorization.

The draft in `CVR-D005/README.md` is AI analytical assistance. Its stress quantiles,
history lengths, evidence criteria, uncertainty methods and validation procedures
are proposals, **not human-approved parameters or findings**. No approval of those
proposals, interpretation of new results, or final relationship is recorded here.

## D006 — 2026-11-10 UTC — D005 methodology and feasibility approval

The lead approved the D005 evidence-profile methodology and discovery-only
feasibility phase. The ultimate human objective is a context-aware volatility
forecasting model that evaluates multiple reference stocks, compares reliability,
recognizes overlapping information and can decline to use unreliable relationships.
The original D001 hypothesis is preserved; this is not a requirement to find peers.

Authorized now: assess independent stress support, historical-window/stress-definition
comparisons without selecting strong-looking associations, precision, uncertainty,
episode dependence, market-severity explanations, retrospective cleaning and uneven
coverage. Explain what evidence is attainable and what additional data would be
needed if support is insufficient. Distinguish simultaneous co-stress from future
predictive information. Do not weaken standards to obtain results.

Explicit boundaries: preserve 2016–2018 relationship outcomes; do not inspect them,
train models, rank reference stocks, invent numerical reliability gates or weighted
scores, or merge. Ask for lead approval before final relationship criteria.

The fixed feasibility grid and diagnostics in `feasibility-D006/design.json` are
AI implementation choices implementing this approval, not parameters independently
chosen by the lead. Results and recommendations are recorded in
`feasibility-D006/README.md` and IMPLEMENTATION.md, never as human conclusions
or approvals.

## D007 — 2026-11-10 UTC — Seek longer auditable discovery history

**Status:** temporarily stopped/superseded as the current priority by D008 below.
No new dataset was selected. Source probes and incomplete implementation are
retained as paused work, not substituted for the approved Plotly foundation.

The lead approved seeking a longer, auditable **pre-2016** discovery dataset.
Human reasoning: existing data has too few independent stressful episodes to
reliably distinguish stock relationships from coincidence, shared market behavior
or data-quality problems; a larger dataset is not automatically better evidence.

Authorized: research public historical sources extending substantially before
2013, preferably multiple market cycles; prioritize direct cloud downloads without
competition access/private credentials; verify small downloads; compare coverage,
stocks, accuracy, actions/adjustments, historical membership, delistings, licensing
and reproducibility; investigate distinct stress support, consistent replacement
versus integration, and a defensible smaller scope if no suitable source exists.

Preserve Plotly, D001–D006, their ledgers and the human decisions. Do not inspect
2016–2018 relationship results, train models, calculate new stock relationships,
select final reliability thresholds, change Project 001 or merge. The lead will
make the final dataset-selection decision. Access probes and AI recommendations
are not dataset adoption or additional human approval.

## D008 — 2026-11-10 UTC — Complete a limited Plotly forecasting project

**Human decision:** freeze D001–D006 as the exploratory foundation and temporarily
stop seeking an expanded dataset. Prioritize **Daily Stock Volatility Prediction
and Model Failure Analysis** using the existing Plotly source. The advanced
context-aware multi-stock vulnerability model is a future extension, not a
requirement for this first completed project. D001 is preserved, not rejected.

**Human-requested comparisons:** a reproducible five-trading-session experiment,
historical-volatility baseline, stock-specific model, and a model incorporating
own-stock plus broad-market information. Use appropriate forecasting metrics and
chronological validation, investigate largest errors, compare both approved
masking policies, and report failures or worse-than-baseline performance honestly.

**Authorized immediately:** preserve the foundation, stop the source search,
prepare a concise experiment/leakage-prevention plan for approval. After the plan
is approved, handle implementation, testing, debugging and documentation
independently with progress explanations. This entry does **not** record approval
of the AI-proposed dates, features, Ridge models or numerical implementation
settings in `forecast-D008/PLAN.md`.

**Explicit boundaries:** development and internal validation only in 2013–2015;
2016–2018 remains for later separately approved evaluation. No complex reference
selection, CVR weighting or additional architecture now. Do not delete previous
work, change Project 001 or merge. **Present the plan and ask for approval before
implementing models.**

The frozen completed foundation is commit
`db4d868a46e7436afcfb41668fcf229a7860d978`, to be tagged
`research-d001-d006-freeze`. Subsequent logs are append-only research chronology;
no earlier finding is rewritten to support a forecasting result.

## D009 — 2026-11-10 UTC — Approve D008 implementation and metric-disagreement analysis

The lead approved the D008 three-model experiment and chronological validation
plan and authorized full implementation, testing, training, failure analysis,
documentation and an interactive Streamlit dashboard. Do not stop at another plan.

Additional human requirement: investigate disagreements between RMSPE and
absolute-error metrics, especially when actual volatility is very small. Do not
silently exclude difficult observations or change metrics to improve results.
Present actual results, comparisons and failure cases in plain English before
making conclusions; preserve human interpretation and research ownership.

Keep exactly the approved historical-volatility, stock-specific and stock-plus-
market models. No additional architectures, scoring systems or dataset searches.
Preserve the frozen D001–D006 foundation, advanced hypothesis and reserved
2016–2018 evaluation period. Project 001 stays unchanged; PR #2 stays unmerged.
Implementation settings are recorded before training in
`forecast-D008/design.json`; no future model score or conclusion is attributed
to the lead in this decision entry.

## D010 — 2026-11-10 — Human interpretation of D008 and future questions

**Status:** interpretation supplied by the lead after reviewing D008; possible
explanations are hypotheses, **not confirmed causes or new experiment approvals**.

**The lead's interpretation, in their words:**

> I believe two possible factors may explain why the learned models perform worse
> during extreme volatility.
>
> First, the training data may not contain enough diverse examples of extreme
> market conditions for the models to learn reliable patterns.
>
> Second, the models may not be interpreting historical volatility information
> effectively under unfamiliar conditions. The simpler baseline may be more
> robust in those situations, even though the advanced models already have access
> to similar historical information.
>
> I would eventually like to investigate both possibilities, including whether a
> model could recognize unfamiliar market conditions and adjust how much it relies
> on the historical-volatility baseline.
>
> However, I recognize these explanations are hypotheses, not proven causes.

**The lead's requested performance description:**

> I also believe a model must be described honestly according to its demonstrated
> performance. We should acknowledge that the current models improve overall
> internal forecasting accuracy but perform worse during the highest-volatility
> outcomes.

**Human-supplied future research questions:**

1. Would a greater diversity of extreme market conditions provide useful training
   evidence, rather than merely a larger number of observations?
2. Are the learned models using the historical-volatility information they already
   possess effectively when conditions differ from their training experience?
3. Could a model recognize unfamiliar conditions and adjust its reliance on the
   historical-volatility baseline?

These preserve the lead's questions, not an AI finding that any proposed cause
has been established or an improvement would work. The confirmed empirical
comparisons remain the bounded 2015 internal-evaluation results in
`forecast-D008/RESULTS.md`, including metric disagreements, highest-outcome-band
failures, uncertainty and retrospective-data limitations. They do not establish
which explanation caused those failures or guarantee future performance.

**Authorization now:** record this interpretation and retain the questions for
future review. **No new model, retraining or access to the reserved 2016–2018
evaluation period without further lead approval.** D001–D006, their frozen
evidence and the original advanced hypothesis remain preserved. No merge.


## D011 — 2026-11-10 — Lead authorizes publication as version 1.0

**Human direction:** “Yeah let’s publish what we came up with and then we can continue to work on this slowly over time. We can publish this as version 1.0.”

The lead approved publishing the completed, bounded Project 002 study as **version 1.0** and continuing research incrementally in future versions. The published scope remains the approved three-model daily-volatility experiment and its honest failure analysis. The advanced conditional-vulnerability/reference-stock framework remains future work, not a v1.0 result. Do not represent untested 2016–2018 results as evaluated or the internal 2015 scores as live performance. Release scope and limitations are recorded in `RELEASE_NOTES_v1.0.md`. Public Streamlit deployment is a separate step from publishing the repository and must be confirmed before claiming a live website.

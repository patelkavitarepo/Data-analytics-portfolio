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

## Pending — no decision has been recorded

- Authorized access route for official competition files.
- Discovery/confirmation window allocation and split approval.
- Operational definition of market stress/context.
- Meaning of “similar reaction” to prioritize.
- Which model comparisons, uncertainty standard, and minimum effect matter.
- Interpretation of empirical charts, model results, or final conclusions.

No empirical findings, stock relationships, or model gains have yet been observed.
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

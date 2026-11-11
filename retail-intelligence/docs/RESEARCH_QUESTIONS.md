# Research log — Project 003

## R001 — What is a valid sales transaction?

**Status:** partially investigated; raw overlap verified, business classification still open.

- A row represents a line item, not necessarily a distinct order or customer.
- UCI documents `C`-prefixed invoice codes as cancellations.
- Initial investigation: [negative quantity findings](NEGATIVE_QUANTITY_FINDINGS.md) — 19,493 negative C-prefixed lines, 3,457 negative non-C lines, and one positive C-prefixed line.
- All 3,457 negative non-C rows have zero unit price, missing customer ID, and UK country; 2,689 lack product description. Possible internal adjustments are a **hypothesis**, not an established label.
- Further investigate refunds, non-merchandise codes, invoice-level groups, zero-priced lines, and duplicate records.
- Do not define revenue solely as `Quantity * UnitPrice` without explaining exclusions, cancellations, and the monetary meaning of the resulting figure.

## R001e — Do annual source worksheets overlap?

**Status:** confirmed in Investigation 007; downstream handling policy pending.

- Both yearly worksheets contain **22,523 identical source-line copies** across **1,088 wholly matching shared invoice IDs**, all from December 2010. [Source and method](ANNUAL_SHEET_OVERLAP.md).
- The 64 extra candidate-line instances from counting across source sheets are cross-sheet exact copies; their repeated presence is not evidence of separate operational transactions.
- A hypothetical positive-quantity, positive-price line total would include **£438,852.65** twice without cross-sheet reconciliation. This is *not* certified revenue.
- **Follow-up completed (Case 008):** [reversible analysis-layer proposal](REVERSIBLE_ANALYSIS_LAYER.md) was implemented and tested on the original workbook, with one retained candidate row per exact cross-sheet shared copy and full original-row provenance. Both **22,523** canonical links and **1,044,848** candidate lines reconciled independently with Case 007. The policy remains **proposed, not approved**; no source rows were modified.
- **Next:** separately decide whether to adopt the candidate view for exploratory KPIs, and define positive-price, cancellations, postage, fees, and other transaction types before any final revenue or order-count metric.

## R009 — What belongs in an exploratory gross transaction metric?

**Status:** experimental source-verified scenarios S0/S1/S2 completed; definitions not approved.

- [Revenue scenario sensitivity](REVENUE_SCENARIOS.md) measures reversible-candidate gross line amounts of £20,533,741.92 (S0 broad), £20,063,792.35 (S1 excluding exact postage/billing code candidates), and £19,723,764.52 (S2 also excluding uncertain manual/discount codes).
- The 19,165 candidate C-prefixed lines are treated separately from gross line amounts; cancellation-coded signed amounts are not verified refunds.
- Do not call any scenario recognized revenue, profit, cash inflow, or finalized sales. Retain row provenance and avoid deletion.
- **Manual M reviewed (Case 010):** See [source-verified M findings](MANUAL_CODE_FINDINGS.md). **861** M positive-priced lines totaling £339,629.94 span standalone and mixed invoices; exclusions remain unapproved.
- **Next:** Case 011 reviewed high-value manual charges and provisional C-negative linkages; see [strict linkage findings](MANUAL_LINKAGE_FINDINGS.md). Zero/negative-price audits and final business definitions remain open.

## R010 — Is Manual code M a valid merchandise-revenue line?

**Status:** full-workbook invoice composition and price-distribution profile completed; business classification still open.

- Of 788 M-containing invoice IDs with positive-priced M entries, **290** have only M-coded lines, **498** also contain other stock codes, and **480** contain positive-priced non-M lines. The 861 M positive lines total £339,629.94 after cross-sheet reconciliation.
- The **median** M line amount is **£8.85**, but the **largest** is **£25,111.09**; the **top ten** make up **31.91%** of M's positive-priced total. Strongly skewed observations merit further scrutiny, not automatic exclusion.
- **534 C-prefixed negative M lines** have signed line-amount magnitude of £422,939.08, **not a verified cash-refund amount**.
- We do not know the accounting meaning of M, so neither S0 inclusion nor S2 exclusion is approved. Keep M as a separate ambiguous category for exploratory reporting.
- [Case 010 findings](MANUAL_CODE_FINDINGS.md); [successful original-workbook run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42886173182).

## R011 — Do high-value Manual charges have credible cancellation partners?

**Status:** strict candidate search completed; verified event/refund relationships unresolved.

- Of **861** positive M lines and **534** C-prefixed negative M lines in the candidate view, there were **80** plausible pair comparisons within 90 days under strict same-known-customer, country, abs quantity, unit-price, and later cancellation conditions. **51** were reciprocal one-to-one candidates; these are **not verified refunds**. No additional matches appeared by extending to 365 days.
- **468** C-negative M lines had no qualifying earlier positive partner, which does **not** prove they lack a real-world corresponding event. Missing customer IDs and time-order assumptions constrain linkage.
- **Close-time counterexample:** June 17, 2010 at 16:52, `C512770` (negative £25,111.09, customer ID present) precedes invoice `512771` at 16:53 (positive £25,111.09, customer ID missing). Their proximity is evidence of a *recording pattern*, not proof of a correction.
- [Case 011 reproducible findings](MANUAL_LINKAGE_FINDINGS.md); [passing original-workbook workflow](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42890694308).
- **Case 012 completed:** [bidirectional short-time pattern findings](MANUAL_BIDIRECTIONAL_FINDINGS.md) found **168** no-known-customer-conflict candidate comparisons within five minutes (104 negative-first, 63 positive-first, 1 same-minute). **78** of these have known matching customer IDs; the remaining **90** include missing IDs and are weak lookalikes, not confirmed event links.
- **Next:** audit 2,631 positive zero-price candidate lines and 5 positive-quantity negative-price lines, before deciding final KPI semantics.

## R012 — Do negative-first Manual sign flips recur in short time windows?

**Status:** descriptive original-workbook check complete; event identity unresolved.

- Matching line fields (without assuming equal missing customer IDs): same code M, absolute quantity, unit price, and country. The C-negative/positive direction is assessed in both directions within 1/5/15/60 minutes.
- **5-minute window:** 171 lookalike comparisons, 3 known-customer conflicts excluded, 168 no-known-conflict candidate comparisons, including 104 negative-first, 63 positive-first, 1 same-minute. Of 168: 78 known-same, 78 one missing, 12 both missing.
- A separate positive-positive M comparison finds 15 matching pairs within five minutes; this is **descriptive only** and is not a causal baseline.
- The £25,111.09 June 17, 2010 negative-before-positive pair is an example of a weak timing candidate with missing customer data, **not** verified reversal or refund.
- [Case 012 report](MANUAL_BIDIRECTIONAL_FINDINGS.md); [successful original-workbook CI](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42898160193).
- **Case 013 completed:** [zero/negative price findings](PRICE_PARADOX_FINDINGS.md) identify 2,631 positive zero-price lines and five `A`-prefixed/`B`-coded `Adjust bad debt` negative-price lines totalling −£158,676.14 in signed amount. Business meaning remains unconfirmed, and no KPI definition was changed.
- **Next:** examine zero-priced items on mixed paid-looking invoices and whether bad-debt-labelled entries appear in other invoice patterns; propose an explicit KPI semantic dictionary.

## R013 — Do zero and negative unit prices indicate free items or accounting entries?

**Status:** full-source diagnostic completed; final business classifications pending.

- The 2,631 non-C positive-quantity zero-priced lines appear on 1,986 invoice numbers, of which 1,861 contain only such lines and 125 also contain positive-price lines. Most lack customer IDs (2,561) and descriptions (1,642); descriptions such as `found`, `check` and `adjustment` are suggestive but not determinative.
- All five positive-quantity negative-unit-price rows have `A`-prefixed invoice IDs, code `B` and description `Adjust bad debt`, each in a single-line invoice without a customer ID. Signed amount total is −£158,676.14, not a verified accounting write-off or refund.
- Two such `A`-prefixed entries are a minute apart and share a −£11,062.06 amount, but different invoice IDs prevent treating them as exact duplicates.
- [Case 013 source-verified findings](PRICE_PARADOX_FINDINGS.md); [successful original-workbook workflow](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42912802097).
- **Next:** review mixed-price invoices, then draft a provisional semantic dictionary without altering the raw workbook or Case 008 reversible view.

## R014 — Are mixed zero/positive-price invoices semantically distinct?

**Status:** Case 014 verified against the original workbook; business classifications remain unresolved.

- [Case 014 source-verified report](MIXED_PRICE_INVOICE_FINDINGS.md): 125 mixed invoice IDs include 709 zero-price lines and 7,660 positive-priced lines; 1,861 zero-price-only invoices contain the other 1,922 zero-price lines.
- All **709** zero-price lines in mixed invoices have descriptions. In the zero-price-only cohort, **1,642 of 1,922** lack descriptions. Known customer IDs: 61 versus 9 lines, respectively.
- **43** zero-price lines across **33** mixed invoices share a stock code with a positive-priced line *on the same invoice*. Examine these with quantities, pricing and time context before trying any label or correction rule.
- Full original-workbook [GitHub Actions run succeeded with 77 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42933178973), with no source changes, revenue assumptions or customer identity exports.
- A separate later inquiry into `A`-invoice / `B`-stock-code entries is still open.

## R015 — Do zero-priced lines sharing a SKU with paid lines on the same invoice form a meaningful pattern?

**Status:** Case 015 verified against original workbook; individual business-event meanings remain unresolved.

- [Case 015 verified findings](SAME_SKU_MIXED_PRICE_FINDINGS.md): **43** positive-£0 same-SKU comparisons across **33** invoice IDs; **10** share equal recorded quantities and **33** have customer IDs missing on both sides; all share a recorded invoice minute.
- Some same-SKU pairs show very unequal counts, including 10,200 £0 units with one positively priced unit on invoice `507637`; this does not resemble a simple 1+1 pattern but the source cannot establish why.
- Full source [audit passed 83 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42935952251). No new promotion, correction, duplicate, or revenue decisions.
- Case 016 now tests SKU-specific recurrence across *different invoices*, rather than interpreting any one invoice as a campaign.

## R016 — Could repeated same-SKU £0/paid pairs across nearby invoices indicate a BOGO campaign?

**Status:** Case 016 original-workbook diagnostic completed; BOGO explanation not established.

- [Case 016 source-verified findings](TEMPORAL_BOGO_HYPOTHESIS.md): **32** SKUs have paid-and-zero same-invoice patterns; **five** have such patterns on different invoices; **two** recur within 7 days, **four** within 30 days.
- Exactly **five** invoice/SKU groups have a strict one-paid-unit + one-zero-unit pattern, but **none** of these groups repeats for the same SKU across different invoices. This weakens the specific recurring literal-BOGO signature.
- The repeated codes include **84016** (six invoices, often highly unequal quantities) and **20724** (four invoices). Neither has an exact 1+1 pattern in the original-source report.
- [Original-workbook workflow passed 89 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42937165126). Do not infer promotion dates, customer redemptions, correction causes or financial totals; no raw or candidate rows or KPI definitions changed.
- Next: explore *multi-unit equal-quantity* paid/zero pairings and time-window-specific paid-only baselines, and investigate code 84016 separately.

## R017 — Does an equal multi-unit £0+paid pattern recur for the same SKU in a short period?

**Status:** Case 017 original workbook audit complete; promotions and corrections remain unverified.

- [Case 017 verified results](MULTIUNIT_WEEKLY_CONTEXT.md): **43** invoice+SKU groups across **33** invoice IDs; **10** have equal total positive priced versus £0 quantities, including **five** multi-unit groups and **five** strict 1+1 groups. No SKU exhibits multi-unit equality on two separate invoices.
- A high same-week pairing fraction can arise from tiny denominators: e.g., SKU `22043` appeared 1 of 1 paid invoice+SKU group that week, *not* an established campaign rate. Recurring `84016` and `20724` never show equal quantities.
- Original [workflow passed 95 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42940297437). This narrows the BOGO hypothesis without proving it impossible, and does not validate a correction cause.
- Pricing follow-up remains optional; prioritize Case 018 SQL reconciliation and business analysis. Preserve source records, reversible provenance and provisional financial scenarios.

## R018 — Can SQL reproduce all candidate classifications and provisional gross amounts independently?

**Status:** SQL classification view, streaming SQLite workbench and five synthetic tests committed; original-workbook SQL reconciliation pending.

- [Provisional semantic dictionary](PROVISIONAL_KPI_DICTIONARY.md) maps source-record shapes to exhaustive, non-causal analytical categories with explicit precedence.
- [SQL workbench](SQL_KPI_WORKBENCH.md) re-derives 1,044,848 candidate-line cohort counts and source-verified S0/S1/S2 amounts/qualifying invoice IDs. The script fails if counts or currency values differ beyond 2p tolerance.
- Monthly S2 gross positive-priced line activity, units, qualifying invoice identifiers, missing customer coverage, cancellation codes, and zero-price entries remain **exploratory only**. No refunds, revenue or BOGO labels are inferred.
- Next: verify on original source, then analyze month/country completeness and invoice concentration, not endless source anomalies.

## R019 — Does recorded merchandise-like activity increase between comparable 2010 and 2011 months?

**Status:** Case 019 original-workbook source and independent SQL-month reconciliation completed, [105 tests passed](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42944895542); [Case 019 verified findings](MONTHLY_BUSINESS_ACTIVITY.md) compare like-for-like Jan–Nov periods.

- From source-verified SQLite 25-month aggregate: **Jan–Nov S2 gross positive-priced line amount £8,639,086.69 in 2010 vs £8,889,734.02 in 2011 (+2.90%)**, not recognized revenue.
- Qualifying lines **443,587 → 461,446**; sum of monthly distinct invoice IDs **18,122 → 17,410**; customer-ID coverage **81.43% → 76.51%**. Invoices and line IDs are not completed orders or unique customers.
- November shows the highest S2 amount in each of 2010 and 2011, but seasonal causation, discounting, shipping/wholesale, product mix and changes in coverage remain untested.
- Next business step: analyze concentration in high-value invoice IDs, month/year source completeness and scenario sensitivity before presenting any growth or dashboard conclusion.

## R020 — Does a small number of large invoice IDs explain the provisional S2 year-over-year difference?

**Status:** Case 020 verified against original workbook, [110 tests passed](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106).

- [Verified Case 020 findings](INVOICE_CONCENTRATION_ANALYSIS.md) show top 1% of qualifying invoice-ID-month groups contribute **16.06% of S2 gross line amount in Jan–Nov 2010** (182 groups) and **17.80% in Jan–Nov 2011** (175 groups).
- Removing each period's top 1% **for sensitivity only** reduces the apparent S2 gross amount change from **+2.90%** to **+0.77%**. The respective independently selected top groups account for £194,744.51 of the £250,647.33 arithmetic period difference; not causal attribution of growth.
- Median group amounts rise £300.58 → £304.24; changes in product mix, quantity, effective prices, customer coverage or large invoices are still unproven. **No actual source rows, KPI rules or unusual invoices were removed.**
- Next: test product mix and within-SKU amount-per-unit composition, then build a concise decision-focused report.

## R002 — Are monthly or geographic differences meaningful?

**Status:** open, not yet tested.

- Check temporal completeness, seasonality, geography, and the effect of major wholesale orders.
- Avoid attributing trends to marketing or customer behavior without corroborating data.

## R003 — What can customer IDs tell us?

**Status:** open, not yet tested.

- Quantify missing customer IDs before estimating repeat-purchase rates or RFM segmentation.
- Document that anonymous transactions cannot confidently be attributed to individuals.

## Evidence discipline

Separate source metadata, observed audit counts, assumptions, and business interpretations. Record every cleaning/filter decision and its row impact before using it downstream. No dashboard or final narrative is approved yet.

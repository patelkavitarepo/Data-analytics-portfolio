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
- **Next:** inspect high-value manual charges, anomalous zero/negative prices, and returns/cancellations matching before selecting business KPIs.

## R010 — Is Manual code M a valid merchandise-revenue line?

**Status:** full-workbook invoice composition and price-distribution profile completed; business classification still open.

- Of 788 M-containing invoice IDs with positive-priced M entries, **290** have only M-coded lines, **498** also contain other stock codes, and **480** contain positive-priced non-M lines. The 861 M positive lines total £339,629.94 after cross-sheet reconciliation.
- The **median** M line amount is **£8.85**, but the **largest** is **£25,111.09**; the **top ten** make up **31.91%** of M's positive-priced total. Strongly skewed observations merit further scrutiny, not automatic exclusion.
- **534 C-prefixed negative M lines** have signed line-amount magnitude of £422,939.08, **not a verified cash-refund amount**.
- We do not know the accounting meaning of M, so neither S0 inclusion nor S2 exclusion is approved. Keep M as a separate ambiguous category for exploratory reporting.
- [Case 010 findings](MANUAL_CODE_FINDINGS.md); [successful original-workbook run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42886173182).

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

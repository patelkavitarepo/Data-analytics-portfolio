# Retail Intelligence — Decision-Focused Dashboard Specification

**Project:** 003 Retail Intelligence  
**Status:** Proposed dashboard / report design. **No Power BI dashboard has been built yet.** Data definitions remain provisional, and Case 021 SKU decomposition is **pending source verification**.

## Audience and question

A retail manager asks: **Did the observed merchandise-like business activity change meaningfully from January–November 2010 to January–November 2011, and what sources of uncertainty make that comparison fragile?**

The proposed dashboard should answer this with **recorded invoice activity**, not certify net sales, true revenue, refund amounts, profit, customer retention or demand. Show the exact S2 definition and the S0/S1 sensitivity before any recommendations.

## Page 1: Executive activity review

- Headline: **Jan–Nov 2010 vs 2011 (matched months only)**; original UCI Online Retail II historical source, not real-time.
- Three labeled S2 cards: **£8.64M vs £8.89M gross positive-priced merchandise-like line amount**; **+2.90% descriptive difference**; **−6.00% recorded S2 units**. Every card carries the qualifier *experimental S2; not recognized revenue*.
- A fourth card compares **18,122 versus 17,410 sum of monthly qualifying invoice-ID counts** (**−3.93%**). Label *invoice identifiers*, never *orders* or *transactions completed*.
- 11-month overlay of the recorded S2 gross amount in 2010 and 2011, with full month coverage disclosure. **Exclude incomplete December 2011** from full-month year-over-year charts.
- A short, conditional business interpretation: *Higher gross positive-priced amounts coexist with fewer recorded units and invoice-ID-month groups. Investigate mix, price conventions, and large-invoice concentration; do not claim demand or profit growth.*

## Page 2: Data-quality and definition controls

- An explicit scenario selector or side-by-side comparison: S0 **£20,533,741.92**, S1 **£20,063,792.35**, S2 **£19,723,764.52** over the full analysis source view. All three are **experimental source-line sums**, not accounting revenue.
- Reversible source tracking: **1,067,371 raw rows → 1,044,848 candidate rows**, with 22,523 cross-sheet publication-copy links and retained original-row provenance.
- Exception context: **19,165 C-prefixed source-coded cancellation lines**, **2,631 positive-quantity £0 lines**, **5 positive-quantity negative-price lines**, and **3,393 non-C negative-quantity £0 lines**. Do not label them verified refunds, promotions, losses or errors.
- Customer-ID coverage: **81.43%** of S2 lines carry known IDs in Jan–Nov 2010 versus **76.51%** in 2011; these are *line coverage*, not unique identified customers.

## Page 3: Invoice concentration and sensitivity

- The highest 1% of **qualifying invoice-ID-month groups** contribute **16.06%** of Jan–Nov 2010 S2 gross amount versus **17.80%** of 2011 S2 gross.
- Show **+2.90%** untrimmed S2 gross period difference alongside **+0.77%** after omitting the top 1% within *each* period **for sensitivity only**. Never imply those invoices should be deleted or have invalid values.
- Show distribution reference points: medians **£300.58 vs £304.24** and 95th percentiles **£1,384.68 vs £1,493.66** per invoice-ID-month group.
- Drilldown to **month aggregates only**, no individual invoice IDs/customer IDs in a public dashboard. Annotate selection and denominator limitations.

## Page 4: SKU and unit-value bridge (conditional, Case 021 pending)

- Only display once the independent Case 021 source checks pass and the product-code bridge reconciles to Case 018.
- Visualize **four arithmetic terms** for Jan–Nov S2 gross change: common-SKU recorded-quantity component, common-SKU effective gross amount-per-unit component, later-only SKU gross contribution, earlier-only SKU disappearing contribution.
- The effective per-unit residual is not automatically **price inflation**, and earlier/later-only source codes do not establish new/discontinued products. No causal claim without external evidence.

## Required footnote and narrative contract

> **Historical observational data.** All amounts are gross positive-priced invoice-line scenarios, *not financial-statement revenue, net sales or cash received*. Source coding does not establish payments, shipments, refunds, BOGO promotions, accounting corrections or product-level profitability. C-prefixed lines are not mechanically netted. Uncertain codes and missing customer IDs remain explicit.

## Publication gates

1. Source-reconciled SQL **Case 018**: complete, 100 tests passed.
2. Matched-month activity **Case 019**: complete, 105 tests passed.
3. Invoice concentration **Case 020**: complete, 110 tests passed.
4. SKU composition **Case 021**: implemented, original-workbook verification pending.
5. Build Power BI dashboards using **aggregate-only, vetted outputs**, verify displayed totals against the GitHub Actions artifact, then draft a one-page case study with business interpretation and limitations.
6. Keep draft PR #3 unmerged until the project-level code review, documentation and responsible source attribution have passed.

**No source data, cleaning policy or accounting rule is changed by this design.**

# Case 019 — First business question: how did merchandise-like activity change?

**Project:** 003 Retail Intelligence  
**Source evidence date:** November 10, 2026 (US Eastern); GitHub Actions source audit 2026-11-11 UTC  
**Status:** **Results below directly calculated from original-source-reconciled Case 018 SQL aggregates.** A separate Case 019 implementation and five synthetic tests are committed; **Case 019's full workflow recheck is pending**. This is descriptive **S2 gross positive-priced merchandise-like line activity**, *not* accounting revenue or verified customer demand.

## Evidence trail and definitions

- Original workbook: UCI Online Retail II (dataset #502), SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- Source audit: https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42941460657 — successful, **100 synthetic tests passed**. SQLite reconciled **1,044,848** candidate lines and all three source-verified Case 009 S0/S1/S2 amount, line-count and qualifying invoice-ID scenarios.
- Aggregate artifact: `retail-initial-audit` from that run, `sql_kpi_workbench.json`: 25 recorded-month rows from Dec 2009 to Dec 2011. SQL `agrees_with_case_009_counts_invoice_ids_and_amounts = true`.
- Full-source raw date range: **2009-12-01 to 2011-12-09**. **December 2011 is incomplete** and must **not** be compared to a full December 2010 as if both were complete periods.
- The **comparison below uses January–November 2010 versus January–November 2011** with identical calendar-month coverage (subject to day-level data gaps that may still require checking). It **excludes both December months**.
- All source records and 22,523 exact cross-sheet copy canonical links remain unchanged. The S2 definition still excludes named postage/billing codes and `M`/`D` manual/discount codes, and **does not net cancellation-coded amounts as refunds**.

## First comparison: January–November, same months

| Provisional observational metric | 2010 Jan–Nov | 2011 Jan–Nov | Difference |
| --- | ---: | ---: | ---: |
| **S2 gross positive-priced line amount** (not revenue) | **£8,639,086.69** | **£8,889,734.02** | **+£250,647.33 (+2.90%)** |
| Qualifying S2 invoice lines | **443,587** | **461,446** | **+17,859 (+4.03%)** |
| **Sum of monthly** distinct qualifying invoice-ID counts (not verified orders) | **18,122** | **17,410** | **−712 (−3.93%)** |
| Recorded S2 positive unit quantities (not verified shipments) | **5,218,220** | **4,905,104** | **−313,116 (−6.00%)** |
| S2 lines with known customer ID | **361,216** | **353,042** | **−8,174** |
| Known customer-ID share of S2 lines | **81.43%** | **76.51%** | **−4.92 percentage points** |
| Gross S2 line amount per **invoice-ID-month pairing** | **£476.72** | **£510.61** | **+7.11%** |

The invoice identifier counts are **summed from distinct-per-month values**. A repeated invoice ID across months would be counted again; the report **does not claim a distinct customer or completed-order count for the whole period**.

## Unit and invoice-ID composition: independent descriptive checks

Derived **only** from the same Case 018 source-reconciled Jan–Nov aggregates, with both years covering the same calendar months:

| Derived ratio | 2010 Jan–Nov | 2011 Jan–Nov | Change |
| --- | ---: | ---: | ---: |
| S2 gross positive-priced line amount per **recorded unit** | **£1.6556** | **£1.8123** | **+9.47%** |
| S2 positive-priced **lines per invoice-ID-month pair** | **24.48** | **26.50** | **+8.28%** |
| S2 gross amount per positive-priced **line** | **£19.48** | **£19.26** | **−1.08%** |
| S2 recorded **units per invoice-ID-month pair** | **287.95** | **281.74** | **−2.16%** |

Each ratio uses aggregate sums, not the arithmetic mean of monthly ratios. A year-over-year change in gross amount per recorded unit is **not** evidence of price inflation: the observed ratio can move because of **product mix, invoices, unit counts or price**. Likewise, more lines per invoice-ID-month are **not** necessarily more products per completed customer order. **None of these ratios confirms revenue growth, better unit economics, increased profitability or a causal effect.**

These indicators reinforce the need for [Case 020 invoice-size concentration](INVOICE_CONCENTRATION_ANALYSIS.md) before presenting the 2.90% gross S2 change as a meaningful business performance improvement.

## Matched-month gross line-amount comparison

| Calendar month | 2010 S2 gross line amount | 2011 S2 gross line amount | 2011 vs 2010 |
| --- | ---: | ---: | ---: |
| January | £622,906.82 | £671,992.41 | **+7.88%** |
| February | £539,761.71 | £508,952.87 | **−5.71%** |
| March | £764,376.40 | £691,265.94 | **−9.56%** |
| April | £649,200.75 | £516,339.79 | **−20.47%** |
| May | £645,739.00 | £741,275.74 | **+14.79%** |
| June | £700,115.15 | £738,876.88 | **+5.54%** |
| July | £634,982.09 | £689,397.74 | **+8.57%** |
| August | £676,215.89 | £736,667.22 | **+8.94%** |
| September | £871,912.38 | £1,030,500.36 | **+18.19%** |
| October | £1,098,145.32 | £1,106,719.54 | **+0.78%** |
| November | £1,435,731.18 | £1,457,745.53 | **+1.53%** |

**Eight of the eleven** matched months have higher S2 gross line amounts in 2011 than in 2010. **November** is the largest matched-month amount in both years; October and September are also near the top. This is **consistent with a late-year seasonal concentration in the recorded data**, but does **not establish a seasonal causal mechanism, growth in demand, holiday sales, or merchandising effectiveness**.

## What these results do and do not tell us

1. **Observed:** S2 gross line amount is 2.90% higher in the 2011 Jan–Nov period; *recorded* S2 line count is 4.03% higher while the *sum of monthly distinct invoice IDs* is 3.93% lower and recorded units 6.00% lower. The measures move in different directions; calling this a simple “sales grew 2.90%” story would be unjustified.
2. **Observed:** Gross line amount per invoice-ID-month is higher, but this may reflect product mix, pricing, wholesale quantity structure, unusual large invoices, or S2 exclusion semantics. It is **not** approved average order value.
3. **Observed:** Customer-ID coverage among S2 lines declines **81.43% → 76.51%**. This limits meaningful attribution of changing activity to identified customers, retention or RFM.
4. **Caution:** The underlying data include wholesalers, C-prefixed cancellation records and ambiguous non-product codes. The S2 gross measure is deliberately **not net** and cannot verify cash, profit or fulfilled orders.
5. **Caution:** Month and year comparisons are descriptive. They have not been adjusted for the number of trading days, promotions, price-level changes, bulk invoicing, product diversity or customer coverage.
6. **Source-reconciliation caution:** 25 individually rounded monthly S2 amounts sum to a value **one penny different** from the aggregate S2 total; the original SQL validation compares the full unrounded source total and reconciles correctly. The Case 019 rollup explicitly tolerates less than 5p for month-level rounding.

## Business questions that now deserve testing

- **R019a — Concentration:** Do a few wholesale-like or very high-value invoices dominate the apparent monthly changes? Need median and upper-tail positive-priced invoice-ID amounts, plus top 1% concentration, within each recorded month.
- **R019b — Composition:** Does the shift reflect different quantities per invoice, priced product mix, or average unit prices? These alternatives require SKU/line-level decomposition; do **not infer** from gross totals alone.
- **R019c — Coverage:** How does missing customer-ID prevalence vary by year, month and source product context? Do not represent unknown IDs as anonymous unique customers.
- **R019d — Sensitivity:** Does the 2.90% observed S2 contrast persist under S0/S1 definitions and when unusually large invoice IDs are profiled separately? Preserve alternative scenarios; do not selectively choose the nicest growth figure.

## Reproducible implementation

Run after Case 018:

```bash
python scripts/analyze_monthly_business_activity.py
python -m pytest -q
```

This reads **only aggregate SQL summary JSON**, matches identical calendar months, validates totals against the independent SQL Case 018 S2 baseline, and outputs `outputs/monthly_business_activity.json`. It neither loads nor publishes the original workbook or any customer-level row.

**Conclusion:** We have credible *observational* month-level differences, but we have not yet isolated whether pricing, quantity, seasonality, wholesale composition, or data coverage explains them. **Next action: test invoice-size concentration before making a retail growth claim or designing a Power BI dashboard.**

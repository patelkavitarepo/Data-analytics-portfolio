# Case 020 — Are a few unusually large invoice IDs driving the apparent activity change?

**Project:** 003 Retail Intelligence  
**Status:** Business question, source-reconciled concentration script and five synthetic tests implemented. **Original-workbook concentration results have not yet been verified by GitHub Actions.** This is exploratory activity, not recognized sales or verified customer purchases.

## Motivation

[Case 019](MONTHLY_BUSINESS_ACTIVITY.md) shows that provisional S2 gross positive-priced line amount increases **2.90%** from Jan–Nov 2010 to Jan–Nov 2011, while sum of monthly distinct qualifying invoice-ID counts **declines 3.93%**, recorded units decrease **6.00%**, and qualifying lines increase **4.03%**. This mix suggests examining **invoice concentration and possible wholesale-like outliers**, without assuming a causal explanation.

## Read-only source-based method

- Script: `scripts/analyze_invoice_concentration.py`; tests: `tests/test_invoice_concentration.py`.
- Uses only the **local ignored Case 008 reversible candidate CSV.gz** and independent, original-source-reconciled [Case 018 SQL summary](SQL_KPI_WORKBENCH.md). Does not load or upload the original workbook.
- Applies the same explicit **S2 filter**: invoice ID not C-prefixed; quantity > 0; unit price > 0; exact trimmed uppercase stock code **not** in `POST`, `DOT`, `C2`, `BANK CHARGES`, `AMAZONFEE`, `M`, `D`.
- Groups qualifying *line amounts* by **recorded month and invoice ID**, not by customer, product category, physical shipment, or confirmed order.
- Reports, for each month, the median, 95th percentile, maximum and gross share attributable to the **upper one percent** of qualifying invoice-ID-month groups. The group count uses ceiling(1% × group count), at least one group.
- Performs two **January–November** matched-period comparisons, one each for 2010 and 2011: share concentrated in the highest 1% of invoice-ID-month groups, and a **sensitivity-only** gross line amount after omitting those groups. The different resulting subsets are **not approved cleaning or a causal matched experiment**.
- Explicitly reconciles monthly S2 gross amounts, per-month distinct qualifying invoice IDs, aggregate qualifying line counts and full S2 gross amount with the independently source-verified Case 018 SQL result. No tolerance greater than **£0.05** is accepted for amount rounding differences.
- Produces only bounded aggregated `outputs/invoice_concentration.json`; **no invoice numbers, customer IDs, individual rows, or row-level derived datasets** are published.

## How we will interpret it

- High upper-one-percent share implies that a small number of invoice-ID-month groups account for a disproportionate amount of the provisional gross line amount. It does **not** establish wholesaling, fraud, actual large purchases or business profitability.
- If the Jan–Nov S2 comparison changes significantly after removing large invoice groups in **each** period, the initial +2.90% observation is not stable to outlier composition.
- Even if the comparison is robust, it cannot establish organic growth or customer demand without exploring prices, product mix, missing customer coverage, source time windows and settlement status.
- We must **not** remove unusual invoice lines from original data, change Case 008's provenance map, revise S2 to force an appealing trend, or net cancellation-coded amounts as verified refunds.

## Decision gate

After **full-data test success**, record the actual concentration values and open a constrained next business question (product mix vs. unit-price change) only if necessary for explaining the observation. Our next portfolio deliverable should be a **decision-focused analytical report/dashboard**, not unlimited anomaly investigation.

**Case 020 source findings pending**, so no concentration values or explanation are asserted at this stage.

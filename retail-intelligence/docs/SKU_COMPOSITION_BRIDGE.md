# Case 021 — SKU quantity and effective value: full-source verified bridge

**Project:** 003 Retail Intelligence  
**Status:** **Original-source verified.** [Successful GitHub Actions run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42949051946) completed with **115 passing synthetic tests**. It matched the independent SQL aggregates for both years. The findings are descriptive identities, **not accounting revenue, price inflation, customer demand or a causal business explanation**.

## The question

From January–November 2010 to the same calendar months in 2011, provisional S2 gross positive-priced merchandise-like line amount rises **£250,647.33 (+2.90%)**, while recorded units decline by approximately **6.00%**. Case 020 also found that the highest 1% of invoice-ID-month groups increased their share of gross amount, with a **+0.77%** upper-tail-excluded sensitivity.

How much of the overall gross S2 difference is associated arithmetically with quantities and observed effective value per unit for stock codes present in both periods, versus recorded stock codes appearing in only one year?

## Evidence and reproducibility

- **Source:** UCI Online Retail II original workbook, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Full-source run:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42949051946 — **success, 115 synthetic tests passed**, all stage checks completed.
- **Script:** `scripts/analyze_sku_composition.py`. **Tests:** `tests/test_sku_composition.py`.
- **Machine-readable source summary:** `outputs/sku_composition.json` in the `retail-initial-audit` Actions artifact. Only aggregate SKU-level examples (maximum 15); **no invoice IDs, customer IDs or original rows**.
- **Provenance and source integrity:** Case 008 reversible candidate view: **1,044,848** lines and 22,523 exact cross-sheet source-copy links, accounting for **1,067,371** raw lines. Original workbook, source-to-canonical links and S0/S1/S2 definitions are **unchanged**.
- **Independent verification:** 2010 and 2011 matched-period S2 source line counts, recorded units and gross line amounts each reconcile exactly to Case 018's separately verified SQLite aggregates.

## Two matched-year observations

| Provisional S2 metric | Jan–Nov 2010 | Jan–Nov 2011 |
| --- | ---: | ---: |
| S2 gross positive-priced line amount (not recognized revenue) | **£8,639,086.69** | **£8,889,734.02** |
| Qualifying positive-priced lines | **443,587** | **461,446** |
| Recorded positive unit quantity (not confirmed shipments) | **5,218,220** | **4,905,104** |
| Recorded stock codes with an S2 qualifying line | **3,948** | **3,722** |
| Gross positive line amount per recorded unit (not inflation) | **£1.655562** | **£1.812344** |

## Identity-based £250,647.33 gross-amount bridge

| Arithmetic component | GBP contribution |
| --- | ---: |
| Shared-stock-code **recorded quantity** change, valued at earlier-period observed gross per unit | **−£992,716.27** |
| Shared-stock-code **effective gross amount per unit** residual | **−£141,027.84** |
| Stock codes recorded **only in 2011** — observed positive gross amount | **+£2,058,492.44** |
| Stock codes recorded **only in 2010** — subtract earlier positive gross amount | **−£674,101.00** |
| **Exact net source-reconciled S2 difference** | **+£250,647.33** |

**SKU cohorts:** 3,067 stock codes have qualifying S2 lines in **both** periods; 655 appear **only in 2011**; 881 appear **only in 2010**. These are descriptive stock-code-presence categories, **not verified product launches, discontinuations, customer preference or merchandising decisions**.

For shared stock codes, the two observed components sum to **−£1,133,744.11**. Codes found in only one matched period contribute a net **+£1,384,391.44**. Their arithmetic sum explains the +£250,647.33 observed change.

**Critical interpretation:** A large source-period-only SKU contribution could reflect changing listings/assortment, code recategorization or reuse, data coverage, reporting conventions, or actual business mix. The dataset does not distinguish these. Likewise the within-SKU effective gross-per-unit residual is **not a pure inflation or price index**.

## Exact method

For a stock code with positive S2 quantity in both periods, set earlier/later units `u0`/`u1`, gross values `v0`/`v1`, and earlier effective value per recorded unit `p0 = v0/u0`.

Then the following is an **arithmetic identity**, not a causal model:

`v1 − v0 = (u1 − u0) × p0 + (v1 − u1 × p0)`

- First term: recorded quantity component at the prior-period *observed effective* unit value.
- Second term: changing effective unit-value residual; may include true price changes, item mix within code, billing changes, discounts or reuse.
- SKU codes only in 2011 contribute their full 2011 gross S2 amount; SKU codes only in 2010 contribute minus their 2010 gross S2 amount.
- Sum of the four components must reconcile within 5p; period gross/quantity/line counts independently agree with Case 018 SQL.

## Business interpretation and next portfolio decision

1. **Observed, not inferred:** The overall provisional S2 gross amount increases 2.90%, while common-stock-code quantity/value components sum to a negative **£1.13 million**. A change in which stock codes appear in the two periods is a major mathematical contributor to the gross comparison.
2. **Observed:** The common-SKU effective gross value residual is **negative** in this chosen base-period decomposition even though the overall gross amount per recorded unit rises from **£1.655562 to £1.812344**. These measures have different weighting/denominators. Therefore a simple “prices increased” explanation is **not established**.
3. **Sensitivity retained:** The separate Case 020 upper-one-percent-omitted comparison falls from **+2.90% to +0.77%**. Do not treat that as an authorized cleaning rule or add it to the SKU arithmetic identity as if independent causal drivers.
4. **Not established:** recognized revenue, real order/customer growth, product launches/retirements, promotion causes, profit margin, inflation, physical shipments, wholesale status or customer retention.
5. **Recommended next portfolio deliverable:** Upgrade the aggregate dashboard and one-page case study with a carefully labeled **four-term decomposition waterfall**. Avoid excessive further anomaly cases unless a specific KPI or business question depends on them.

**Decision D059:** Publish the full four-term observed S2 identity with its source checks and prominent causal limitations. Preserve all original source data, reversible provenance, row classifications and experimental S0/S1/S2 rules unchanged.

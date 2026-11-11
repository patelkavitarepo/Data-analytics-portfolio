# Retail Intelligence dashboard — aggregate-only preview

**Status:** Versioned **static HTML** executive dashboard. It is **not a Power BI `.pbix` file**, nor does this repository claim published Power BI online service deployment. The preview uses independently source-verified summaries from Cases 018–021. It contains no transaction-level rows, individual invoice/customer IDs or source workbook.

## Open the preview

Open [`index.html`](index.html) in a browser after cloning/downloading the repository, or view the matching HTML artifact shared in the project conversation.

The preview includes:

- **Cases 018–019:** January–November 2010 vs 2011 recorded S2 gross positive-priced line amount and 11 matching month comparisons; **+2.90%** is **not recognized revenue growth**.
- **Case 020:** Upper 1% invoice-ID-month groups: 16.06% of the S2 gross amount in 2010 versus 17.80% in 2011. Omitting these upper groups independently for sensitivity changes the apparent comparison to **+0.77%**. Original records remain intact.
- **Case 021:** Exact four-part arithmetic bridge: shared-SKU recorded quantities **−£992,716.27**, shared-SKU effective gross amount per unit residual **−£141,027.84**, 2011-only stock codes **+£2,058,492.44**, 2010-only stock codes **−£674,101.00**. Net **+£250,647.33**.
- **Data integrity:** 1,067,371 raw invoice lines, 22,523 exact cross-sheet copy links, 1,044,848 candidate lines, and S0/S1/S2 sensitivity.

## Reproducible data and validation

The full-source audited source is [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii), official workbook SHA-256:

`bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`

Original-source GitHub Actions verification:

| Investigation | Evidence | Result |
| --- | --- | --- |
| Case 018 — SQL cohorts and experimental S0/S1/S2 | [Run #42941460657](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42941460657) | 100 tests passed |
| Case 019 — Matched-month activity | [Run #42944895542](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42944895542) | 105 tests passed |
| Case 020 — Invoice concentration | [Run #42945421106](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106) | 110 tests passed |
| Case 021 — SKU composition | [Run #42949051946](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42949051946) | 115 tests passed |

From `retail-intelligence/`, after the earlier source audit steps have generated the **ignored local** summary JSON files, validate the static preview:

```bash
python scripts/verify_dashboard_preview.py
python -m pytest -q
```

The verifier compares the static HTML claims against Case 019–021 aggregate JSON and their independent SQL year-level checks. A mismatch fails CI rather than silently publishing stale numbers. The workflow publishes only aggregate JSON artifacts, not raw customer/invoice tables.

## Power BI-importable aggregate tables

A separate aggregate-only ZIP package prepared from the verified GitHub Actions artifact contains CSVs at these distinct grains:

- `monthly_activity.csv`: 25 recorded months.
- `monthly_invoice_concentration.csv`: 25 monthly distribution summaries.
- `matched_month_yoy.csv`: 11 comparable Jan–Nov months.
- `period_invoice_concentration.csv`: two Jan–Nov periods.
- `scenario_sensitivity.csv`: three provisional source gross-amount scenarios.
- `sku_change_components.csv`: four signed bridge elements.
- `sku_presence_cohorts.csv`: three stock-code population cohorts.
- `top_sku_aggregate_examples.csv`: at most 15 SKU-level aggregates, no invoice/customer identifiers.

**Power BI Desktop instructions:** Get Data → Text/CSV, import each file separately, and initially leave tables **disconnected**. Create visuals at each file's recorded grain; do not join a monthly summary to a scenario/period table as though it were line-level transaction data. Display *gross positive-priced line amount* instead of the ambiguous label *sales*. Show the 2011 incomplete-December restriction and the audit citations in the report. A native `.pbix` file still requires report creation in Power BI Desktop.

## Publishing discipline

These are historical observational source-line descriptions, not signed accounting records. C-prefixed cancellations are not verified cash refunds; £0 lines are not verified BOGO promotional redemptions; matching invoice IDs are not verified physical orders. Stock-code presence in only one period is not proof of a product launch or retirement, and the observed effective gross-per-unit residual is not a pure price-inflation measure.

The HTML report is explicitly a **static** portfolio preview; review the full [portfolio case study](../docs/PORTFOLIO_CASE_STUDY.md) and [dashboard design contract](../docs/DASHBOARD_SPEC.md) before public publication or promotion.

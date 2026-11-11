# Case 018 — SQL-first retail KPI workbench

**Status:** Reproducible SQLite workbench and five synthetic tests committed; **original-workbook SQL validation pending CI**. Source-specific accounting definitions and revenue recognition are **not approved**.

## Why we are switching gears

Seventeen investigations examined potential duplicates, cancellation shapes, ambiguous manual amounts, price anomalies, and the BOGO versus operations hypothesis. This is enough to **begin descriptive decision-focused analytics** without pretending every anomaly is causally solved.

See [provisional KPI semantic dictionary](PROVISIONAL_KPI_DICTIONARY.md): it states line-level labels, reproducibility requirements, cohort precedence, and exactly what proposed S0/S1/S2 metrics **do not** mean.

## Reproduction

In the local project directory after Case 008 and Case 009 have run:

```bash
python scripts/run_sql_kpi_workbench.py
python -m pytest -q
```

The standard-library SQLite workbench:
1. Loads only the **local ignored** `data/derived/candidate_analysis_lines.csv.gz` that Case 008 writes. It does **not** upload or commit row-level source material.
2. Applies `sql/001_provisional_retail_kpis.sql` to create an exhaustive, mutually exclusive **temporary** `retail_classified` view. Source records remain unchanged.
3. Verifies all descriptive cohort counts and the S0/S1/S2 **line counts**, **distinct invoice identifier counts**, and **gross positive line amounts** against source-verified Case 009 `outputs/revenue_sensitivity.json`. The monetary comparison permits only 2p difference for float summation at large scale; it does not silently revise the business definition.
4. Generates an aggregate-only `outputs/sql_kpi_workbench.json` summarizing the 9 provisional row cohorts, S0/S1/S2 values, and monthly S2 positive-priced line amounts, qualifying invoice IDs, recorded units, known customer-ID lines, C-coded cancellation lines and zero-price exceptions.
5. Fails on missing input, unexpected cohort discrepancies, inconsistent invoice-ID counts or gross-amount mismatches. No dataframe with original rows or individual IDs is published.

## Proposed analyses, not certified KPIs

- **Monthly recorded gross-positive merchandise-like line amount (S2)**; not recognized revenue, net sales or cash.
- **Invoice IDs with an S2 line**; not completed orders or unique customers.
- **Recorded positive units in S2 lines**; not fulfilled shipments.
- **Known-customer-ID coverage**; missing ID values remain unknown.
- **Separate C-coded cancellation and £0 positive-line counts**; not cash refunds or free promotional units.

## Current limitations

The UCI source does not expose payment settlement, official revenue mapping, cost of goods, inventory ledger or promotions schedule. The strict S2 definition omits some possible legitimate paid entries (`M`, `D`, named postage/carriage/billing) and **does not become truer by excluding more**. The project will present all three scenario alternatives prominently.

The calendar months may be unevenly covered, and the business may include wholesale outliers. Apparent growth, geographic differences or average invoice spend require additional context before interpretation.

## Next gates

- Verify the first full-source SQL workbench against the Case 009 reference, then document the actual monthly aggregates.
- Develop **SQL analysis questions**, starting with monthly/seasonal activity, concentration by country and invoice size, and missing customer-ID coverage, each with denominator checks.
- Add a decision-focused dashboard only after aggregate reconciliation, with definitions and limitations visible to portfolio readers.

**No source rows, source-to-canonical provenance links, cleaning rules or financial policies have been changed.**

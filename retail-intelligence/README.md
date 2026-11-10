# Project 003 — Retail Intelligence

**Status:** Phase 01 raw-data audit complete; Phase 02 anomaly investigation underway. Observed findings are verified against the original workbook, but financial definitions and causal explanations remain open.

## Objective

Use historical invoice-line data to investigate what happened in an online retail business, distinguish defensible business measures from misleading ones, and build decision-focused analysis. Python and SQL exploration will precede any Power BI dashboard.

## Data source and citation

- **Dataset:** Online Retail II, UCI Machine Learning Repository (dataset 502)
- **Author:** Daqing Chen
- **DOI:** https://doi.org/10.24432/C5CG6D
- **Official page:** https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **License:** CC BY 4.0 — attribution required
- **Publisher's description:** 1,067,371 invoice-line records, December 2009 to December 2011, UK-based non-store retailer; includes wholesalers.
- **File:** `online_retail_II.xlsx`, two yearly Excel sheets, approximately 43.5 MB.

This repository does **not** redistribute the original dataset. Original UCI workbook audited successfully: **1,067,371 invoice lines**, workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`. [GitHub audit evidence](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42851689386).

## First milestone: audit without cleaning

The audit reports raw row counts by sheet, date range, duplicate lines, missing values, `C`-prefixed cancellation codes, negative and zero quantities/prices, distinct countries, and the SHA-256 hash of the original workbook. No rows are removed. No sales or revenue measure is asserted before resolving returns, cancelled lines, non-merchandise items, and customer-ID missingness.

```bash
cd retail-intelligence
python -m pip install -r requirements.txt
python scripts/audit.py --download
python scripts/investigate_negative_quantities.py
python scripts/investigate_duplicates.py
python scripts/investigate_consecutive_invoices.py
python -m pytest -q
```

For an already downloaded workbook:

```bash
python scripts/audit.py --workbook data/raw/online_retail_II.xlsx
```

The download command obtains the official UCI workbook. The four analyses save `outputs/initial_audit.json`, `outputs/negative_quantity_investigation.json`, `outputs/duplicate_investigation.json`, and `outputs/consecutive_invoice_investigation.json` (outputs and workbook are ignored by Git). A successful GitHub Actions run audited the full source workbook and passed 19 synthetic-data tests. See [Investigation 001 findings](docs/NEGATIVE_QUANTITY_FINDINGS.md), including the cross-tab of negative quantities and cancellation prefixes.

**Hypothesis H001 follow-up:** [operational adjustment evidence](docs/H001_FOLLOW_UP.md) — description keyword checks, large-quantity case examples, and conservative interpretation limits. No cause or inventory-loss total is asserted. No source lines have been dropped or reclassified.

**Investigation 003 — duplicates:** [source-level invoice match results](docs/DUPLICATE_INVESTIGATION.md). The two -9,600 smudged-printing lines have consecutive *different* invoice IDs (556690, 556691) and are not eight-field exact duplicates. Across all 1,067,371 lines, the audit observed 34,335 extra exact matches, including 64 extra exact matches among the 3,457 negative non-C lines. These are not automatically erroneous records.

**Investigation 004 — consecutive invoices:** [seven-field near-matches across different invoice IDs](docs/CONSECUTIVE_INVOICE_FINDINGS.md). Of 36,182 numeric consecutive invoice-ID pairs, 166 distinct pairs share at least one exact seven-field invoice-line signature. In the negative non-C cohort, only four such matching pairs were found, including the -9,600 case and a three-invoice chain labeled `given away`. No cause or deduplication policy is asserted.

## Research directions (questions, not findings)

1. How sensitive is reported merchandise performance to cancellation, return and non-product definitions?
2. What is the pattern of purchasing across months and countries once the observation unit and coverage are established?
3. How does repeat purchasing vary across identifiable customers, and how much does missing customer identification limit that analysis?

See [research log](docs/RESEARCH_QUESTIONS.md). Initial priority is data integrity rather than rushing to visualizations.

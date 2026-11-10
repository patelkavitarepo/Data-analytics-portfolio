# Project 003 — Retail Intelligence

**Status:** Phase 01 / source and audit setup; findings and business definitions are **not yet verified**.

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

This repository does **not** redistribute the original dataset. Publisher-reported facts are not results from our own audit.

## First milestone: audit without cleaning

The audit reports raw row counts by sheet, date range, duplicate lines, missing values, `C`-prefixed cancellation codes, negative and zero quantities/prices, distinct countries, and the SHA-256 hash of the original workbook. No rows are removed. No sales or revenue measure is asserted before resolving returns, cancelled lines, non-merchandise items, and customer-ID missingness.

```bash
cd retail-intelligence
python -m pip install -r requirements.txt
python scripts/audit.py --download
python -m pytest -q
```

For an already downloaded workbook:

```bash
python scripts/audit.py --workbook data/raw/online_retail_II.xlsx
```

The first command downloads the official UCI archive, extracts the workbook and writes `outputs/initial_audit.json` (both ignored by git). Requires network access. The script has been tested against synthetic input; **the full source workbook has not yet been audited here**.

## Research directions (questions, not findings)

1. How sensitive is reported merchandise performance to cancellation, return and non-product definitions?
2. What is the pattern of purchasing across months and countries once the observation unit and coverage are established?
3. How does repeat purchasing vary across identifiable customers, and how much does missing customer identification limit that analysis?

See [research log](docs/RESEARCH_QUESTIONS.md). Initial priority is data integrity rather than rushing to visualizations.

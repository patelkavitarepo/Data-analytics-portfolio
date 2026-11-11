# Project 003 — Retail Intelligence | Portfolio Case Study (Draft)

**Project status:** Source-verified retrospective analysis and dashboard preview prepared; **Case 021 SKU-composition findings and final Power BI report pending**. The project is a portfolio investigation, **not audited financial reporting**.

## Executive question

**Did observed merchandise-like retail activity improve between January–November 2010 and the same months in 2011—or do a small number of unusually large invoice groups distort the headline?**

The answer from the source-reconciled exploratory **S2 gross positive-priced line amount** is nuanced. A **+2.90%** period increase coexists with **6.00% fewer recorded units** and **3.93% fewer monthly-summed qualifying invoice identifiers**. The upper **1%** of invoice-ID-month groups accounts for an increasing share of the measured amount. If those upper-tail groups are omitted *independently in each period, for sensitivity only*, the observed comparison falls to **+0.77%**.

**Recommendation:** Do **not** describe the +2.90% as established organic sales, demand, or revenue growth. Report both untrimmed and upper-tail-sensitive perspectives, then investigate product-code composition and unit-value conventions. Keep all observations; the upper tail is part of the recorded business.

## Data and independent verification

The analysis uses the historical [UCI Online Retail II dataset](https://archive.ics.uci.edu/dataset/502/online+retail+ii), including wholesalers. It contains **1,067,371** original invoice lines across two annual worksheets, with a repeated December 2010 publication overlap.

- **Case 008:** Built an explicitly provisional, **reversible** 1,044,848-line candidate analysis view with **22,523** exact cross-sheet copy links and complete original-row provenance. No original source row or within-sheet duplicate was deleted.
- **Case 009:** Defined alternative experimental positive-priced gross-line scenarios S0/S1/S2, separately treating ambiguous shipping, manual and discount codes and cancellation-coded rows.
- **Case 018:** Reproduced source cohorts, S0/S1/S2 money totals **and invoice-ID counts independently in SQLite**, with **100 passing tests**. [Verification](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42941460657).
- **Case 019:** Compared only **January–November** in both years and independently reconciled 25 monthly SQL aggregates, with **105 passing tests**. [Verification](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42944895542).
- **Case 020:** Compared upper-tail gross-amount concentration in invoice-ID-month aggregates, independently checking those totals against SQL, with **110 passing tests**. [Verification](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106).

All source-level data and customer identifiers remain out of the public aggregate artifacts.

## Business findings

| Exploratory metric | 2010 Jan–Nov | 2011 Jan–Nov | Change |
| --- | ---: | ---: | ---: |
| **S2 gross positive-priced line amount** (not accounting revenue) | **£8,639,086.69** | **£8,889,734.02** | **+2.90%** |
| Qualifying positive-priced source lines | **443,587** | **461,446** | **+4.03%** |
| **Sum of monthly** distinct qualifying invoice-ID counts (not verified orders) | **18,122** | **17,410** | **−3.93%** |
| Recorded positive units (not verified shipments) | **5,218,220** | **4,905,104** | **−6.00%** |
| Known-customer-ID coverage of S2 lines | **81.43%** | **76.51%** | **−4.92 percentage points** |
| Top 1% of invoice-ID-month groups: share of S2 gross | **16.06%** | **17.80%** | **+1.74 percentage points** |
| Median gross per qualifying invoice-ID-month group | **£300.58** | **£304.24** | **+1.22%** |
| S2 gross after omitting each year's top 1% of invoice-ID-month groups *for sensitivity only* | **£7,251,414.04** | **£7,307,316.86** | **+0.77%** |

**Concentration interpretation:** The independently selected upper-one-percent groups account for **£1,387,672.65** in 2010 and **£1,582,417.16** in 2011. Their **£194,744.51** arithmetic difference is about **77.7%** of the untrimmed **£250,647.33** period difference. But the upper groups do **not** contain the same invoice IDs across years and cannot be treated as a causal explanation for the change.

**Recorded-month interpretation:** **8 of 11** matched months have higher S2 gross amounts in 2011. November is the largest recorded matched-month S2 amount in each year, but that does not prove seasonality or marketing effectiveness. **December 2011 is incomplete** in the source and is deliberately excluded from the matched-month comparison.

**Customer-data interpretation:** Falling customer-ID coverage limits customer behavior and retention conclusions. Missing identifiers are not silently converted into invented customers.

## What the project prevented

The analysis avoided three common errors:

1. **Publication overlap mistaken for extra transactions:** the 22,523 exact December 2010 cross-sheet copies could inflate a broad gross positive-priced line scenario by **£438,852.65** if both annual sheets are naively stacked.
2. **Cancellations mistaken for known refunds:** C-prefixed invoice lines carry source cancellation codes, but their cash treatment is not verified; no cancellation amount is automatically netted into S0/S1/S2.
3. **Zero-price lines mistaken for a promotion:** the earlier Cases 015–017 showed no repeated same-SKU strict or multi-unit equal-quantity BOGO pattern on separate invoices, while unusual paid/£0 billing structures exist. Operational correction vs promotion remains an unverified explanation, not a finalized category.

## What a decision-maker should do

Use **descriptive source activity**, not unverified recognized revenue, for exploration. Evaluate upper-tail concentration alongside medians and monthly distribution, and investigate SKU quantity/mix changes before proposing operational action. Keep S0/S1/S2 sensitivity and unknown-customer coverage visible on the dashboard.

**No recommendation to delete outliers, restructure inventory, change prices, advertise a BOGO, or alter accounting entries is justified by these data alone.**

## Reproducible assets and next gates

- [Provisional KPI semantic dictionary](PROVISIONAL_KPI_DICTIONARY.md)
- [SQL workbench](SQL_KPI_WORKBENCH.md)
- [Matched-month activity findings](MONTHLY_BUSINESS_ACTIVITY.md)
- [Invoice concentration findings](INVOICE_CONCENTRATION_ANALYSIS.md)
- [Dashboard specification](DASHBOARD_SPEC.md)

**Case 021:** SKU-composition bridge script and tests committed; full-source verification pending. Its findings may refine this case study, not retroactively transform observational patterns into causal claims.

**Final publication gates:** verify Case 021; generate a genuine Power BI report or clearly labeled static portfolio dashboard; validate every chart against source-reconciled aggregates; retain independent source attribution and caveats; review draft PR #3 before merge.

**Methodological bottom line:** **Reproducible ≠ causal; gross positive-priced line amount ≠ recognized revenue; invoice identifier ≠ verified order; customer-ID coverage ≠ retention.**

# Project 003 — Retail Intelligence

**Status:** Source integrity audit, anomaly investigations, independent SQL KPI reconciliation, comparable-month business analysis, invoice concentration and the SKU composition bridge are **source-verified**. A [static executive dashboard](dashboard/index.html), [dashboard instructions](dashboard/README.md) and [portfolio case study](docs/PORTFOLIO_CASE_STUDY.md) are versioned on the draft branch. Financial definitions and causal interpretations remain provisional; a native Power BI `.pbix` is not yet built.

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
python scripts/investigate_invoice_batches.py
python scripts/investigate_population_batches.py
python scripts/investigate_sheet_overlap.py
python scripts/build_reversible_layer.py
python scripts/investigate_revenue_scenarios.py
python scripts/investigate_manual_code.py
python scripts/investigate_m_linkages.py
python scripts/investigate_m_bidirectional.py
python scripts/investigate_price_paradox.py
python scripts/investigate_mixed_price_invoices.py
python scripts/investigate_same_sku_price_pairs.py
python scripts/investigate_temporal_zero_paid_sku.py
python scripts/investigate_multiunit_weekly_context.py
python scripts/run_sql_kpi_workbench.py
python scripts/analyze_monthly_business_activity.py
python scripts/analyze_invoice_concentration.py
python scripts/analyze_sku_composition.py
python scripts/verify_dashboard_preview.py
python scripts/export_powerbi_aggregates.py
python -m pytest -q
```

For an already downloaded workbook:

```bash
python scripts/audit.py --workbook data/raw/online_retail_II.xlsx
```

The download command obtains the official UCI workbook. The investigations and source-reconciled analytical scripts save aggregate JSON results in `outputs/`, including `population_batch_prevalence.json`, `annual_sheet_overlap.json`, `reversible_layer_audit.json`, and `revenue_sensitivity.json` and `manual_code_investigation.json` and `manual_linkage_cases.json` and `manual_bidirectional_patterns.json` and `price_paradox.json` (outputs and workbook are ignored by Git). A successful GitHub Actions run audited the full source workbook and passed 72 synthetic-data tests. See [Investigation 001 findings](docs/NEGATIVE_QUANTITY_FINDINGS.md), including the cross-tab of negative quantities and cancellation prefixes.

**Hypothesis H001 follow-up:** [operational adjustment evidence](docs/H001_FOLLOW_UP.md) — description keyword checks, large-quantity case examples, and conservative interpretation limits. No cause or inventory-loss total is asserted. No source lines have been dropped or reclassified.

**Investigation 003 — duplicates:** [source-level invoice match results](docs/DUPLICATE_INVESTIGATION.md). The two -9,600 smudged-printing lines have consecutive *different* invoice IDs (556690, 556691) and are not eight-field exact duplicates. Across all 1,067,371 lines, the audit observed 34,335 extra exact matches, including 64 extra exact matches among the 3,457 negative non-C lines. These are not automatically erroneous records.

**Investigation 004 — consecutive invoices:** [seven-field near-matches across different invoice IDs](docs/CONSECUTIVE_INVOICE_FINDINGS.md). Of 36,182 numeric consecutive invoice-ID pairs, 166 distinct pairs share at least one exact seven-field invoice-line signature. In the negative non-C cohort, only four such matching pairs were found, including the -9,600 case and a three-invoice chain labeled `given away`. No cause or deduplication policy is asserted.

**Investigation 005 — surrounding invoice context:** [full invoice contents and batch clues](docs/INVOICE_BATCH_INVESTIGATION.md). Two -9,600 lines are standalone invoices preceded by another negative zero-price disposal-labeled invoice at 10:36. Six consecutive one-line `given away` invoices are recorded within three minutes. These patterns suggest related operational posting, but do not establish a cause or event count. [Successful workflow evidence](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42864663688).

**Investigation 006 — full population:** [invoice-sequence prevalence and comparison](docs/POPULATION_BATCH_FINDINGS.md). About 66.8% of candidate sheet-specific invoice instances belong to short consecutive runs, compared with 67.6% of positive-priced invoices; clustering itself is therefore not diagnostic. All 3,457 candidate lines are in one-line, candidate-only invoice instances. A possible **cross-sheet overlap** needs verification before aggregating invoices across years.

**Investigation 007 — annual worksheet overlap:** [confirmed repeated December 2010 records](docs/ANNUAL_SHEET_OVERLAP.md). The two annual worksheets contain **22,523 exact matching line copies** across **1,088 fully matching shared invoices**. All matches occur in December 2010. A naive positive-quantity, positive-price line-total calculation would count an extra **£438,852.65** from cross-sheet copies. This is a scenario, not certified company revenue. No source records have been modified. [Evidence](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42871691979).

**Investigation 008 — reversible candidate analysis layer:** [design, audit and all-row provenance](docs/REVERSIBLE_ANALYSIS_LAYER.md). A source-verified candidate view contains **1,044,848 lines** and retains **1,067,371 original row references** in a separate provenance ledger. Exactly **22,523** cross-sheet duplicate copies have canonical links to matching first-sheet rows. An alternative gross positive-priced line amount is £20,533,741.92 rather than £20,972,594.57 (difference £438,852.65). This view is *proposed*, not an approved cleaning or revenue rule. **Derived row-level files are in ignored `data/derived/` and are not uploaded to GitHub.** [Successful workflow](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42879978426).

**Investigation 009 — experimental gross-line scenarios:** [source-verified S0/S1/S2 sensitivity](docs/REVENUE_SCENARIOS.md). On the reversible candidate view, gross positive-priced amounts are **£20,533,741.92 (S0)**; **£20,063,792.35 (S1, minus named postage/billing codes)**; and **£19,723,764.52 (S2, also minus M and D)**. None is approved accounting revenue. C-prefixed cancellation amounts remain separate, not automatically recognized as refunds. **48 tests passed** on the [verified workflow](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42883445158). No original or candidate rows were modified.

**Investigation 010 — ambiguous Manual code M:** [M line distribution and full-invoice context](docs/MANUAL_CODE_FINDINGS.md). Of **861 positive-priced M lines** (£339,629.94 in the reversible candidate view), **534** appear on invoices that also have non-M positive-priced lines; 480 of 788 M-containing invoice IDs contain such other positive-priced items. The median M line amount is **£8.85**, while the top ten lines account for **31.91%** of its amount. We should **not automatically exclude or recognize M as sales**: the source label is ambiguous. The workflow [passed 53 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42886173182). No source rows changed.

**Investigation 011 — high-value Manual and possible cancellation linkages:** [strict candidate matching and time-order counterexamples](docs/MANUAL_LINKAGE_FINDINGS.md). On the reversible candidate view, **80** strict positive/C-negative line pair comparisons met known customer, country, quantity, price and cancellation-after-positive criteria within 90 days; **51** were reciprocal one-to-one *candidate* pairs, **not verified refunds**. The £25,111.09 negative `C512770` at 16:52 and positive `512771` at 16:53 on June 17, 2010 illustrate why close-time reversal/reposting hypotheses need separate scrutiny: the negative precedes the positive and their customer-ID availability differs. **59 tests passed** on the [successful full-source CI run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42890694308). No business classifications or source rows changed.

**Investigation 012 — short-time bidirectional Manual sign flips:** [candidate counts and uncertainty classifications](docs/MANUAL_BIDIRECTIONAL_FINDINGS.md). Within 5 minutes, **171** M negative/positive line comparisons share abs quantity, unit price and country; **168** lack a conflicting known customer ID, including **104 negative-first**, **63 positive-first**, and one same-minute comparison. Of those 168, **78** have known identical customer IDs, **78** have one missing, and **12** have both missing. These are *descriptive lookalikes*, not verified refunds or corrections; no rows or financial definitions changed. [Successful full-workbook workflow: 67 passing tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42898160193).

**Investigation 013 — The Price Paradox:** [verified zero- and negative-unit-price findings](docs/PRICE_PARADOX_FINDINGS.md). Among **2,631** positive-quantity zero-priced lines, **2,561** lack customer IDs, **1,642** lack descriptions, and **1,861 of 1,986** affected invoice IDs consist exclusively of zero-priced lines. The **five negative-unit-price, positive-quantity lines** are all `A`-prefixed, stock code `B`, description `Adjust bad debt`, and total **−£158,676.14** in signed line amount. None is treated as an ordinary negative-priced merchandise sale or verified accounting write-off. [Successful original-workbook workflow (72 tests)](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42912802097). No source or KPI rules changed.

**Investigation 014 — The Mixed-Price Mystery:** [source-verified invoice context](docs/MIXED_PRICE_INVOICE_FINDINGS.md). The original workbook confirms **125 mixed-price invoice IDs** containing **709 zero-price lines** and **7,660 positive-priced lines**; all 709 zero-price lines on mixed invoices have descriptions, versus **1,642 missing descriptions among 1,922 zero-priced lines on zero-price-only invoices**. **43** zero-priced lines share a stock code with paid lines on the same invoice, across **33** invoice IDs. The verified full-source workflow [passed 77 synthetic tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42933178973). This does not establish promotions, gifts, inventory adjustments or revenue, and no rows, provenance or KPI rules were changed.

**Investigation 015 — Same-SKU mixed-price source audit:** [source-verified pattern results](docs/SAME_SKU_MIXED_PRICE_FINDINGS.md). Among **43** zero-priced/positive-priced same-SKU invoice-line comparisons across **33 invoices**, only **10** have equal quantities; all 43 share a recorded minute, **33** have both customer IDs missing, and some paid/£0 quantities differ dramatically (e.g. 1 versus 10,200). The full original-workbook [audit succeeded with 83 synthetic tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42935952251). No BOGO, duplicate, correction, cause, or financial rule is established; all source rows and provenance remain unchanged.

**Investigation 016 — Timed BOGO hypothesis:** [source-verified recurrence findings](docs/TEMPORAL_BOGO_HYPOTHESIS.md). Of **32** stock codes with any same-invoice zero-price and positive-price pairing, **five** recur across different invoices, **two** recur within seven days, and **four** within 30 days. Only **five invoice/SKU groups** have an exact one-paid-unit + one-zero-unit structure, and **none** recur across different invoices for the same stock code. The [original-workbook audit passed 89 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42937165126). This weakens a repeat literal-BOGO interpretation but does not establish corrections or rule out different promotions. No data or KPI definitions changed.

**Investigation 017 — The Multi-Unit Mystery:** [source-verified multi-unit and same-week comparison](docs/MULTIUNIT_WEEKLY_CONTEXT.md). Across **43** invoice+SKU paid/£0 groups, only **10** have equal total quantities (**5** strict 1+1; **5** multi-unit equality), and **none** of the five multi-unit cases repeats on another invoice for the same SKU. Calendar-week paid-only comparisons expose how small denominators can make apparent concentrations misleading. The [original-workbook audit passed 95 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42940297437). No BOGO, correction, shipment, or financial meaning is established.

**Investigation 018 — SQL exploratory KPI workbench (source verification pending):** [semantic dictionary](docs/PROVISIONAL_KPI_DICTIONARY.md), [SQL workbench design](docs/SQL_KPI_WORKBENCH.md), and [SQLite classification view](sql/001_provisional_retail_kpis.sql). Recomputes mutually exclusive line classes and S0/S1/S2 amounts using a separate SQL engine; it fails if aggregate row counts, invoice-ID counts or source scenario amounts disagree with Case 009. Monthly merchandise-like gross line activity and cancellations are explicitly exploratory, not recognized sales. The source-data SQL run is not yet verified.

**Investigation 019 — Monthly business activity:** [source-backed Jan–Nov comparisons](docs/MONTHLY_BUSINESS_ACTIVITY.md). Independent verified SQL output shows **£8.639M in 2010 versus £8.890M in 2011 (+2.90%) in provisional S2 gross positive-priced line amounts**, with qualifying S2 lines up 4.03% but sum of monthly distinct invoice-ID counts down 3.93%; known-customer-ID coverage drops by 4.92 percentage points. These are **not revenue, verified orders or customer demand**. The separate like-for-like monthly analysis passed the [original-workbook audit with 105 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42944895542) and reconciled the reported 25 source months back to Case 018.

**Investigation 020 — Invoice concentration (verified):** [original-source upper-1% sensitivity and monthly context](docs/INVOICE_CONCENTRATION_ANALYSIS.md). Among Jan–Nov S2 qualifying invoice-ID-month groups, the largest one percent accounts for **16.06%** of gross positive-priced line amount in 2010 versus **17.80%** in 2011. Omitting those groups separately for sensitivity changes the apparent S2 increase **+2.90% → +0.77%**, substantially weakening a simple growth narrative. The [original-source audit passed 110 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106). No source data, KPI policy or actual invoices are altered.

**Investigation 021 — SKU composition (verified):** [full-source-verified arithmetic bridge](docs/SKU_COMPOSITION_BRIDGE.md). The source-checked Jan–Nov S2 **+£250,647.33** difference comprises shared-SKU recorded quantities (**−£992,716.27**) and effective unit-value residual (**−£141,027.84**), 2011-only stock-code amounts (**+£2,058,492.44**) and 2010-only amounts (**−£674,101.00**). The [original workbook audit passed 115 tests](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42949051946). This is an exact arithmetic identity, not proof of inflation, product launches, revenue or demand.

**Portfolio narrative (draft):** [Evidence-first retail case study](docs/PORTFOLIO_CASE_STUDY.md) and [dashboard specification](docs/DASHBOARD_SPEC.md). Verified results through Case 020 support aggregate-only executive reporting: +2.90% matched Jan–Nov S2 gross line-amount change, versus +0.77% after independently omitting each year's largest 1% invoice-ID-month groups as a sensitivity analysis. A standalone HTML dashboard preview and Power BI-ready aggregate CSV import package were prepared from the [Case 020 GitHub Actions summary artifact](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106), not from customer-level source exports. These generated files are not yet hosted in the repository and are not a Power BI .pbix. Case 021 original-source validation remains in progress.\n\n## Research directions (questions, not findings)

1. How sensitive is reported merchandise performance to cancellation, return and non-product definitions?
2. What is the pattern of purchasing across months and countries once the observation unit and coverage are established?
3. How does repeat purchasing vary across identifiable customers, and how much does missing customer identification limit that analysis?

See [research log](docs/RESEARCH_QUESTIONS.md). Initial priority is data integrity rather than rushing to visualizations.

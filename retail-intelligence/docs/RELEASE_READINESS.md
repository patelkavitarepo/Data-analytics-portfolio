# Project 003 — Release readiness review

**Review date:** November 11, 2026  
**Branch:** `feat/retail-intelligence-audit`  
**Pull request:** [draft PR #3](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/3), deliberately unmerged  
**Recommendation:** **Evidence and static portfolio preview ready for a final reviewer check; native Power BI and PR merge remain outstanding.**

## Verified release gates

| Gate | Evidence | Status |
| --- | --- | --- |
| Source/license attribution | [UCI Online Retail II, Daqing Chen, DOI 10.24432/C5CG6D, CC BY 4.0](https://archive.ics.uci.edu/dataset/502/online+retail+ii); source workbook SHA-256 recorded in project README | Complete |
| Reversible source treatment | 1,067,371 original rows, 22,523 exact cross-sheet publication-copy links, 1,044,848 candidate lines; source/provenance retained | Complete |
| Cohort and SQL experimental gross scenario reconciliation | [Run #42941460657](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42941460657), 100 synthetic tests | Complete |
| Matched January–November activity comparison | [Run #42944895542](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42944895542), 105 synthetic tests | Complete |
| Upper-one-percent invoice-ID-month sensitivity | [Run #42945421106](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42945421106), 110 synthetic tests | Complete |
| Four-term SKU composition bridge | [Run #42949051946](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42949051946), 115 synthetic tests | Complete |
| Versioned static HTML dashboard and mismatch guardrail | [Run #42953226803](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42953226803), **120 synthetic tests passed** and `verified=true` for matching dashboard claims | Complete |
| Power BI aggregate CSV reproducibility | `scripts/export_powerbi_aggregates.py`, eight explicit aggregate-only output schemas, four added synthetic tests, separate CI artifact `retail-powerbi-aggregates` | **Pending full-source CI check** |
| Source rows/customer and invoice IDs in aggregate artifacts | CSV exporter uses explicit allowed columns and intentionally does not emit individual invoice/customer IDs; original source and row-level candidate files remain ignored | Code guardrails in place; inspect the new CI artifact before public use |
| Native Power BI authoring | This repository has an HTML dashboard and CSV import files, not a Power BI Desktop `.pbix` | Not done |
| Independent project/visual QA and final PR review | Review figures, labels, color/contrast and mobile layout; inspect the full changed-file list before deciding to merge | Pending |

## Defensible business conclusion

- **Observed:** Experimental S2 merchandise-like positive-priced line amount for January–November rises from **£8,639,086.69** (2010) to **£8,889,734.02** (2011), a **+2.90%** difference. Recorded positive units declined 6.00% and monthly-summed qualifying invoice-ID counts declined 3.93%.
- **Sensitivity:** Highest 1% of invoice-ID-month groups contribute **16.06% (2010)** and **17.80% (2011)** of S2 gross. Omitting those groups independently as a sensitivity exercise changes the observed S2 difference to **+0.77%**. **No outlier was deleted.**
- **Composition:** The +£250,647.33 difference decomposes arithmetically into shared-stock-code quantity **−£992,716.27**, shared-code effective-value-per-unit residual **−£141,027.84**, codes seen only in 2011 **+£2,058,492.44**, and codes seen only in 2010 **−£674,101.00**.
- **Limitations:** These are not official revenue, verified completed orders, fulfilled units, profit, organic growth, formal inflation or causal product launches. C-prefix source cancellations are not mechanically treated as cash refunds; £0 lines are not verified promotional redemptions.

## Reviewer checklist before merger

- [x] Clear original dataset attribution, DOI/license and source hash in README
- [x] Every original source row accounted for without deleting original data
- [x] Experimental S0/S1/S2 distinctions and cancellation/zero-price limitations disclosed
- [x] Case 018–021 source results reconciled to independently verified SQL outputs
- [x] Dashboard claims verified by source-aggregate CI (120 passing tests)
- [x] Static executive dashboard and written case study included in draft branch
- [x] Power BI CSV exporter, allowed schemas and synthetic tests implemented
- [ ] Full-source new CI run for Power BI export success; inspect artifact names, file counts, and privacy controls
- [ ] Independent manual review of dashboard appearance and all analysis assumptions
- [ ] Confirm whether the release target is **HTML portfolio case study only** or includes a native Power BI report
- [ ] Final read-through of draft PR #3's complete changed-file scope (a large research PR)
- [ ] Explicit user approval before marking PR ready for review or merging to `main`

**Release policy:** Publishing an HTML report as a static portfolio piece can be separate from producing a Power BI `.pbix`. Do not imply a native report exists. Keep this PR a draft until its remaining gates are explicitly satisfied.

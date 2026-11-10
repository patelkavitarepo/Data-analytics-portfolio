# Investigation 001 — Negative-quantity records

**Status:** Reproducible first-pass findings from the original UCI workbook; no row-level cause classification or cleaning decision.

## Evidence and provenance

- **Dataset:** Online Retail II (UCI dataset 502), Daqing Chen: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **Workbook SHA-256:** `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- **Successful audit and investigation:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42851689386
- **GitHub Actions output:** `retail-initial-audit` artifact with `initial_audit.json` and `negative_quantity_investigation.json`
- **Reproducible command:** `python scripts/audit.py --download` followed by `python scripts/investigate_negative_quantities.py`
- **Synthetic-data validation:** Six tests passed in the audit workflow.
- **Observation unit:** Invoice **line**, not unique transaction, document, customer, or product.
- **Reconciliation:** All 1,067,371 rows accounted for; numeric quantity present on every row.

## Observed cross-tab

| Invoice number prefix | Quantity negative | Quantity zero or positive | Total |
| --- | ---: | ---: | ---: |
| Starts with `C` | 19,493 | 1 | 19,494 |
| Does not start with `C` | 3,457 | 1,044,420 | 1,047,877 |
| **Total** | **22,950** | **1,044,421** | **1,067,371** |

UCI documents a `C`-prefixed invoice as a *cancellation*. The invoice prefix and sign are distinct fields. Do not equate every negative line with a customer return.

## The 3,457 negative-quantity rows **without** a C prefix

| Attribute observed | Count / value |
| --- | --- |
| Distinct invoice IDs | 3,393 |
| Zero unit price | **3,457 of 3,457** |
| Missing customer ID | **3,457 of 3,457** |
| Country United Kingdom | **3,457 of 3,457** |
| Missing description | **2,689** |
| Year 2009–2010 sheet | 2,121 |
| Year 2010–2011 sheet | 1,336 |
| Negative quantity range | -9,600 through -1 |

Descriptions among those that are nonblank include `check` (123 rows), `damages` (84), `?` (83), `damaged` (78), `missing` (27) and `sold as set on dotcom` (20). These are **counts of observed descriptions**, not verified causes or mutually exclusive business processes.

## Other discrepancies and checks

- One `C`-prefixed line has **positive quantity 1**; it uses stock code `M` and description `Manual`, and its customer ID is missing.
- Among the 19,493 `C`-prefixed negative lines, 749 have a missing customer ID. Their minimum quantity is -80,995.
- These subsets were tabulated without excluding duplicates, zero prices, or missing identifiers.

## Hypothesis (not a finding)

The simultaneous combination of negative quantity, zero price, no identified customer, and descriptions such as damage/check/missing is consistent with *possible stock corrections or other internal administrative entries*, but cannot establish the business cause. The source documentation does not conclusively define non-`C` negatives.

## Decision log

- **D001:** Retain all original rows for investigation. **No cleaning rules approved.**
- **D002:** Label records using *observed signals* (sign, C-prefix, price, customer-ID status); do **not** create definitive 'customer return' / 'inventory adjustment' labels yet.
- **D003:** Keep calculation of merchandise sales or net revenue postponed until line types and exclusions are defensible.
- **Next:** Examine invoice-level mixtures, special stock codes, and whether unmarked negative entries resemble warehouse adjustments; quantify impact on candidate KPI definitions.

## Interpretation cautions

The records are historical and observational. Repeated invoice IDs can contain several lines. Missing descriptions do not prove warehouse damage. A £0 unit price does not by itself indicate that a line is valid or invalid; it only affects simple line-amount calculations. No distinct-customer or financial outcome has been inferred here.

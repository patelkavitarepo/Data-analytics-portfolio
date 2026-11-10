# Investigation 005 — Invoice-level neighborhood and batch patterns

**Date:** November 10, 2026  
**Project:** 003 Retail Intelligence  
**Status:** Full original-workbook check completed successfully; interpretation remains provisional.

## Evidence and reproducibility

- **Source:** UCI Online Retail II (dataset 502), original workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- **Completed GitHub Actions check:** https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42864663688
- **Script:** `scripts/investigate_invoice_batches.py`; test module `tests/test_invoice_batches.py`. Re-run with `python scripts/investigate_invoice_batches.py` after downloading workbook.
- **Output:** `outputs/invoice_batch_neighborhoods.json` (workflow artifact `retail-initial-audit`). Full invoice contents include all source lines for a selected invoice ID on its original worksheet.
- **Privacy:** Customer IDs are not exported; only customer-ID missingness is reported.
- **Cleaning:** None. No original rows deleted or changed, no financial totals computed.

## Case A — Printing defects, June 14, 2011

| Invoice | Timestamp | Lines in complete invoice | Description | Unit price | Missing customer ID |
| --- | --- | ---: | --- | ---: | --- |
| `556687` | 10:36 | 1 | `Printing smudges/thrown away` | £0 | Yes |
| `556690` | 10:37 | 1 | `printing smudges/thrown away` | £0 | Yes |
| `556691` | 10:37 | 1 | `printing smudges/thrown away` | £0 | Yes |

- All three lines have negative quantities. `556690` and `556691` each specifically contain -9,600 units of stock code `23005`. Both are complete single-line invoices on adjacent Excel rows (225531 and 225532).
- `556687` (Excel row 225530) directly precedes both and has a matching disposal-oriented description, negative quantity, £0 price and no customer ID. The full-invoice summary does not independently prove that its quantity or stock code matches the -9,600 pair.
- In the inclusive ±5-minute window around 10:37, precisely **three lines from three invoice IDs** meet the negative, £0, missing-customer numeric-invoice pattern; all three are the above.
- The nearby numeric invoice IDs before these records include ordinary positive-price, positive-quantity sales (e.g., `556682`–`556685`).
- **Interpretation:** The cluster is consistent with concentrated administrative stock/disposal recording rather than normal customer refunds, but it does not independently prove whether `556690` and `556691` represent independent disposal batches or repeated posting of the same movement.

## Case B — Given-away chain, July 12, 2010

| Invoice | Time | Lines in complete invoice | Quantity sign | Unit price | Description |
| --- | --- | ---: | --- | ---: | --- |
| `515459` | 15:46 | 1 | Negative | £0 | `given away` |
| `515460` | 15:46 | 1 | Negative | £0 | `given away` |
| `515461` | 15:46 | 1 | Negative | £0 | `given away` |
| `515462` | 15:47 | 1 | Negative | £0 | `given away` |
| `515463` | 15:47 | 1 | Negative | £0 | `given away` |
| `515464` | 15:48 | 1 | Negative | £0 | `given away` |

- All six invoices also lack customer IDs.
- The original three-invoice near-match finding applies to `515459` / `515460` / `515461`: each has stock code `20852` and quantity -1,000. The later three invoices share the description and other operational shape but have not been verified as identical seven-field matches.
- The ±5-minute window around 15:46 contains **six lines in six invoice IDs**, all satisfying the negative, £0, no-customer condition. Immediately before (e.g. `515457`, `515458`) and after (e.g. `515465`, `515466`) were normal positive-price lines.
- **Interpretation:** This is stronger evidence of a small run of related, non-customer stock postings. It is **not** proof that the event was a single giveaway, six independent giveaways, or duplicate accounting.

## Case C — Small negative pair, January 10, 2011

| Invoice | Time | Complete invoice lines | Stock code | Quantity | Unit price | Description |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `540678` | 16:21 | 1 | `21667` | -1 | £0 | Missing |
| `540679` | 16:21 | 1 | `21667` | -1 | £0 | Missing |

- Both have no customer IDs, appear on consecutive worksheet rows, and share the exact same timestamp.
- Unlike Cases A and B, the ±5-minute window includes a large ordinary order (e.g., `540681` with 289 positive-quantity lines), so clustering by time **alone** does not prove that surrounding transactions are stock adjustments.
- The immediately preceding numeric invoices `540673`–`540675` contain zero-priced positive-quantity lines with descriptions `found` / `Found`. This is suggestive of stocktaking, but it is **not** proven to be linked to `540678` or `540679`.
- **Interpretation:** Evidence of mixed stock-related and regular transactions in local time, not of a uniform batch across the window.

## Synthesis and decisions

**Supported:** Invoices are often complete single-line entries during these unusual negative-quantity patterns. Near the `556690` / `556691` pair, another disposal-labeled, unpriced negative line occurs one minute earlier. The `given away` case contains six consecutive, one-line, zero-price, anonymous negative postings within three minutes. These observations strengthen **H001: some non-C negative lines represent operational inventory adjustments rather than customer returns**.

**Unresolved:** Whether any same-time, same-product pair represents two different events versus repeated bookkeeping. The dataset does not include a unique source event ID or staff/workflow metadata. No specific employee action, fraud, theft or physical loss amount can be inferred.

- **D012:** Preserve all original invoice rows, including near-matches and exact duplicates.
- **D013:** Label these cases `possible operational recording batches`, not confirmed stock losses, returns or duplicate posting errors.
- **D014:** Treat temporal proximity as supportive context only; do not make a universal batch rule from three hand-picked examples.
- **Next research step:** Explore how frequent these exact operational-looking single-line invoice runs are across *all* negative non-C rows, and assess candidate KPI definitions with explicitly documented exclusions. Any financial value requires defensible product prices/costs and business semantics.

## Limitations

- The case studies are **selected examples**, so they are not a random sample nor a representative estimate of frequency.
- The original dataset timestamps are recorded to minute precision; equal timestamps do not guarantee simultaneous actions.
- Numeric invoice proximity and complete invoice summaries cannot determine how a retailer's original software generated invoice IDs.
- No individual customer IDs are published, and no raw dataset is redistributed in the repository.

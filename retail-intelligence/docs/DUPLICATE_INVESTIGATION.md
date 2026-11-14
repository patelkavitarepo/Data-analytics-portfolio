# Investigation 003 — Exact duplicate invoice lines

**Date:** November 10, 2026  
**Status:** Verified against original UCI Online Retail II workbook, hypothesis open; source rows unchanged.

## Evidence
- UCI Online Retail II, original Excel workbook SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
- [Successful GitHub Actions investigation](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/42859519258), 13 tests passed.
- [Reproducible script](../scripts/investigate_duplicates.py), report artifact `duplicate_investigation.json`.
- Eight exact-match keys: `invoice_no`, `stock_code`, `description`, `quantity`, `invoice_date`, `unit_price`, `customer_id`, `country`. Source row and sheet are retained only as locators and are **not** part of the match key.
- Exact duplicate **extra copies after first** and **all members of duplicate groups** are deliberately separate counts.

## Dataset-wide observations

| Measure | Original workbook |
| --- | ---: |
| Total invoice lines | 1,067,371 |
| Extra copies of exact eight-field matches | 34,335 |
| Rows belonging to exact-match groups, including first copies | 67,242 |
| Number of distinct repeated key groups | 32,907 |
| Largest exact-match group size | 20 |

An identical line could be an accidental duplicate or a legitimate second line with indistinguishable fields. No source-level transaction event ID resolves this.

## Exact duplicates by observed cohort

| Cohort | Raw lines | Extra copies | Lines in repeated groups | Hypothetical lines if first copy retained |
| --- | ---: | ---: | ---: | ---: |
| Negative quantity, non-C invoice | 3,457 | **64** | 128 | 3,393 |
| Negative quantity, C-prefixed invoice | 19,493 | 390 | 774 | 19,103 |
| All remaining lines | 1,044,421 | 33,881 | 66,340 | 1,010,540 |
| **All** | **1,067,371** | **34,335** | **67,242** | **1,033,036** |

**Hypothetical** figures are only sensitivity measures; **no source data was modified or cleaned**.

## The two -9,600-unit smudged-printing records

Contrary to our initial suspicion, these entries are **not eight-field exact duplicates** because the invoice IDs differ. The script traced them to adjacent Excel rows.

| Field | Record A | Record B |
| --- | --- | --- |
| Invoice ID | `556690` | `556691` |
| Stock code | `23005` | `23005` |
| Description | `printing smudges/thrown away` | Same |
| Quantity | -9,600 | -9,600 |
| Unit price | £0 | £0 |
| Timestamp | 2011-06-14 10:37:00 | Same |
| Customer ID | Missing | Missing |
| Country | United Kingdom | Same |
| Sheet | Year 2010-2011 | Same |
| Original Excel row | 225531 | 225532 |

**Observed:** Consecutive invoice IDs, identical timestamps, consecutive workbook rows and the same negative-quantity value. **Not established:** Whether these represent (a) two actual stock disposal batches, (b) a second entry or correction of one event, or (c) some other administrative process. Do **not** assert a 19,200-unit loss on the strength of this pair alone.

## Decisions

- **D006:** Preserve both 9,600-unit records as separate *source observations*. They are not exact duplicates; do not collapse by stock/date/time alone.
- **D007:** Preserve the 64 extra exact-match rows in the negative non-C cohort until the business meaning of repeated line items is justified.
- **D008:** Do not treat the 34,335 extra exact copies as confirmed data errors, or as cash/inventory losses.

**Update — Investigation 004:** [Consecutive invoice findings](CONSECUTIVE_INVOICE_FINDINGS.md) show 4 matching consecutive-ID pairs within the negative non-C cohort, including the `556690`/`556691` pair. Their pattern is rare within that cohort but not unique; do not infer whether the two entries represent one or two operational events.

## Follow-up

**R001d:** Test *near*-duplicate patterns (same stock code, date/time, quantity, price, description, customer, and country but **different invoice IDs**) and check how common consecutive invoice numbers are. A repeated pattern could reflect system batching or accidental double entry; the dataset alone may not adjudicate the cause.

**R001e:** Compare financial KPIs under clearly stated, alternative treatment of exact duplicate lines before deciding any exclusion policy. Document the effect by year, channel and product and distinguish sales lines from administrative zero-price entries.

## Limits

This is an exact-field test, not a verified loss-prevention review. A repeated line is not independent evidence that an employee was involved. Two same-time rows may share a bookkeeping operation. All original records, including suspicious ones, remain intact.

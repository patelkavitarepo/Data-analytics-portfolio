### Definitions and analytical contract

- **Request:** one unique source request identifier. Duplicate/missing IDs halt publication; no arbitrary deduplication.
- **Creation cohort:** calendar year 2025 in San Francisco local time. Floating source timestamps are interpreted in `America/Los_Angeles`, converted to UTC; ambiguous/nonexistent creation times halt validation. Aggregates use San Francisco local creation date; elapsed horizons use UTC timestamps and exact 24-hour days.
- **Agency/category/neighborhood:** source labels, not manually inferred organizational boundaries. Missing labels become `Unknown`. Category is a coarse complexity proxy; residual complexity remains.
- **As of:** extraction completion timestamp, held fixed for all dashboard calculations. Current snapshot statuses are not historical event logs.
- **Valid administrative closure:** status is `closed`, closure timestamp is present, creation ≤ closure ≤ as of. This does not establish confirmed physical resolution. Inconsistent records remain in rate denominators but cannot count as successful closures.
- **7-/30-day eligible cohort:** age at extraction ≥ the exact elapsed horizon (24-hour days). Every eligible request, including unresolved or inconsistent cases, enters the denominator. Numerator: valid administrative closure within ≤7/30 elapsed days. No eligibility shortcut based on early closure.
- **Median/P90:** nearest-rank quantile among valid closed cases only, estimated from floored elapsed-day bins. Displayed values are lower bounds with error <1 day. They are subject to closed-case selection bias; never interpreted as time to eventual resolution for the full cohort.
- **Additive cube:** San Francisco local creation date × category × agency × neighborhood × duration_day. `duration_day=-1` denotes no valid observed closure. `requests`, `eligible7`, `closed7`, `eligible30`, `closed30`, `closed_valid` are additive counts. No IDs, addresses, descriptions or coordinates are published.
- **Comparable cell:** month/category/unit and the pooled other-unit peer group each have ≥30 30-day eligible requests. This per-cell stability rule is an additional documented screening choice.
- **Category-adjusted gap:** focal agency's closure rate minus all other agencies' rate in the same month/category, in percentage points. The displayed pair-level gap weights monthly gaps by focal eligible requests. This is a within-category benchmark, not a causal estimate or an agency-wide standardized ranking. Categories without peer overlap are omitted and never assigned a zero gap.
- **Persistent candidate:** ≥3 comparable months and ≥90 comparable requests; gap ≤−10 points in ≥half of comparable months (rounded up), minimum two. Sensitivity repeats at −15 points. No multiple-testing correction or causal attribution is claimed. Missing comparison months are excluded and the comparable-month count is displayed.
- **Recurring reporting:** category/neighborhood/month request intensity. Without address-level linkage, repeat reports cannot establish repeated failures at one physical location.
- **Geography:** neighborhood labels only; Unknown coverage shown. No population, service exposure or need denominator. Heatmap cells require ≥30 eligible requests. No unverified map boundaries are used.
- **Coverage:** count reconciliation and unchanged API `rowsUpdatedAt` are checks of extraction consistency, not proof of all real service events, immutable snapshots, or source correctness. Deleted/revised records and unreported needs cannot be measured.

### Provisional DataSF source mapping

This mapping is not claimed verified until a live metadata check passes. Any missing column halts extraction. Review source definitions and change the mapping explicitly when needed.

| Common field | Candidate DataSF field |
|---|---|
| request_id | service_request_id |
| created_at | requested_datetime |
| closed_at | closed_date |
| status | status_description |
| category | service_name |
| agency | responsible_agency |
| neighborhood | neighborhoods_sffind_boundaries |

### Quality ledger

The refresh records missing/duplicate IDs, missing creation time, negative duration, future timestamps, closed-without-date, nonclosed-with-date, unknown status and missing dimensions. Identity/cohort failures block publication. Other inconsistencies remain explicit, conservatively contribute no closure success, and must be reviewed before drawing conclusions. No statistical confidence interval is supplied; sample sizes and sensitivity are screening context, not uncertainty elimination.

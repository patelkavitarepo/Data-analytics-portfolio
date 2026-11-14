"""Case 019: comparable recorded-month business activity from Case 018 SQL output.

Only aggregate, already verified SQLite results are loaded. No row-level
source records or customer IDs are accessed, published, or transformed.
This is NOT a recognized-revenue or demand-growth estimator.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path


MONEY = "s2_gross_positive_line_amount_gbp_not_accounting_revenue"
LINES = "s2_positive_priced_lines"
IDS = "s2_distinct_qualifying_invoice_ids_not_orders"
UNITS = "s2_recorded_positive_units_not_verified_shipments"
KNOWN = "s2_known_customer_id_lines"


def _amount(value) -> Decimal:
    return Decimal(str(value))


def summarize_comparable_months(
    source: dict, first_year: int = 2010, second_year: int = 2011,
    months: tuple[int, ...] = tuple(range(1, 12)),
) -> dict:
    if not source.get("agrees_with_case_009_counts_invoice_ids_and_amounts"):
        raise ValueError("Unverified or unreconciled SQL source is not eligible")
    rows = source["monthly_s2_recorded_activity"]
    unique = {}
    for line in rows:
        key = str(line["recorded_month"])
        if key in unique:
            raise ValueError("Duplicate SQL monthly aggregates: " + key)
        if len(key) != 7 or key[4] != "-" or not key[:4].isdigit() or not key[5:7].isdigit():
            raise ValueError("Unexpected recorded month label: " + key)
        unique[key] = line
    if not months or len(set(months)) != len(months) or any(m < 1 or m > 12 for m in months):
        raise ValueError("Explicit non-empty valid comparable-month set required")
    chosen = {}
    for year in (first_year, second_year):
        entries = []
        for m in months:
            key = f"{year:04d}-{m:02d}"
            if key not in unique:
                raise ValueError("Missing requested comparable month: " + key)
            entries.append(unique[key])
        chosen[year] = entries

    def period(year: int) -> dict:
        arr = chosen[year]
        gross = sum((_amount(r[MONEY]) for r in arr), Decimal("0"))
        lines = sum(int(r[LINES]) for r in arr)
        id_month_pairs = sum(int(r[IDS]) for r in arr)
        units = sum(_amount(r[UNITS]) for r in arr)
        known = sum(int(r[KNOWN]) for r in arr)
        if not lines or not id_month_pairs:
            raise ValueError("Zero denominator for a selected reporting period")
        if not 0 <= known <= lines:
            raise ValueError("Impossible customer-ID coverage")
        return {
            "year": year,
            "included_recorded_months": [r["recorded_month"] for r in arr],
            "s2_gross_positive_line_amount_gbp_not_revenue": round(float(gross), 2),
            "s2_lines": lines,
            "sum_monthly_distinct_s2_invoice_ids_not_distinct_orders_across_period": id_month_pairs,
            "recorded_s2_positive_units_not_fulfilled_shipments": float(units),
            "s2_known_customer_id_lines": known,
            "s2_known_customer_id_line_share": round(known / lines, 6),
            "gross_line_amount_per_invoice_id_month_pair_not_aov": round(float(gross) / id_month_pairs, 2),
        }

    earlier, later = period(first_year), period(second_year)
    a, b = _amount(earlier["s2_gross_positive_line_amount_gbp_not_revenue"]), _amount(
        later["s2_gross_positive_line_amount_gbp_not_revenue"]
    )
    if a == 0:
        raise ValueError("Earlier gross line amount is zero")
    yoy = []
    for m in months:
        old, new = unique[f"{first_year:04d}-{m:02d}"], unique[f"{second_year:04d}-{m:02d}"]
        old_money, new_money = _amount(old[MONEY]), _amount(new[MONEY])
        yoy.append({
            "calendar_month_number": m,
            "earlier_recorded_month": str(old["recorded_month"]),
            "later_recorded_month": str(new["recorded_month"]),
            "earlier_s2_gross_positive_line_amount_gbp": float(old_money),
            "later_s2_gross_positive_line_amount_gbp": float(new_money),
            "change_pct_not_demand_growth": round(float(
                (new_money / old_money - 1) * 100
            ), 2) if old_money != 0 else None,
        })

    # Validate the monthly rollup is consistent with the independent
    # full-source SQL S2 amount; allow pennies from per-month rounding.
    all_months_total = sum((_amount(r[MONEY]) for r in rows), Decimal("0"))
    full_s2 = _amount(source["scenario_reconciliation"][
        "S2_also_exclude_manual_and_discount_code_candidates"
    ]["hypothetical_gross_line_amount_gbp"])
    if abs(all_months_total - full_s2) > Decimal("0.05"):
        raise AssertionError("Sum of monthly S2 amounts does not match SQL source S2 total")
    if sum(int(r[LINES]) for r in rows) != int(source["scenario_reconciliation"][
        "S2_also_exclude_manual_and_discount_code_candidates"
    ]["lines"]):
        raise AssertionError("Sum of monthly S2 line counts does not reconcile")

    return {
        "status": "source_reconciled_comparable_month_activity_not_verified_revenue_growth",
        "source_is_case_018_sql_aggregates": True,
        "comparison": f"{first_year} vs {second_year}; same calendar months: {list(months)}",
        "earlier": earlier,
        "later": later,
        "s2_gross_positive_line_amount_change_gbp": round(float(b - a), 2),
        "s2_gross_positive_line_amount_yoy_pct_not_recognized_revenue": round(
            float((b / a - 1) * 100), 2),
        "s2_line_count_delta": later["s2_lines"] - earlier["s2_lines"],
        "monthly_invoice_id_sum_delta_not_unique_orders":
            later["sum_monthly_distinct_s2_invoice_ids_not_distinct_orders_across_period"]
            - earlier["sum_monthly_distinct_s2_invoice_ids_not_distinct_orders_across_period"],
        "known_customer_id_line_share_change_percentage_points": round(
            100 * (later["s2_known_customer_id_line_share"]
                   - earlier["s2_known_customer_id_line_share"]), 2
        ),
        "monthly_yoy": yoy,
        "positive_months_of_matched_calendar_months": sum(
            1 for d in yoy if d["change_pct_not_demand_growth"] is not None
            and d["change_pct_not_demand_growth"] > 0
        ),
        "all_25_months_reconcile_to_case_018_s2_amount_within_5p": True,
        "guardrails": [
            "Compared like calendar months only; 2011-12 is not assumed to be a full month.",
            "Source has invoice lines, not verified orders, payments, fulfilment or recognized revenue.",
            "Invoice-ID counts are summed across months and may count an ID once per month; not a period-distinct customer/order measure.",
            "Gross positive line amounts do not subtract cancellation-coded entries as refunds.",
            "Changes in product mix, wholesale-like quantities, price and atypical invoices can affect apparent activity.",
            "Known customer-ID line share is coverage, not customer retention or conversion.",
            "Exploratory S2 exclusion choices are not accounting-approved and may omit legitimate transactions.",
            "No statistical causality or business intent is inferred from observational changes.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sql-summary", type=Path, default=Path("outputs/sql_kpi_workbench.json"))
    p.add_argument("--output", type=Path, default=Path("outputs/monthly_business_activity.json"))
    args = p.parse_args()
    if not args.sql_summary.is_file():
        raise FileNotFoundError("Case 018 SQL-verified monthly aggregates required")
    source = json.loads(args.sql_summary.read_text(encoding="utf-8"))
    report = summarize_comparable_months(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

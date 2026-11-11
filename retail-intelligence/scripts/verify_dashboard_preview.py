"""Validate versioned dashboard preview against verified aggregate-only evidence.

Static portfolio HTML, not Power BI .pbix. Never loads the raw workbook,
source-line CSV or invoice/customer identifiers. Refuse stale KPI claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _rounded_money(value: float, *, decimals: int = 0) -> str:
    return "£" + f"{abs(value):,.{decimals}f}"


def verify_dashboard_content(html: str, monthly: dict, concentration: dict, sku: dict) -> dict:
    if not monthly.get("all_25_months_reconcile_to_case_018_s2_amount_within_5p"):
        raise ValueError("Case 019 source reconciliation is missing")
    if sku.get("status") != "sku_quantity_and_effective_value_decomposition_not_causal_pricing":
        raise ValueError("Case 021 source-verified SKU decomposition required")
    if sku.get("years") != [2010, 2011] or sku.get("calendar_months_compared") != list(range(1, 12)):
        raise ValueError("Dashboard uses an invalid comparison period")

    components = sku["identity_components_gbp"]
    if abs(sum(components.values()) - sku["decomposition_gross_change_gbp"]) > .02:
        raise AssertionError("Case 021 SKU decomposition does not balance")
    if abs(float(monthly["s2_gross_positive_line_amount_change_gbp"]) - sku["decomposition_gross_change_gbp"]) > .02:
        raise AssertionError("Case 019 matched-month change differs from Case 021")
    for year, period in zip((2010, 2011), sku["periods_reconciled_independently_to_case_018_sql"]):
        m = monthly["earlier" if year == 2010 else "later"]
        if int(period["year"]) != year:
            raise AssertionError("Wrong SKU comparison year")
        if abs(float(period["gross_positive_line_amount_gbp_not_revenue"]) - float(m["s2_gross_positive_line_amount_gbp_not_revenue"])) > .02:
            raise AssertionError("SKU year gross sum differs from independently verified SQL monthly amount")
        if int(period["s2_source_lines"]) != int(m["s2_lines"]):
            raise AssertionError("SKU source line count differs from Case 019")

    values = [
        f"{monthly['s2_gross_positive_line_amount_yoy_pct_not_recognized_revenue']:+.2f}%",
        f"{concentration['yoy_change_after_omitting_each_period_upper_one_percent_id_month_groups_pct_sensitivity']:+.2f}%",
        "+" + _rounded_money(sku["decomposition_gross_change_gbp"], decimals=2),
    ]
    for signed in components.values():
        values.append(("+" if signed > 0 else "−") + _rounded_money(signed))
    for required in values + [
        "SKU composition explains the arithmetic change",
        "Case 021",
        "115 tests",
        "not a price-inflation",
        "not a verified launch",
        "not recognized revenue",
        "Not a Power BI .pbix",
    ]:
        if required.lower() not in html.lower():
            raise AssertionError(f"Dashboard missing verified data/caveat: {required}")

    return {
        "verified": True,
        "comparison": "matched Jan–Nov 2010 vs Jan–Nov 2011",
        "gross_line_amount_change_gbp": round(float(sku["decomposition_gross_change_gbp"]), 2),
        "component_count": len(components),
        "source_is_only_aggregate_outputs": True,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dashboard", type=Path, default=Path("dashboard/index.html"))
    p.add_argument("--monthly", type=Path, default=Path("outputs/monthly_business_activity.json"))
    p.add_argument("--concentration", type=Path, default=Path("outputs/invoice_concentration.json"))
    p.add_argument("--sku", type=Path, default=Path("outputs/sku_composition.json"))
    args = p.parse_args()
    out = verify_dashboard_content(
        args.dashboard.read_text(encoding="utf-8"),
        json.loads(args.monthly.read_text(encoding="utf-8")),
        json.loads(args.concentration.read_text(encoding="utf-8")),
        json.loads(args.sku.read_text(encoding="utf-8")),
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

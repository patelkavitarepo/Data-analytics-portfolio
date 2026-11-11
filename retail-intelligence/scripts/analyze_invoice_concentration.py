"""Case 020: concentration of provisional S2 gross line amount by invoice ID.

The original workbook is never loaded or modified. The Case 008 local,
reversible candidate CSV.gz is used only in-memory; aggregate JSON includes
no raw rows, invoice IDs or customer IDs. Uses Case 018 SQL monthly summary
as an independent source-wide monetary/count reconciliation gate.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


NARROW_CODES = frozenset({"POST", "DOT", "C2", "BANK CHARGES", "AMAZONFEE"})
AMBIGUOUS_CODES = frozenset({"M", "D"})
GROSS_FIELD = "s2_gross_positive_line_amount_gbp_not_accounting_revenue"


def _part(values: pd.DataFrame) -> dict:
    """Report upper-tail invoice-ID-month concentration within selected groups."""
    num = int(len(values))
    if not num:
        raise ValueError("Cannot summarize an empty invoice-ID-month cohort")
    gross = values["s2_line_amount"].astype("float64").sort_values(ascending=False)
    top_count = max(1, math.ceil(num * .01))
    total = float(gross.sum())
    if total <= 0:
        raise ValueError("Positive-priced S2 source should have positive gross amount")
    top_sum = float(gross.iloc[:top_count].sum())
    return {
        "invoice_id_month_groups_not_confirmed_orders": num,
        "s2_gross_line_amount_gbp_not_revenue": round(total, 2),
        "upper_one_percent_id_month_groups_count": top_count,
        "upper_one_percent_gross_line_amount_gbp_not_revenue": round(top_sum, 2),
        "upper_one_percent_share_of_gross_line_amount_not_verified_market_share": round(top_sum / total, 6),
        "gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only": round(total - top_sum, 2),
        "median_id_month_gross_line_amount_gbp": round(float(gross.median()), 2),
        "ninety_fifth_percentile_id_month_gross_line_amount_gbp": round(float(gross.quantile(.95)), 2),
        "maximum_single_id_month_gross_line_amount_gbp": round(float(gross.iloc[0]), 2),
        "maximum_single_id_month_share_of_total": round(float(gross.iloc[0]) / total, 6),
    }


def inspect_invoice_concentration(
    candidate: pd.DataFrame, sql_summary: dict,
    period_month_numbers: tuple[int, ...] = tuple(range(1, 12)),
) -> dict:
    expected = {"invoice_no", "stock_code", "quantity", "unit_price", "invoice_date"}
    if missing := sorted(expected.difference(candidate.columns)):
        raise ValueError("Missing source fields: " + repr(missing))
    if not sql_summary.get("agrees_with_case_009_counts_invoice_ids_and_amounts"):
        raise ValueError("Independently source-reconciled SQL results are required")
    df = candidate[list(expected)].copy()
    df["invoice_no"] = df["invoice_no"].astype("string").str.strip()
    if df["invoice_no"].isna().any() or df["invoice_no"].eq("").any():
        raise ValueError("Missing invoice IDs")
    df["stock_code"] = df["stock_code"].astype("string").str.strip().str.upper()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    if df["invoice_date"].isna().any():
        raise ValueError("Date coverage incomplete: missing or invalid invoice date")
    code = df["stock_code"]
    s2 = df.loc[
        ~df["invoice_no"].str.upper().str.startswith("C").fillna(False)
        & df["quantity"].gt(0).fillna(False)
        & df["unit_price"].gt(0).fillna(False)
        & ~code.isin(NARROW_CODES | AMBIGUOUS_CODES)
    ].copy()
    s2["month"] = s2["invoice_date"].dt.strftime("%Y-%m")
    s2["s2_line_amount"] = s2["quantity"] * s2["unit_price"]
    invoice_month = s2.groupby(
        ["month", "invoice_no"], sort=False, dropna=False
    )["s2_line_amount"].sum().reset_index()

    monthly = []
    expected_months = {
        str(r["recorded_month"]): r for r in sql_summary["monthly_s2_recorded_activity"]
    }
    if len(expected_months) != len(sql_summary["monthly_s2_recorded_activity"]):
        raise ValueError("Repeated recorded month in reference")
    actual_months = set(invoice_month["month"])
    reference_months = {
        k for k, row in expected_months.items() if int(row["s2_positive_priced_lines"]) > 0
    }
    if actual_months != reference_months:
        raise AssertionError("Date/month coverage differs from Case 018 SQL results")
    for mon, group in invoice_month.groupby("month", sort=True):
        part = _part(group)
        base = expected_months[mon]
        if part["invoice_id_month_groups_not_confirmed_orders"] != int(
            base["s2_distinct_qualifying_invoice_ids_not_orders"]
        ):
            raise AssertionError("Invoice counts mismatch for " + mon)
        if abs(part["s2_gross_line_amount_gbp_not_revenue"] - float(base[GROSS_FIELD])) > 0.05:
            raise AssertionError("Gross S2 amount mismatch for " + mon)
        monthly.append({"recorded_month": mon, **part})
    if sum(int(r["s2_positive_priced_lines"]) for r in expected_months.values()) != len(s2):
        raise AssertionError("Full source S2 line count differs from independent SQL")
    total = float(s2["s2_line_amount"].sum())
    scenario = sql_summary["scenario_reconciliation"]["S2_also_exclude_manual_and_discount_code_candidates"]
    if abs(total - float(scenario["hypothetical_gross_line_amount_gbp"])) > 0.05:
        raise AssertionError("Full source S2 amount differs from independent SQL")

    years = (2010, 2011)
    periods = []
    for year in years:
        selected = invoice_month.loc[
            (invoice_month["month"].str[:4] == str(year))
            & invoice_month["month"].str[-2:].astype("int64").isin(period_month_numbers)
        ]
        if not selected["month"].nunique() == len(period_month_numbers):
            raise ValueError("A requested comparable period is missing source months")
        periods.append({"year": year, "included_months": list(period_month_numbers), **_part(selected)})
    earlier, later = periods
    first = earlier["gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only"]
    second = later["gross_without_upper_one_percent_id_month_groups_gbp_sensitivity_only"]
    if first <= 0:
        raise ValueError("Trimmed baseline is zero; no percentage comparison is valid")
    trimmed_change = round((second / first - 1) * 100, 2)
    return {
        "status": "exploratory_invoice_id_month_concentration_not_causal_sales_growth",
        "reconciled_s2_lines": int(len(s2)),
        "source_candidate_view_rows": int(len(df)),
        "monthly_id_concentration": monthly,
        "comparable_jan_nov_period_concentration": periods,
        "yoy_change_after_omitting_each_period_upper_one_percent_id_month_groups_pct_sensitivity": trimmed_change,
        "guardrails": [
            "Invoice ID-month is not necessarily one completed order, unique customer, shipment or paid sale.",
            "Upper 1% includes ceiling(1% of monthly or period invoice-ID-month groups), at least one group.",
            "Omitting the largest IDs is a sensitivity analysis, not a source-cleaning or approved financial exclusion.",
            "Trimming periods independently changes the constituent invoices; trimmed year-over-year change is not evidence of organic growth.",
            "No real customer IDs, invoice identifiers, personal data, source-line records or item-level tables are exported.",
            "The S2 merchandise-like code filter excludes ambiguous source entries; accounting status remains unapproved.",
            "C-prefixed cancellation values are not verified refunds and remain outside these gross-positive sums.",
            "Extreme invoices, changes in unit prices, wholesale order mix and date coverage can materially affect results.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, default=Path("data/derived/candidate_analysis_lines.csv.gz"))
    p.add_argument("--sql-summary", type=Path, default=Path("outputs/sql_kpi_workbench.json"))
    p.add_argument("--output", type=Path, default=Path("outputs/invoice_concentration.json"))
    a = p.parse_args()
    if not a.candidate.is_file() or not a.sql_summary.is_file():
        raise FileNotFoundError("Case 008 locally derived candidate data and verified Case 018 SQL summary are required")
    candidate = pd.read_csv(
        a.candidate, compression="gzip", low_memory=False,
        usecols=["invoice_no", "stock_code", "quantity", "unit_price", "invoice_date"],
        dtype={"invoice_no": "string", "stock_code": "string"},
    )
    sql = json.loads(a.sql_summary.read_text(encoding="utf-8"))
    out = inspect_invoice_concentration(candidate, sql)
    out["source_workbook_sha256_from_case_018"] = sql["source_workbook_sha256_from_case_009"]
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": out["status"],
        "candidate_rows": out["source_candidate_view_rows"],
        "reconciled_s2_lines": out["reconciled_s2_lines"],
        "period_summary": out["comparable_jan_nov_period_concentration"],
        "sensitivity_yoy_pct": out["yoy_change_after_omitting_each_period_upper_one_percent_id_month_groups_pct_sensitivity"],
    }, indent=2))


if __name__ == "__main__":
    main()

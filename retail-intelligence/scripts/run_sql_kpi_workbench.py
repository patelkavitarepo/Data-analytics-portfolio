"""Case 018: SQL workbench cross-checks exploratory retail semantics.

Reads the locally derived Case 008 reversible candidate CSV.gz; the
source workbook, derived row-level files and customer IDs are NOT published.
SQLite comes from the Python standard library. Outputs aggregates only.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sqlite3
from pathlib import Path


LABELS = (
    "cancellation_coded",
    "negative_quantity_zero_price_unknown_customer",
    "non_c_negative_quantity_other",
    "positive_quantity_negative_price",
    "positive_quantity_zero_price",
    "named_shipping_billing_code_candidate",
    "manual_discount_code_candidate",
    "other_positive_priced",
    "unresolved_other",
)
SOURCE_COHORT_MAP = {
    "cancellation_coded": "c_prefixed_any_quantity",
    "negative_quantity_zero_price_unknown_customer": "negative_non_c_zero_price_missing_customer",
    "non_c_negative_quantity_other": "other_negative_non_c",
    "positive_quantity_negative_price": "positive_non_c_negative_price",
    "positive_quantity_zero_price": "positive_non_c_zero_price",
    "other_positive_priced": "positive_non_c_positive_price",
}


def _none(value: str | None) -> str | None:
    if value is None or value.strip() == "" or value.strip().lower() in {"nan", "none", "null"}:
        return None
    return value.strip()


def create_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute("""CREATE TABLE candidate_lines (
        invoice_no TEXT, stock_code TEXT, quantity REAL, unit_price REAL,
        invoice_date TEXT, customer_id TEXT, country TEXT
    )""")
    return con


def add_frame_rows(con: sqlite3.Connection, rows: list[dict]) -> None:
    """For synthetic tests only; source loading uses streaming CSV.gz."""
    con.executemany(
        "INSERT INTO candidate_lines VALUES (?,?,?,?,?,?,?)",
        [
            (r.get("invoice_no"), r.get("stock_code"), r.get("quantity"),
             r.get("unit_price"), r.get("invoice_date"), r.get("customer_id"),
             r.get("country"))
            for r in rows
        ],
    )


def load_candidate_csv(con: sqlite3.Connection, path: Path, batch_size: int = 20000) -> int:
    if not path.is_file():
        raise FileNotFoundError(f"Case 008 derived candidate view missing: {path}")
    total = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        expected = {"invoice_no", "stock_code", "quantity", "unit_price",
                    "invoice_date", "customer_id", "country"}
        if not expected.issubset(set(reader.fieldnames or [])):
            raise ValueError("Candidate CSV is missing required columns")
        batch = []
        for row in reader:
            invoice = _none(row["invoice_no"])
            if not invoice:
                raise ValueError("Missing invoice IDs require explicit policy")
            quantity = _none(row["quantity"])
            unit_price = _none(row["unit_price"])
            batch.append((
                invoice,
                _none(row["stock_code"]),
                float(quantity) if quantity is not None else None,
                float(unit_price) if unit_price is not None else None,
                _none(row["invoice_date"]),
                _none(row["customer_id"]),
                _none(row["country"]),
            ))
            if len(batch) >= batch_size:
                con.executemany("INSERT INTO candidate_lines VALUES (?,?,?,?,?,?,?)", batch)
                total += len(batch)
                batch.clear()
        if batch:
            con.executemany("INSERT INTO candidate_lines VALUES (?,?,?,?,?,?,?)", batch)
            total += len(batch)
    con.commit()
    return total


def analyze_sql(con: sqlite3.Connection, view_sql: str) -> dict:
    con.executescript(view_sql)
    cohort_rows = con.execute(
        "SELECT provisional_line_cohort, COUNT(*) FROM retail_classified "
        "GROUP BY provisional_line_cohort"
    ).fetchall()
    cohort = {label: 0 for label in LABELS}
    for name, count in cohort_rows:
        if name not in cohort:
            raise AssertionError(f"Unexpected SQL cohort {name}")
        cohort[name] = int(count)

    # Distinct invoice IDs are source *identifiers*, NOT verified orders.
    scenario_query = """
      SELECT
        COUNT(*) AS qualifying_lines,
        COUNT(DISTINCT invoice_no) AS qualifying_invoice_ids,
        ROUND(COALESCE(SUM(quantity * unit_price),0),2) AS gross_line_amount_gbp
      FROM retail_classified
      WHERE provisional_line_cohort IN ({})
    """
    scenarios = {}
    filters = {
        "S0_all_positive_priced_non_C": (
            "other_positive_priced", "manual_discount_code_candidate",
            "named_shipping_billing_code_candidate"),
        "S1_exclude_named_shipping_and_billing_code_candidates": (
            "other_positive_priced", "manual_discount_code_candidate"),
        "S2_also_exclude_manual_and_discount_code_candidates": (
            "other_positive_priced",),
    }
    for name, labels in filters.items():
        placeholders = ",".join("?" for _ in labels)
        row = con.execute(scenario_query.format(placeholders), labels).fetchone()
        scenarios[name] = {
            "lines": int(row[0]), "invoice_ids": int(row[1]),
            "hypothetical_gross_line_amount_gbp": float(row[2]),
        }

    # Monthly S2 is explicitly gross-positive line activity, not net sales.
    monthly = con.execute("""
      SELECT COALESCE(NULLIF(SUBSTR(invoice_date,1,7),''),'<unknown>') AS month,
             COUNT(*) AS source_lines,
             SUM(CASE WHEN provisional_line_cohort='other_positive_priced'
                       THEN 1 ELSE 0 END) AS s2_lines,
             ROUND(SUM(CASE WHEN provisional_line_cohort='other_positive_priced'
                            THEN quantity*unit_price ELSE 0 END),2) AS s2_gross_gbp,
             COUNT(DISTINCT CASE WHEN provisional_line_cohort='other_positive_priced'
                                 THEN invoice_no ELSE NULL END) AS s2_invoice_ids,
             SUM(CASE WHEN provisional_line_cohort='other_positive_priced'
                       THEN quantity ELSE 0 END) AS s2_recorded_positive_units,
             SUM(CASE WHEN provisional_line_cohort='other_positive_priced'
                            AND customer_id IS NOT NULL
                       THEN 1 ELSE 0 END) AS s2_known_customer_id_lines,
             SUM(CASE WHEN provisional_line_cohort='cancellation_coded'
                       THEN 1 ELSE 0 END) AS cancellation_coded_lines,
             SUM(CASE WHEN provisional_line_cohort='positive_quantity_zero_price'
                       THEN 1 ELSE 0 END) AS zero_price_positive_lines
      FROM retail_classified
      GROUP BY month ORDER BY month
    """).fetchall()
    months = [{
        "recorded_month": str(t[0]), "candidate_source_lines": int(t[1]),
        "s2_positive_priced_lines": int(t[2]),
        "s2_gross_positive_line_amount_gbp_not_accounting_revenue": float(t[3]),
        "s2_distinct_qualifying_invoice_ids_not_orders": int(t[4]),
        "s2_recorded_positive_units_not_verified_shipments": float(t[5]),
        "s2_known_customer_id_lines": int(t[6]),
        "source_cancellation_coded_lines_not_refunds": int(t[7]),
        "source_zero_price_positive_lines_not_gifts": int(t[8]),
    } for t in monthly]
    assert sum(t["candidate_source_lines"] for t in months) == sum(cohort.values())
    assert sum(t["s2_positive_priced_lines"] for t in months) == scenarios[
        "S2_also_exclude_manual_and_discount_code_candidates"
    ]["lines"]
    return {
        "status": "sql_kpi_workbench_not_accounting_revenue",
        "candidate_view_lines": sum(cohort.values()),
        "mutually_exclusive_provisional_line_cohorts": cohort,
        "scenario_reconciliation": scenarios,
        "monthly_s2_recorded_activity": months,
        "guardrails": [
            "No source or candidate data were modified; only aggregate JSON exported.",
            "Invoice IDs are not verified completed orders and missing customers remain unknown.",
            "Monetary sums are exploratory gross positive line amounts, not recognized, net or cash sales.",
            "C-prefixed cancellations are not verified refunds and are never netted mechanically.",
            "Zero-price lines are not automatically gifts, discounts or inventory corrections.",
            "S2 scenario exclusions are hypotheses, not validated product classifications.",
            "Month and country comparisons must account for temporal coverage and wholesale outliers.",
        ],
    }


def check_against_case_009(result: dict, baseline: dict, money_tolerance: float = 0.02) -> None:
    source = baseline["cross_sheet_reconciled_candidate"]
    expected = source["mutually_exclusive_line_cohorts"]
    actual = result["mutually_exclusive_provisional_line_cohorts"]
    assert result["candidate_view_lines"] == int(source["source_lines"])
    for name, src_label in SOURCE_COHORT_MAP.items():
        if name == "other_positive_priced":
            # Split this exact Case 009 cohort into S2 + fee + manual.
            assert (
                actual["other_positive_priced"]
                + actual["manual_discount_code_candidate"]
                + actual["named_shipping_billing_code_candidate"]
                == int(expected[src_label])
            )
        else:
            assert actual[name] == int(expected[src_label]), (name, actual[name], expected[src_label])
    assert actual["unresolved_other"] == int(expected["unresolved_non_c_other"]) + int(expected["zero_quantity_non_c"])
    expected_scenarios = source["scenarios_experimental_not_accounting_revenue"]
    for name, measured in result["scenario_reconciliation"].items():
        prior = expected_scenarios[name]
        assert measured["lines"] == int(prior["lines"]), name
        assert measured["invoice_ids"] == int(prior["invoice_ids"]), name
        assert abs(
            measured["hypothetical_gross_line_amount_gbp"]
            - float(prior["hypothetical_gross_line_amount_gbp"])
        ) <= money_tolerance, name
    result["agrees_with_case_009_counts_invoice_ids_and_amounts"] = True


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-csv", type=Path,
                   default=Path("data/derived/candidate_analysis_lines.csv.gz"))
    p.add_argument("--sql", type=Path, default=Path("sql/001_provisional_retail_kpis.sql"))
    p.add_argument("--prior-scenarios", type=Path, default=Path("outputs/revenue_sensitivity.json"))
    p.add_argument("--output", type=Path, default=Path("outputs/sql_kpi_workbench.json"))
    args = p.parse_args()
    if not args.prior_scenarios.is_file():
        raise FileNotFoundError("Source-verified Case 009 scenarios required for SQL reconciliation")
    with create_db() as con:
        loaded = load_candidate_csv(con, args.candidate_csv)
        result = analyze_sql(con, args.sql.read_text(encoding="utf-8"))
        assert loaded == result["candidate_view_lines"]
        baseline = json.loads(args.prior_scenarios.read_text(encoding="utf-8"))
        check_against_case_009(result, baseline)
    result["source_workbook_sha256_from_case_009"] = baseline["source_workbook_sha256"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_view_lines": result["candidate_view_lines"],
        "cohorts": result["mutually_exclusive_provisional_line_cohorts"],
        "scenario_reconciliation": result["scenario_reconciliation"],
        "months_reported": len(result["monthly_s2_recorded_activity"]),
        "agrees_with_case_009_counts_invoice_ids_and_amounts": True,
    }, indent=2))


if __name__ == "__main__":
    main()

"""Case 019: comparable month selection, provenance/reconciliation guardrails."""
from copy import deepcopy

import pytest

from scripts.analyze_monthly_business_activity import summarize_comparable_months


def month(label, gross, lines, invoices, units, known):
    return {
        "recorded_month": label,
        "candidate_source_lines": lines + 2,
        "s2_positive_priced_lines": lines,
        "s2_gross_positive_line_amount_gbp_not_accounting_revenue": gross,
        "s2_distinct_qualifying_invoice_ids_not_orders": invoices,
        "s2_recorded_positive_units_not_verified_shipments": units,
        "s2_known_customer_id_lines": known,
        "source_cancellation_coded_lines_not_refunds": 1,
        "source_zero_price_positive_lines_not_gifts": 1,
    }


def source():
    return {
        "agrees_with_case_009_counts_invoice_ids_and_amounts": True,
        "monthly_s2_recorded_activity": [
            month("2010-01", 100, 3, 2, 6, 2),
            month("2010-02", 200, 4, 2, 8, 3),
            month("2011-01", 110, 4, 2, 7, 3),
            month("2011-02", 250, 5, 3, 10, 4),
        ],
        "scenario_reconciliation": {
            "S2_also_exclude_manual_and_discount_code_candidates": {
                "hypothetical_gross_line_amount_gbp": 660.0,
                "lines": 16,
            }
        }
    }


def test_like_for_like_month_comparison_without_accounting_claims():
    result = summarize_comparable_months(source(), months=(1, 2))
    assert result["earlier"]["s2_gross_positive_line_amount_gbp_not_revenue"] == 300
    assert result["later"]["s2_gross_positive_line_amount_gbp_not_revenue"] == 360
    assert result["s2_gross_positive_line_amount_change_gbp"] == 60
    assert result["s2_gross_positive_line_amount_yoy_pct_not_recognized_revenue"] == 20.0
    assert result["s2_line_count_delta"] == 2
    assert result["monthly_invoice_id_sum_delta_not_unique_orders"] == 1
    assert result["positive_months_of_matched_calendar_months"] == 2
    assert result["earlier"]["s2_known_customer_id_line_share"] == 0.714286
    assert result["later"]["s2_known_customer_id_line_share"] == 0.777778
    assert result["known_customer_id_line_share_change_percentage_points"] == 6.35
    assert result["all_25_months_reconcile_to_case_018_s2_amount_within_5p"] is True


def test_no_duplicate_missing_invalid_months():
    d = source()
    d["monthly_s2_recorded_activity"].append(
        month("2011-02", 1, 1, 1, 1, 1)
    )
    with pytest.raises(ValueError, match="Duplicate"):
        summarize_comparable_months(d, months=(1, 2))
    d = source()
    d["monthly_s2_recorded_activity"][0]["recorded_month"] = "2010-99"
    with pytest.raises(ValueError, match="Missing requested"):
        summarize_comparable_months(d, months=(1, 2))
    with pytest.raises(ValueError, match="Missing requested"):
        summarize_comparable_months(source(), months=(1, 2, 3))


def test_unverified_or_reversed_sql_aggregate_cannot_drive_story():
    d = source()
    d["agrees_with_case_009_counts_invoice_ids_and_amounts"] = False
    with pytest.raises(ValueError, match="Unverified"):
        summarize_comparable_months(d, months=(1, 2))
    d = source()
    d["scenario_reconciliation"][
        "S2_also_exclude_manual_and_discount_code_candidates"
    ]["hypothetical_gross_line_amount_gbp"] = 600
    with pytest.raises(AssertionError, match="does not match"):
        summarize_comparable_months(d, months=(1, 2))


def test_monthly_line_count_and_customer_share_consistency():
    d = source()
    d["scenario_reconciliation"][
        "S2_also_exclude_manual_and_discount_code_candidates"
    ]["lines"] = 20
    with pytest.raises(AssertionError, match="line counts"):
        summarize_comparable_months(d, months=(1, 2))
    d = source()
    d["monthly_s2_recorded_activity"][1]["s2_known_customer_id_lines"] = 999
    with pytest.raises(ValueError, match="Impossible"):
        summarize_comparable_months(d, months=(1, 2))


def test_zero_denom_invalid_selections_and_no_false_unique_invoice_claim():
    d = source()
    for record in d["monthly_s2_recorded_activity"]:
        if record["recorded_month"].startswith("2010"):
            record["s2_gross_positive_line_amount_gbp_not_accounting_revenue"] = 0
    d["scenario_reconciliation"][
        "S2_also_exclude_manual_and_discount_code_candidates"
    ]["hypothetical_gross_line_amount_gbp"] = 360
    with pytest.raises(ValueError, match="Earlier gross"):
        summarize_comparable_months(d, months=(1, 2))
    with pytest.raises(ValueError, match="comparable-month"):
        summarize_comparable_months(source(), months=(1, 1))
    out = summarize_comparable_months(source(), months=(1, 2))
    assert "not_distinct_orders" in str(out["earlier"].keys())
    assert out["comparison"].startswith("2010 vs 2011")

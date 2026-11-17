"""Case 022 publication gate: no stale dashboard values or misleading labels."""
from pathlib import Path
import pytest

from scripts.verify_dashboard_preview import verify_dashboard_content


def example():
    monthly = {
        "all_25_months_reconcile_to_case_018_s2_amount_within_5p": True,
        "s2_gross_positive_line_amount_change_gbp": 50.0,
        "s2_gross_positive_line_amount_yoy_pct_not_recognized_revenue": 5.0,
        "earlier": {"s2_gross_positive_line_amount_gbp_not_revenue": 1000.0, "s2_lines": 10},
        "later": {"s2_gross_positive_line_amount_gbp_not_revenue": 1050.0, "s2_lines": 12},
    }
    conc = {
        "yoy_change_after_omitting_each_period_upper_one_percent_id_month_groups_pct_sensitivity": 1.5
    }
    sku = {
        "status": "sku_quantity_and_effective_value_decomposition_not_causal_pricing",
        "years": [2010, 2011],
        "calendar_months_compared": list(range(1, 12)),
        "identity_components_gbp": {
            "common_skus_recorded_quantity_component": -10.0,
            "common_skus_effective_gross_per_unit_component": -5.0,
            "new_only_later_year_sku_gross_contribution": 100.0,
            "disappeared_only_earlier_year_sku_gross_contribution": -35.0,
        },
        "decomposition_gross_change_gbp": 50.0,
        "periods_reconciled_independently_to_case_018_sql": [
            {"year": 2010, "gross_positive_line_amount_gbp_not_revenue": 1000, "s2_source_lines": 10},
            {"year": 2011, "gross_positive_line_amount_gbp_not_revenue": 1050, "s2_source_lines": 12},
        ],
    }
    html = """
    SKU composition explains the arithmetic change Case 021 115 tests
    +5.00% +1.50% +£50.00 −£10 −£5 +£100 −£35
    not a price-inflation index; not a verified launch
    not recognized revenue. Not a Power BI .pbix
    """
    return html, monthly, conc, sku


def test_source_reconciled_dashboard_passes_without_row_data():
    result = verify_dashboard_content(*example())
    assert result["verified"] is True
    assert result["gross_line_amount_change_gbp"] == 50.0
    assert result["component_count"] == 4


def test_mismatched_source_decomposition_rejected():
    html, monthly, conc, sku = example()
    sku["identity_components_gbp"]["new_only_later_year_sku_gross_contribution"] = 150
    with pytest.raises(AssertionError, match="does not balance"):
        verify_dashboard_content(html, monthly, conc, sku)


def test_mismatched_monthly_aggregate_and_unverified_source_rejected():
    html, monthly, conc, sku = example()
    monthly["s2_gross_positive_line_amount_change_gbp"] = 40
    with pytest.raises(AssertionError, match="differs"):
        verify_dashboard_content(html, monthly, conc, sku)
    html, monthly, conc, sku = example()
    monthly["all_25_months_reconcile_to_case_018_s2_amount_within_5p"] = False
    with pytest.raises(ValueError, match="source reconciliation"):
        verify_dashboard_content(html, monthly, conc, sku)


def test_missing_caveat_and_kpi_data_rejected():
    html, monthly, conc, sku = example()
    with pytest.raises(AssertionError, match="Dashboard missing"):
        verify_dashboard_content(html.replace("not recognized revenue", ""), monthly, conc, sku)
    with pytest.raises(AssertionError, match="Dashboard missing"):
        verify_dashboard_content(html.replace("+1.50%", ""), monthly, conc, sku)


def test_versioned_real_dashboard_has_source_provenance_and_prominent_uncertainty():
    html = (Path(__file__).resolve().parents[1] / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert "SKU composition explains the arithmetic change" in html
    assert "Case 021" in html
    assert "115 tests" in html
    assert "not recognized revenue" in html.lower()
    assert "Not a Power BI .pbix" in html

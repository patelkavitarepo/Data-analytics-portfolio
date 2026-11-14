"""Case 009 — transparent *scenario* definitions for retail gross line amounts.

The unit is source invoice LINE, not certified sale or customer. Compares raw
worksheets and the reversible Case 008 candidate view. Code-based exclusions
are deliberately narrow and *illustrative*, never an approved revenue policy.
No source row is dropped; only aggregate JSON is uploaded by GitHub Actions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import sha256_file
    from scripts.investigate_sheet_overlap import _prepare
    from scripts.build_reversible_layer import build_candidate_layer
except ModuleNotFoundError:
    from audit import sha256_file
    from investigate_sheet_overlap import _prepare
    from build_reversible_layer import build_candidate_layer


# Exact stock codes; these are candidate names for sensitivity checks,
# NOT proof of what the retailer recognizes as merchandise or services.
NARROW_NONMERCH_CODES = frozenset({
    "POST", "DOT", "C2", "BANK CHARGES", "AMAZONFEE",
})
EXTENDED_AMBIGUOUS_CODES = frozenset({"M", "D"})


def analyze_lines(frame: pd.DataFrame) -> dict:
    """Mutually exclusive source-pattern cohorts and hypothetical scenarios."""
    quantity = pd.to_numeric(frame["quantity"], errors="coerce")
    price = pd.to_numeric(frame["unit_price"], errors="coerce")
    invoice = frame["invoice_no"].astype("string").str.strip()
    stock = frame["stock_code"].astype("string").str.strip().str.upper()
    c = invoice.str.upper().str.startswith("C", na=False).fillna(False)
    pos = quantity.gt(0).fillna(False)
    neg = quantity.lt(0).fillna(False)
    zero_qty = quantity.eq(0).fillna(False)
    pos_price = price.gt(0).fillna(False)
    zero_price = price.eq(0).fillna(False)
    negative_price = price.lt(0).fillna(False)
    operational_shape = neg & zero_price & frame["customer_id"].isna() & ~c
    positive_priced = pos & pos_price & ~c
    fields = {
        "c_prefixed_any_quantity": c,
        "negative_non_c_zero_price_missing_customer": operational_shape,
        "other_negative_non_c": neg & ~c & ~operational_shape,
        "positive_non_c_positive_price": positive_priced,
        "positive_non_c_zero_price": pos & zero_price & ~c,
        "positive_non_c_negative_price": pos & negative_price & ~c,
        "zero_quantity_non_c": zero_qty & ~c,
    }
    accounted = pd.Series(False, index=frame.index)
    for label, mask in fields.items():
        assert not bool((accounted & mask).any()), f"Overlapping cohort: {label}"
        accounted = accounted | mask
    fields["unresolved_non_c_other"] = ~accounted
    cohorts = {name: int(mask.sum()) for name, mask in fields.items()}
    assert sum(cohorts.values()) == len(frame)

    amount = quantity.astype("float64") * price.astype("float64")
    narrow = stock.isin(NARROW_NONMERCH_CODES) & positive_priced
    extended = stock.isin(EXTENDED_AMBIGUOUS_CODES) & positive_priced
    assert not bool((narrow & extended).any())
    defined = [
        (
            "S0_all_positive_priced_non_C",
            positive_priced,
            "All positive-quantity positive-unit-price lines not C-prefixed",
        ),
        (
            "S1_exclude_named_shipping_and_billing_code_candidates",
            positive_priced & ~narrow,
            "S0 excluding exact codes POST, DOT, C2, BANK CHARGES, AMAZONFEE",
        ),
        (
            "S2_also_exclude_manual_and_discount_code_candidates",
            positive_priced & ~narrow & ~extended,
            "S1 additionally excluding exact codes M and D (more speculative)",
        ),
    ]
    scenarios = {}
    for key, mask, definition in defined:
        scenarios[key] = {
            "definition": definition,
            "lines": int(mask.sum()),
            "invoice_ids": int(invoice.loc[mask].nunique()),
            "hypothetical_gross_line_amount_gbp": round(float(amount.loc[mask].sum()), 2),
        }
    exclusions = {}
    for key, mask in [("narrow_named_shipping_billing", narrow), ("additional_manual_discount", extended)]:
        exclusions[key] = {
            "lines": int(mask.sum()),
            "invoice_ids": int(invoice.loc[mask].nunique()),
            "hypothetical_positive_line_amount_gbp": round(float(amount.loc[mask].sum()), 2),
        }
    by_code = {}
    for code in sorted(NARROW_NONMERCH_CODES | EXTENDED_AMBIGUOUS_CODES):
        mask = positive_priced & stock.eq(code).fillna(False)
        if not mask.any():
            by_code[code] = {"lines": 0, "amount_gbp": 0.0, "examples": []}
            continue
        examples = (
            frame.loc[mask, "description"].dropna().astype("string")
            .str.strip().loc[lambda x: x.ne("")].drop_duplicates().head(4).tolist()
        )
        by_code[code] = {
            "lines": int(mask.sum()),
            "amount_gbp": round(float(amount.loc[mask].sum()), 2),
            "examples": examples,
        }

    cancelled_negative_priced = c & neg & pos_price
    cancellation_summary = {
        "c_prefixed_lines_all": int(c.sum()),
        "c_prefixed_negative_quantity_positive_price_lines": int(cancelled_negative_priced.sum()),
        "absolute_signed_amount_for_those_lines_gbp": round(
            float((-amount.loc[cancelled_negative_priced]).sum()), 2
        ),
        "warning": "A cancellation-coded line is NOT necessarily a cash refund; this amount is NOT subtracted from any sales scenario.",
    }

    # Exact arithmetic relationships after rounding (one penny tolerance
    # permits differences in summation order at million-row scale).
    assert abs(
        scenarios["S0_all_positive_priced_non_C"]["hypothetical_gross_line_amount_gbp"]
        - scenarios["S1_exclude_named_shipping_and_billing_code_candidates"]["hypothetical_gross_line_amount_gbp"]
        - exclusions["narrow_named_shipping_billing"]["hypothetical_positive_line_amount_gbp"]
    ) <= 0.01
    assert abs(
        scenarios["S1_exclude_named_shipping_and_billing_code_candidates"]["hypothetical_gross_line_amount_gbp"]
        - scenarios["S2_also_exclude_manual_and_discount_code_candidates"]["hypothetical_gross_line_amount_gbp"]
        - exclusions["additional_manual_discount"]["hypothetical_positive_line_amount_gbp"]
    ) <= 0.01
    return {
        "source_lines": int(len(frame)),
        "mutually_exclusive_line_cohorts": cohorts,
        "scenarios_experimental_not_accounting_revenue": scenarios,
        "named_code_exclusion_effects": exclusions,
        "observed_description_examples_by_exact_code": by_code,
        "cancellation_lines_not_assumed_to_be_refunds": cancellation_summary,
    }


def investigate_revenue_scenarios(sheets: dict[str, pd.DataFrame]) -> dict:
    if len(sheets) != 2:
        raise ValueError("Expected exactly two original yearly worksheets")
    # Keep original data and cross-sheet matching behavior fixed. We compare
    # scenario decisions against both raw sheets and the Case 008 candidate.
    candidate, provenance, layer = build_candidate_layer(sheets)
    raw = pd.concat([_prepare(frame) for frame in sheets.values()], ignore_index=True)
    raw_metrics = analyze_lines(raw)
    candidate_metrics = analyze_lines(candidate)
    assert raw_metrics["source_lines"] == layer["raw_source_rows"]
    assert candidate_metrics["source_lines"] == layer["candidate_view_rows"]
    assert len(provenance) == layer["provenance_rows_including_every_original_line"]
    assert candidate_metrics["scenarios_experimental_not_accounting_revenue"][
        "S0_all_positive_priced_non_C"
    ]["hypothetical_gross_line_amount_gbp"] == layer[
        "hypothetical_positive_line_amount_candidate_gbp"
    ]
    assert raw_metrics["scenarios_experimental_not_accounting_revenue"][
        "S0_all_positive_priced_non_C"
    ]["hypothetical_gross_line_amount_gbp"] == layer[
        "hypothetical_positive_line_amount_raw_gbp"
    ]
    raw_s = raw_metrics["scenarios_experimental_not_accounting_revenue"]
    can_s = candidate_metrics["scenarios_experimental_not_accounting_revenue"]
    sensitivity = {
        scenario: {
            "raw_line_count": raw_s[scenario]["lines"],
            "candidate_line_count": can_s[scenario]["lines"],
            "cross_sheet_copies_not_counted_in_candidate": (
                raw_s[scenario]["lines"] - can_s[scenario]["lines"]
            ),
            "raw_gross_line_amount_gbp": raw_s[scenario]["hypothetical_gross_line_amount_gbp"],
            "candidate_gross_line_amount_gbp": can_s[scenario]["hypothetical_gross_line_amount_gbp"],
            "source_overlap_difference_gbp": round(
                raw_s[scenario]["hypothetical_gross_line_amount_gbp"]
                - can_s[scenario]["hypothetical_gross_line_amount_gbp"], 2
            ),
        }
        for scenario in can_s
    }
    return {
        "status": "exploratory_revenue_sensitivity_not_approved_KPI",
        "input_source": "original UCI Online Retail II workbook, with Case 008 reversible candidate view",
        "raw": raw_metrics,
        "cross_sheet_reconciled_candidate": candidate_metrics,
        "sensitivity_by_scenario": sensitivity,
        "reversible_layer_links": layer["canonical_links_for_suppressed_rows"],
        "caveats": [
            "S0, S1, S2 are illustrative gross POSITIVE-priced line amount scenarios, not revenue recognized in financial statements.",
            "Postage, billing and manual/discount code semantics are candidates supported by code labels; not independently certified.",
            "No source rows, original data, or the candidate view are changed by comparing these scenarios.",
            "C-prefixed cancellations are shown separately, NOT mechanically subtracted as refunds.",
            "Missing customer ID does not exclude otherwise qualifying positive-priced lines.",
            "Taxes, settlement, refunds, discounts, stock valuation, and unverified item codes are not resolved.",
            "No row-level datasets or customer IDs are published with this aggregate report.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/revenue_sensitivity.json"))
    parser.add_argument("--prior-candidate-audit", type=Path, default=Path("outputs/reversible_layer_audit.json"))
    args = parser.parse_args()
    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    result = investigate_revenue_scenarios(sheets)
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_candidate_audit.is_file():
        prior = json.loads(args.prior_candidate_audit.read_text(encoding="utf-8"))
        assert result["reversible_layer_links"] == prior["canonical_links_for_suppressed_rows"]
        assert (
            result["cross_sheet_reconciled_candidate"]["source_lines"]
            == prior["candidate_view_rows"]
        )
        result["prior_candidate_layer_agreement"] = True
    else:
        result["prior_candidate_layer_agreement"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

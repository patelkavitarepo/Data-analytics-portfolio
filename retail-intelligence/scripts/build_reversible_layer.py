"""Case 008 — reversible candidate analysis layer for yearly-sheet overlap.

This is a PROPOSAL, not an approved data cleaning or revenue policy.
We retain EVERY row in a source-to-canonical provenance map. The candidate
view keeps all rows from the first worksheet plus only unmatched occurrences
from the second, matching on ALL eight fields with within-sheet occurrence
rank (multiset semantics). No within-sheet duplicates are removed.

Run from retail-intelligence/ after obtaining the official source workbook.
Both CSV.gz files are ignored by Git and NEVER uploaded in GitHub Actions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import FIELDS, sha256_file
    from scripts.investigate_sheet_overlap import _prepare
except ModuleNotFoundError:
    from audit import FIELDS, sha256_file
    from investigate_sheet_overlap import _prepare


PROVENANCE_FIELDS = (
    "source_sheet", "source_excel_row", "included_in_candidate_view",
    "candidate_canonical_sheet", "candidate_canonical_excel_row",
    "overlap_type",
)


def _classify(df: pd.DataFrame) -> dict[str, int]:
    q = pd.to_numeric(df["quantity"], errors="coerce")
    p = pd.to_numeric(df["unit_price"], errors="coerce")
    invoice = df["invoice_no"].astype("string")
    c = invoice.str.upper().str.startswith("C").fillna(False)
    candidate = q.lt(0).fillna(False) & p.eq(0).fillna(False) & df["customer_id"].isna() & ~c
    positive = q.gt(0).fillna(False) & p.gt(0).fillna(False) & ~c
    other = ~(candidate | positive | c)
    return {
        "negative_non_c_zero_price_missing_customer": int(candidate.sum()),
        "c_prefixed_cancellation": int(c.sum()),
        "positive_quantity_positive_price_non_c": int(positive.sum()),
        "other": int(other.sum()),
    }


def _positive_line_amount(df: pd.DataFrame) -> float:
    q = pd.to_numeric(df["quantity"], errors="coerce")
    p = pd.to_numeric(df["unit_price"], errors="coerce")
    c = df["invoice_no"].astype("string").str.upper().str.startswith("C").fillna(False)
    positive = q.gt(0).fillna(False) & p.gt(0).fillna(False) & ~c
    return round(float((q[positive].astype(float) * p[positive].astype(float)).sum()), 2)


def build_candidate_layer(
    sheets: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Produce candidate lines, complete row-level provenance, and checks.

    A/B choice is explicit and deterministic: all sheet A source lines are
    retained. Sheet B source lines are linked to corresponding sheet A lines
    by exact eight-field key plus occurrence number; only matched B copies
    are suppressed in the *candidate view*. Both source observations remain
    in provenance and in the unchanged official workbook.
    """
    if len(sheets) != 2:
        raise ValueError("Expected exactly two original yearly worksheets")
    (name_a, raw_a), (name_b, raw_b) = list(sheets.items())
    if str(name_a) == str(name_b):
        raise ValueError("Worksheet names must differ")

    a, b = _prepare(raw_a).reset_index(drop=True), _prepare(raw_b).reset_index(drop=True)
    keys = list(FIELDS)
    for data in (a, b):
        data["_excel_row"] = data.index.to_numpy() + 2  # Excel header is row 1
        data["_occurrence"] = data.groupby(keys, dropna=False, sort=False).cumcount()

    # Narrow the expensive eight-column merge to invoice IDs shared between
    # the worksheets. Every exact-key cross-sheet match must share invoice ID.
    shared_ids = pd.Index(a["invoice_no"].dropna().unique()).intersection(
        pd.Index(b["invoice_no"].dropna().unique())
    )
    a_candidates = a.loc[a["invoice_no"].isin(shared_ids), keys + ["_occurrence", "_excel_row"]]
    b_candidates = b.loc[b["invoice_no"].isin(shared_ids), keys + ["_occurrence", "_excel_row"]]
    pairs = b_candidates.rename(columns={"_excel_row": "_b_excel_row"}).merge(
        a_candidates.rename(columns={"_excel_row": "_a_excel_row"}),
        on=keys + ["_occurrence"],
        how="inner",
        validate="one_to_one",
    )
    # Original Online Retail II has no missing invoice IDs. Refuse to
    # silently miss possible cross-sheet matches if that ever changes.
    if a["invoice_no"].isna().any() or b["invoice_no"].isna().any():
        raise ValueError("Missing invoice IDs require explicit reconciliation")

    assert pairs["_b_excel_row"].is_unique and pairs["_a_excel_row"].is_unique
    matched_b_rows = pairs["_b_excel_row"].astype("int64")
    b["_keep"] = ~b["_excel_row"].isin(matched_b_rows)
    a["_keep"] = True

    a["source_sheet"] = str(name_a)
    b["source_sheet"] = str(name_b)
    a["source_excel_row"] = a["_excel_row"]
    b["source_excel_row"] = b["_excel_row"]
    a["included_in_candidate_view"] = True
    b["included_in_candidate_view"] = b["_keep"]
    a["candidate_canonical_sheet"] = str(name_a)
    b["candidate_canonical_sheet"] = b["_keep"].map({True: str(name_b), False: str(name_a)})
    a["candidate_canonical_excel_row"] = a["_excel_row"]
    b_lookup = pairs.set_index("_b_excel_row")["_a_excel_row"]
    b["candidate_canonical_excel_row"] = b["_excel_row"].where(
        b["_keep"], b["_excel_row"].map(b_lookup)
    ).astype("int64")
    a["overlap_type"] = "retained_first_sheet"
    b["overlap_type"] = b["_keep"].map({
        True: "retained_second_sheet_unmatched",
        False: "second_sheet_exact_cross_sheet_copy",
    })

    source_provenance = pd.concat(
        [a[list(PROVENANCE_FIELDS)], b[list(PROVENANCE_FIELDS)]],
        ignore_index=True,
    )
    candidate_lines = pd.concat(
        [
            a[keys + ["source_sheet", "source_excel_row"]],
            b.loc[b["_keep"], keys + ["source_sheet", "source_excel_row"]],
        ],
        ignore_index=True,
    )
    removed = b.loc[~b["_keep"]].copy()
    raw_count = len(a) + len(b)
    assert len(source_provenance) == raw_count
    assert len(candidate_lines) + len(removed) == raw_count
    assert int(source_provenance["included_in_candidate_view"].sum()) == len(candidate_lines)
    assert (
        source_provenance[["source_sheet", "source_excel_row"]].duplicated().sum() == 0
    )
    assert len(removed) == len(pairs)

    raw_by_type = _classify(pd.concat([a, b], ignore_index=True))
    removed_by_type = _classify(removed)
    candidate_by_type = _classify(candidate_lines)
    assert all(
        raw_by_type[key] - removed_by_type[key] == candidate_by_type[key]
        for key in raw_by_type
    )
    result = {
        "status": "candidate_only_unapproved_reversible_analysis_layer",
        "policy": "all first-sheet rows kept; from second sheet suppress only matching eight-field source lines at matched within-sheet occurrence rank",
        "source_sheet_priority": [str(name_a), str(name_b)],
        "raw_source_rows": int(raw_count),
        "candidate_view_rows": int(len(candidate_lines)),
        "second_sheet_matching_copies_excluded_in_candidate_view": int(len(removed)),
        "provenance_rows_including_every_original_line": int(len(source_provenance)),
        "first_sheet_lines_retained": int(len(a)),
        "second_sheet_lines_retained": int(b["_keep"].sum()),
        "rows_by_type_raw": raw_by_type,
        "rows_by_type_excluded_cross_sheet": removed_by_type,
        "rows_by_type_candidate": candidate_by_type,
        "hypothetical_positive_line_amount_raw_gbp": _positive_line_amount(
            pd.concat([a, b], ignore_index=True)
        ),
        "hypothetical_positive_line_amount_candidate_gbp": _positive_line_amount(
            candidate_lines
        ),
        "hypothetical_positive_line_amount_difference_gbp": _positive_line_amount(removed),
        "canonical_links_for_suppressed_rows": int(len(pairs)),
        "limitations": [
            "This candidate view is NOT an approved cleaned dataset, official sales, net revenue, or financial reporting.",
            "No source rows are modified; all source rows have unique sheet+Excel-row provenance.",
            "Within-sheet exact duplicates remain, even if multiple copies have all eight fields equal.",
            "Only exact cross-sheet line matches are suppressed in the candidate view; invoice-ID equality alone is insufficient.",
            "CSV.gz analysis and provenance files contain source data and must remain local/ignored, not committed or publicly uploaded.",
            "The source workbook is needed alongside provenance for full reversal and independent audit.",
        ],
    }
    assert round(
        result["hypothetical_positive_line_amount_raw_gbp"]
        - result["hypothetical_positive_line_amount_candidate_gbp"], 2
    ) == result["hypothetical_positive_line_amount_difference_gbp"]
    return candidate_lines, source_provenance, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--derived-dir", type=Path, default=Path("data/derived"))
    parser.add_argument("--report", type=Path, default=Path("outputs/reversible_layer_audit.json"))
    parser.add_argument("--prior-overlap-report", type=Path, default=Path("outputs/annual_sheet_overlap.json"))
    args = parser.parse_args()

    sheets = pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl")
    candidate, provenance, result = build_candidate_layer(sheets)
    result["source_workbook_sha256"] = sha256_file(args.workbook)
    if args.prior_overlap_report.is_file():
        prior = json.loads(args.prior_overlap_report.read_text(encoding="utf-8"))
        assert result["raw_source_rows"] == prior["combined_raw_rows"]
        assert result["candidate_view_rows"] == prior[
            "hypothetical_rows_if_only_cross_sheet_exact_copies_counted_once"
        ]
        assert result["second_sheet_matching_copies_excluded_in_candidate_view"] == prior[
            "exact_matching_source_line_copies_across_sheets"
        ]
        assert result["hypothetical_positive_line_amount_difference_gbp"] == prior[
            "hypothetical_duplicated_gross_positive_line_amount_gbp"
        ]
        result["independently_reconciled_with_prior_overlap_audit"] = True
    else:
        result["independently_reconciled_with_prior_overlap_audit"] = False

    args.derived_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = args.derived_dir / "candidate_analysis_lines.csv.gz"
    provenance_path = args.derived_dir / "source_line_provenance.csv.gz"
    candidate.to_csv(candidate_path, index=False, compression="gzip")
    provenance.to_csv(provenance_path, index=False, compression="gzip")
    result["local_candidate_file"] = str(candidate_path)
    result["local_provenance_file"] = str(provenance_path)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

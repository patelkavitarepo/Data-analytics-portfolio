"""Case 006: population-wide prevalence of candidate operational invoice sequences.

A candidate line is numeric invoice + negative quantity + £0 price + missing
customer ID. A candidate-only invoice has no other line types. A "short-gap
consecutive run" links invoice IDs differing by exactly 1 within the same
source sheet, if recorded timestamps differ by at most five minutes.

These are OBSERVED patterns, not certified stocktakes, losses, or corrections.
No source rows are dropped or reclassified in the workbook.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import normalize_columns, sha256_file
except ModuleNotFoundError:
    from audit import normalize_columns, sha256_file


def summarize_runs(invoices: pd.DataFrame, limit: int = 12) -> dict:
    """Cluster only same-sheet, consecutive-ID, <=5-minute-neighbor invoices."""
    if invoices.empty:
        return {
            "invoices": 0, "runs": 0, "single_invoice_runs": 0,
            "runs_size_2": 0, "runs_size_3_to_4": 0, "runs_size_5_plus": 0,
            "invoices_in_runs_size_2_plus": 0, "invoices_in_runs_size_3_plus": 0,
            "invoices_in_runs_size_5_plus": 0, "invoice_lines_in_runs_size_2_plus": 0,
            "largest_run_invoices": 0, "top_runs": [],
        }
    ordered = invoices.sort_values(["_sheet", "_num"], kind="mergesort").copy()
    same_sheet = ordered["_sheet"].eq(ordered["_sheet"].shift())
    adjacent_id = ordered["_num"].sub(ordered["_num"].shift()).eq(1)
    minutes_apart = ordered["first_time"].sub(ordered["first_time"].shift()).dt.total_seconds().abs().div(60)
    linked = same_sheet & adjacent_id & minutes_apart.le(5) & minutes_apart.notna()
    ordered["_run_id"] = (~linked).cumsum()
    runs = (
        ordered.groupby("_run_id", sort=False)
        .agg(
            sheet=("_sheet", "first"),
            first_invoice=("_num", "first"),
            last_invoice=("_num", "last"),
            invoice_count=("_num", "size"),
            source_line_count=("line_count", "sum"),
            first_time=("first_time", "min"),
            last_time=("last_time", "max"),
        )
    )
    counts = runs["invoice_count"]
    multi = counts.ge(2)
    top = runs.loc[multi].sort_values(
        ["invoice_count", "source_line_count"], ascending=[False, False]
    ).head(limit)
    examples = [
        {
            "source_sheet": str(x["sheet"]),
            "first_invoice": str(int(x["first_invoice"])),
            "last_invoice": str(int(x["last_invoice"])),
            "invoices": int(x["invoice_count"]),
            "lines": int(x["source_line_count"]),
            "first_time": pd.Timestamp(x["first_time"]).isoformat(),
            "last_time": pd.Timestamp(x["last_time"]).isoformat(),
        }
        for _, x in top.iterrows()
    ]
    assert int(counts.sum()) == len(ordered)
    return {
        "invoices": int(len(ordered)),
        "runs": int(len(runs)),
        "single_invoice_runs": int(counts.eq(1).sum()),
        "runs_size_2": int(counts.eq(2).sum()),
        "runs_size_3_to_4": int(counts.between(3, 4).sum()),
        "runs_size_5_plus": int(counts.ge(5).sum()),
        "invoices_in_runs_size_2_plus": int(counts.loc[counts.ge(2)].sum()),
        "invoices_in_runs_size_3_plus": int(counts.loc[counts.ge(3)].sum()),
        "invoices_in_runs_size_5_plus": int(counts.loc[counts.ge(5)].sum()),
        "invoice_lines_in_runs_size_2_plus": int(runs.loc[multi, "source_line_count"].sum()),
        "largest_run_invoices": int(counts.max()),
        "top_runs": examples,
    }


def investigate_population(sheets: dict[str, pd.DataFrame]) -> dict:
    if not sheets:
        raise ValueError("No source sheets provided")
    frames = []
    for sheet, raw in sheets.items():
        frame = normalize_columns(raw).copy()
        frame["_sheet"] = str(sheet)
        frames.append(frame)
    source = pd.concat(frames, ignore_index=True)
    invoice = source["invoice_no"].astype("string").str.strip()
    numeric = invoice.str.fullmatch(r"[0-9]+").fillna(False)
    data = source.loc[numeric].copy()
    data["_invoice"] = invoice.loc[numeric]
    data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["_price"] = pd.to_numeric(data["unit_price"], errors="coerce")
    data["_dt"] = pd.to_datetime(data["invoice_date"], errors="coerce")
    data["_candidate"] = (
        data["_qty"].lt(0).fillna(False)
        & data["_price"].eq(0).fillna(False)
        & data["customer_id"].isna()
    )
    # Paid positive lines are a *structural comparison*, not verified sales.
    data["_positive_priced"] = (
        data["_qty"].gt(0).fillna(False) & data["_price"].gt(0).fillna(False)
    )
    agg = (
        data.groupby(["_sheet", "_invoice"], sort=False, dropna=False)
        .agg(
            line_count=("_invoice", "size"),
            candidate_lines=("_candidate", "sum"),
            positive_priced_lines=("_positive_priced", "sum"),
            first_time=("_dt", "min"),
            last_time=("_dt", "max"),
        )
        .reset_index()
    )
    agg["_num"] = agg["_invoice"].astype("int64")
    agg["_all_candidate"] = agg["line_count"].eq(agg["candidate_lines"])
    agg["_all_positive_priced"] = agg["line_count"].eq(agg["positive_priced_lines"])

    candidates = agg.loc[agg["_all_candidate"]].copy()
    paid = agg.loc[agg["_all_positive_priced"]].copy()
    flagged = int(data["_candidate"].sum())
    only_candidate_lines = int(candidates["line_count"].sum())
    candidate_mixed = agg.loc[agg["candidate_lines"].gt(0) & ~agg["_all_candidate"]]
    assert flagged == int(agg["candidate_lines"].sum())
    assert flagged == only_candidate_lines + int(candidate_mixed["candidate_lines"].sum())
    assert (agg["_all_candidate"] & agg["_all_positive_priced"]).sum() == 0

    result = {
        "source": "UCI Online Retail II; source invoice lines",
        "status": "verified_source_observations_only",
        "total_raw_lines": int(len(source)),
        "numeric_invoice_lines": int(len(data)),
        "total_numeric_invoice_ids_within_sheet": int(len(agg)),
        "candidate_line_definition": "numeric non-C invoice, negative quantity, zero unit price, missing customer ID",
        "candidate_lines": flagged,
        "candidate_only_invoice_ids_within_sheet": int(len(candidates)),
        "candidate_lines_in_candidate_only_invoices": only_candidate_lines,
        "candidate_lines_in_mixed_invoices": int(candidate_mixed["candidate_lines"].sum()),
        "mixed_invoices_with_candidate_lines": int(len(candidate_mixed)),
        "candidate_only_invoice_line_count_breakdown": {
            "one_line": int(candidates["line_count"].eq(1).sum()),
            "two_or_more_lines": int(candidates["line_count"].ge(2).sum()),
        },
        "comparator_definition": "all lines have positive quantity and positive unit price; not verified sales",
        "positive_priced_only_invoice_ids_within_sheet": int(len(paid)),
        "run_rule": "Consecutive numeric invoice IDs within the same source sheet, each neighbor's first timestamp separated by at most five minutes, regardless of order of timestamps",
        "candidate_only_invoice_sequences": summarize_runs(candidates),
        "positive_priced_only_invoice_sequences": summarize_runs(paid),
        "coverage_by_original_sheet": {
            str(sheet): {
                "candidate_lines": int(data.loc[data["_sheet"].eq(sheet), "_candidate"].sum()),
                "candidate_only_invoice_ids": int(candidates["_sheet"].eq(sheet).sum()),
                "candidate_only_invoices_in_2_plus_runs": int(summarize_runs(candidates.loc[candidates["_sheet"].eq(sheet)])["invoices_in_runs_size_2_plus"]),
            }
            for sheet in source["_sheet"].unique()
        },
        "limits": [
            "Observed candidate shape is not proof of operational inventory adjustment or loss.",
            "Consecutive-ID and <=5-minute grouping is a deliberately chosen descriptive rule, not a verified batch boundary.",
            "Comparative groups have different invoice/line compositions; counts are not causal rates.",
            "Positive quantity and positive price do not independently certify a merchandise sale.",
            "Invoice IDs are grouped within source sheet; the same number in distinct sheets is not merged.",
            "No original rows deleted or reclassified; no revenue, cost, theft or shrinkage value computed.",
        ],
    }
    assert result["candidate_only_invoice_sequences"]["invoices"] == len(candidates)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("data/raw/online_retail_II.xlsx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/population_batch_prevalence.json"))
    args = parser.parse_args()
    report = investigate_population(pd.read_excel(args.workbook, sheet_name=None, engine="openpyxl"))
    report["workbook_sha256"] = sha256_file(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

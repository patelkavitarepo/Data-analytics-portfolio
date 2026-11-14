"""Case 012: close-time M sign flips, including rows with missing customer IDs.

Purely observational comparison of C-prefixed negative M with non-C positive M
of same absolute quantity, unit price and country within 1/5/15/60 minutes.
Customer-ID agreement is classified, never assumed for missing values.
Timestamp order is retained: negative-first, positive-first, or same minute.
An analogous positive-positive comparison is descriptive only, not a control
sufficient for a statistical/casual conclusion. No matches are called refunds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.audit import sha256_file
    from scripts.build_reversible_layer import build_candidate_layer
except ModuleNotFoundError:
    from audit import sha256_file
    from build_reversible_layer import build_candidate_layer


DIRECTIONS = ("negative_before_positive", "positive_before_negative", "same_recorded_minute")
CUSTOMER_STATES = ("known_same", "known_different", "one_missing", "both_missing")
WINDOWS = (1, 5, 15, 60)


def _prep_m(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = df.loc[df["stock_code"].astype("string").str.strip().str.upper().eq("M").fillna(False)].copy()
    m["invoice_no"] = m["invoice_no"].astype("string").str.strip()
    m["invoice_date"] = pd.to_datetime(m["invoice_date"], errors="coerce")
    m["quantity"] = pd.to_numeric(m["quantity"], errors="coerce")
    m["unit_price"] = pd.to_numeric(m["unit_price"], errors="coerce")
    m["customer_id"] = pd.to_numeric(m["customer_id"], errors="coerce")
    m["country"] = m["country"].astype("string").str.strip()
    m["_line_id"] = m.index.astype("int64")
    cancel = m["invoice_no"].str.upper().str.startswith("C").fillna(False)
    pos = m.loc[~cancel & m["quantity"].gt(0) & m["unit_price"].gt(0)].copy()
    neg = m.loc[cancel & m["quantity"].lt(0) & m["unit_price"].gt(0)].copy()
    pos["_abs_qty"] = pos["quantity"]
    neg["_abs_qty"] = -neg["quantity"]
    return pos, neg


def _pairs(pos: pd.DataFrame, neg: pd.DataFrame) -> pd.DataFrame:
    keys = ["_abs_qty", "unit_price", "country"]
    left = pos.dropna(subset=keys + ["invoice_date"])[
        keys + ["invoice_date", "invoice_no", "customer_id", "_line_id",
                "source_sheet", "source_excel_row"]
    ].rename(columns={
        "invoice_date":"positive_date", "invoice_no":"positive_invoice",
        "customer_id":"positive_customer", "_line_id":"positive_line_id",
        "source_sheet":"positive_sheet", "source_excel_row":"positive_excel_row"
    })
    right = neg.dropna(subset=keys + ["invoice_date"])[
        keys + ["invoice_date", "invoice_no", "customer_id", "_line_id",
                "source_sheet", "source_excel_row"]
    ].rename(columns={
        "invoice_date":"negative_date", "invoice_no":"negative_invoice",
        "customer_id":"negative_customer", "_line_id":"negative_line_id",
        "source_sheet":"negative_sheet", "source_excel_row":"negative_excel_row"
    })
    joined = right.merge(left, on=keys, how="inner", validate="many_to_many")
    if joined.empty:
        return joined.assign(elapsed_minutes=pd.Series(dtype="float64"),
                             direction=pd.Series(dtype="string"),
                             customer_state=pd.Series(dtype="string"),
                             comparable_amount=pd.Series(dtype="float64"),
                             adjacent_numeric_invoice_ids=pd.Series(dtype="bool"))
    joined = joined.loc[joined["positive_invoice"].ne(joined["negative_invoice"])].copy()
    joined["elapsed_minutes"] = (joined["positive_date"] - joined["negative_date"]).dt.total_seconds() / 60.
    joined["direction"] = "same_recorded_minute"
    joined.loc[joined["elapsed_minutes"].gt(0), "direction"] = "negative_before_positive"
    joined.loc[joined["elapsed_minutes"].lt(0), "direction"] = "positive_before_negative"
    pc, nc = joined["positive_customer"], joined["negative_customer"]
    joined["customer_state"] = "one_missing"
    joined.loc[pc.isna() & nc.isna(), "customer_state"] = "both_missing"
    known = pc.notna() & nc.notna()
    joined.loc[known & pc.eq(nc).fillna(False), "customer_state"] = "known_same"
    joined.loc[known & pc.ne(nc).fillna(False), "customer_state"] = "known_different"
    joined["comparable_amount"] = joined["_abs_qty"] * joined["unit_price"]
    pi = pd.to_numeric(joined["positive_invoice"], errors="coerce")
    ni = pd.to_numeric(joined["negative_invoice"].str.replace(r"^[cC]", "", regex=True), errors="coerce")
    joined["adjacent_numeric_invoice_ids"] = pi.sub(ni).abs().eq(1).fillna(False)
    return joined


def _positive_repetition_control(pos: pd.DataFrame) -> dict:
    """Descriptive positive-positive pairs with same code/quantity/price/country."""
    if len(pos) < 2:
        return {"positive_M_lines":int(len(pos)), "positive_positive_same_fields_5min_pairs":0,
                "positive_positive_same_fields_15min_pairs":0,
                "positive_positive_same_fields_15min_distinct_lines":0}
    keys = ["_abs_qty", "unit_price", "country"]
    z = pos.dropna(subset=keys + ["invoice_date"])[
        keys + ["invoice_date", "invoice_no", "_line_id"]
    ]
    pairs = z.merge(z, on=keys, suffixes=("_a","_b"), validate="many_to_many")
    pairs = pairs.loc[
        pairs["_line_id_a"].lt(pairs["_line_id_b"])
        & pairs["invoice_no_a"].ne(pairs["invoice_no_b"])
    ]
    delta = (pairs["invoice_date_a"] - pairs["invoice_date_b"]).dt.total_seconds().abs() / 60.
    short = pairs.loc[delta.le(15)]
    return {
        "positive_M_lines":int(len(pos)),
        "positive_positive_same_fields_5min_pairs":int(delta.le(5).sum()),
        "positive_positive_same_fields_15min_pairs":int(len(short)),
        "positive_positive_same_fields_15min_distinct_lines":int(
            len(set(short["_line_id_a"]) | set(short["_line_id_b"]))
        ),
    }


def _summarize_window(pairs: pd.DataFrame, minutes: int) -> dict:
    near = pairs.loc[pairs["elapsed_minutes"].abs().le(minutes)].copy()
    plausible = near.loc[near["customer_state"].ne("known_different")]
    left = plausible.groupby("positive_line_id")["negative_line_id"].nunique()
    right = plausible.groupby("negative_line_id")["positive_line_id"].nunique()
    if len(plausible):
        unique = plausible.loc[
            plausible["positive_line_id"].map(left).eq(1)
            & plausible["negative_line_id"].map(right).eq(1)
        ]
    else:
        unique = plausible
    result = {
        "minutes":minutes,
        "same_fields_ignoring_customer_pairs":int(len(near)),
        "same_fields_ignoring_customer_distinct_positive_lines":int(near["positive_line_id"].nunique()),
        "same_fields_ignoring_customer_distinct_negative_lines":int(near["negative_line_id"].nunique()),
        "direction_pair_counts":{k:int(near["direction"].eq(k).sum()) for k in DIRECTIONS},
        "customer_relation_pair_counts":{k:int(near["customer_state"].eq(k).sum()) for k in CUSTOMER_STATES},
        "different_known_customer_pairs_not_considered_links":int(near["customer_state"].eq("known_different").sum()),
        "no_known_customer_conflict_candidate_pairs":int(len(plausible)),
        "no_known_customer_conflict_candidate_positive_lines":int(plausible["positive_line_id"].nunique()),
        "no_known_customer_conflict_candidate_negative_lines":int(plausible["negative_line_id"].nunique()),
        "reciprocal_one_to_one_weak_or_strong_candidates_not_verified":int(len(unique)),
        "no_known_customer_conflict_adjacent_numeric_invoice_pair_comparisons":int(plausible["adjacent_numeric_invoice_ids"].sum()),
        "candidate_direction_pair_counts":{k:int(plausible["direction"].eq(k).sum()) for k in DIRECTIONS},
        "candidate_customer_relation_pair_counts":{k:int(plausible["customer_state"].eq(k).sum()) for k in CUSTOMER_STATES if k!="known_different"},
    }
    assert sum(result["direction_pair_counts"].values()) == len(near)
    assert sum(result["customer_relation_pair_counts"].values()) == len(near)
    return result


def _case_examples(pairs: pd.DataFrame, direction: str, count: int = 10) -> list[dict]:
    selected = pairs.loc[
        pairs["elapsed_minutes"].abs().le(15)
        & pairs["direction"].eq(direction)
        & pairs["customer_state"].ne("known_different")
    ].sort_values(["comparable_amount", "elapsed_minutes"], ascending=[False, True]).head(count)
    return [
        {
            "negative_invoice":str(r["negative_invoice"]),
            "positive_invoice":str(r["positive_invoice"]),
            "negative_timestamp":r["negative_date"].isoformat(),
            "positive_timestamp":r["positive_date"].isoformat(),
            "minutes_positive_minus_negative":round(float(r["elapsed_minutes"]), 3),
            "negative_source_sheet":str(r["negative_sheet"]),
            "negative_source_excel_row":int(r["negative_excel_row"]),
            "positive_source_sheet":str(r["positive_sheet"]),
            "positive_source_excel_row":int(r["positive_excel_row"]),
            "absolute_quantity":int(r["_abs_qty"]),
            "unit_price_gbp":round(float(r["unit_price"]), 2),
            "absolute_line_amount_gbp_not_confirmed_transfer":round(float(r["comparable_amount"]), 2),
            "customer_relation":str(r["customer_state"]),
            "adjacent_numeric_invoice_ids":bool(r["adjacent_numeric_invoice_ids"]),
        }
        for _,r in selected.iterrows()
    ]


def investigate_bidirectional_m(frame: pd.DataFrame) -> dict:
    required = ["invoice_no","stock_code","quantity","unit_price","country","invoice_date",
                "customer_id","source_sheet","source_excel_row"]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    # The original candidate view must not be modified.
    pos, neg = _prep_m(frame.reset_index(drop=True))
    pairs = _pairs(pos, neg)
    result = {
        "status":"source_observed_bidirectional_M_temporal_similarities_not_verified_reversals",
        "candidate_view_rows":int(len(frame)),
        "positive_non_C_M_lines":int(len(pos)),
        "negative_C_M_lines":int(len(neg)),
        "comparison_uses":"stock code M, absolute quantity, original numeric unit price, country and <=N minutes; customer-ID relationship separately categorized",
        "windows":{str(m):_summarize_window(pairs,m) for m in WINDOWS},
        "positive_positive_same_fields_descriptive_comparator":_positive_repetition_control(pos),
        "top_negative_before_positive_15min_nonconflicting_examples":_case_examples(pairs,"negative_before_positive",12),
        "top_positive_before_negative_15min_nonconflicting_examples":_case_examples(pairs,"positive_before_negative",8),
        "top_same_minute_15min_nonconflicting_examples":_case_examples(pairs,"same_recorded_minute",6),
        "guardrails":[
            "No candidate pairing is a proven customer refund, correction or same-event reversal.",
            "When one or both customer IDs are missing, the pair is weak even if the amount and timestamps match.",
            "Known different customers are counted as attribute similarities, explicitly NOT candidate links.",
            "Same recorded minute does not resolve true transaction order. Timestamps have minute precision.",
            "Multiple potential partners are allowed and counted without claiming uniquely matched business events.",
            "Positive-positive comparator is descriptive, not a causal/statistical control for expected cancellation rates.",
            "Only aggregate counts and bounded invoice examples are published; customer identifiers never leave memory.",
            "No lines removed and no revenue metric changed.",
        ],
    }
    assert result["windows"]["5"]["no_known_customer_conflict_candidate_pairs"] <= result["windows"]["15"]["no_known_customer_conflict_candidate_pairs"]
    return result


def investigate_original_workbook(sheets:dict[str,pd.DataFrame]) -> dict:
    candidate,provenance,layer=build_candidate_layer(sheets)
    result=investigate_bidirectional_m(candidate)
    assert result["candidate_view_rows"]==layer["candidate_view_rows"]
    result["source_rows_accounted_for_in_provenance"]=int(len(provenance))
    result["cross_sheet_canonical_links"]=int(layer["canonical_links_for_suppressed_rows"])
    return result


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook",type=Path,default=Path("data/raw/online_retail_II.xlsx"))
    p.add_argument("--output",type=Path,default=Path("outputs/manual_bidirectional_patterns.json"))
    p.add_argument("--prior-case-011",type=Path,default=Path("outputs/manual_linkage_cases.json"))
    a=p.parse_args()
    result=investigate_original_workbook(pd.read_excel(a.workbook,sheet_name=None,engine="openpyxl"))
    result["source_workbook_sha256"]=sha256_file(a.workbook)
    if a.prior_case_011.is_file():
        prior=json.loads(a.prior_case_011.read_text(encoding="utf-8"))
        assert result["positive_non_C_M_lines"]==prior["positive_non_C_M_lines"]
        assert result["negative_C_M_lines"]==prior["negative_C_M_lines"]
        assert result["cross_sheet_canonical_links"]==prior["canonical_cross_sheet_links"]
        result["independent_agreement_with_case_011"]=True
    else:
        result["independent_agreement_with_case_011"]=False
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()

"""Case 012: exactly specified sign-flip timing and identity safeguards."""
import pandas as pd
import pytest

from scripts.investigate_m_bidirectional import investigate_bidirectional_m, investigate_original_workbook
from scripts.investigate_sheet_overlap import _prepare


def line(invoice,qty,price,customer=None,date="2010-06-17 16:53",stock="M",country="United Kingdom"):
    return {"Invoice":invoice,"StockCode":stock,"Description":"Manual",
            "Quantity":qty,"InvoiceDate":pd.Timestamp(date),"Price":price,
            "Customer ID":customer,"Country":country}


def prepared(rows):
    x=_prepare(pd.DataFrame(rows))
    x["source_sheet"]="one"
    x["source_excel_row"]=range(2,len(x)+2)
    return x


def test_negative_before_positive_missing_customer_is_weak_not_discarded():
    df=prepared([
        line("C512770",-1,25111.09,17,date="2010-06-17 16:52"),
        line("512771",1,25111.09,None,date="2010-06-17 16:53"),
    ])
    r=investigate_bidirectional_m(df)
    w=r["windows"]["1"]
    assert w["same_fields_ignoring_customer_pairs"]==1
    assert w["customer_relation_pair_counts"]["one_missing"]==1
    assert w["candidate_direction_pair_counts"]["negative_before_positive"]==1
    assert w["no_known_customer_conflict_adjacent_numeric_invoice_pair_comparisons"]==1
    assert r["top_negative_before_positive_15min_nonconflicting_examples"][0]["negative_invoice"]=="C512770"


def test_positive_before_negative_known_match_and_same_minute():
    r=investigate_bidirectional_m(prepared([
        line("1",2,10,7,"2010-01-01 10:00"),
        line("C2",-2,10,7,"2010-01-01 10:04"),
        line("3",1,5,8,"2010-01-01 12:00"),
        line("C4",-1,5,8,"2010-01-01 12:00"),
    ]))
    w=r["windows"]["5"]
    assert w["no_known_customer_conflict_candidate_pairs"]==2
    assert w["customer_relation_pair_counts"]["known_same"]==2
    assert w["direction_pair_counts"]["positive_before_negative"]==1
    assert w["direction_pair_counts"]["same_recorded_minute"]==1


def test_known_different_customers_never_candidate_even_if_adjacent():
    r=investigate_bidirectional_m(prepared([
        line("C10",-1,10,1,"2010-01-01 10:00"),
        line("11",1,10,2,"2010-01-01 10:01"),
    ]))
    w=r["windows"]["5"]
    assert w["same_fields_ignoring_customer_pairs"]==1
    assert w["different_known_customer_pairs_not_considered_links"]==1
    assert w["no_known_customer_conflict_candidate_pairs"]==0
    assert r["top_negative_before_positive_15min_nonconflicting_examples"]==[]


def test_both_missing_never_become_known_same_and_many_to_many_not_unique():
    r=investigate_bidirectional_m(prepared([
        line("C10",-1,10,None,"2010-01-01 10:00"),
        line("C11",-1,10,None,"2010-01-01 10:01"),
        line("12",1,10,None,"2010-01-01 10:02"),
    ]))
    w=r["windows"]["5"]
    assert w["customer_relation_pair_counts"]["both_missing"]==2
    assert w["reciprocal_one_to_one_weak_or_strong_candidates_not_verified"]==0
    assert w["no_known_customer_conflict_candidate_pairs"]==2


def test_quantity_price_country_code_and_window_must_match():
    r=investigate_bidirectional_m(prepared([
        line("C10",-2,10,1,"2010-01-01 10:00"),
        line("11",2,11,1,"2010-01-01 10:01"),
        line("12",1,10,1,"2010-01-01 10:01"),
        line("13",2,10,1,"2010-01-01 10:02",country="France"),
        line("14",2,10,1,"2010-01-01 12:00"),
        line("15",2,10,1,"2010-01-01 10:01",stock="MANUAL"),
    ]))
    assert r["windows"]["60"]["same_fields_ignoring_customer_pairs"]==0


def test_positive_positive_comparator_counts_distinct_invoices():
    r=investigate_bidirectional_m(prepared([
        line("100",1,10,1,"2010-01-01 10:00"),
        line("101",1,10,2,"2010-01-01 10:04"),
        line("102",1,10,3,"2010-01-01 10:14"),
        line("103",1,12,4,"2010-01-01 10:04"),
    ]))
    c=r["positive_positive_same_fields_descriptive_comparator"]
    assert c["positive_positive_same_fields_5min_pairs"]==1
    assert c["positive_positive_same_fields_15min_pairs"]==3
    assert c["positive_positive_same_fields_15min_distinct_lines"]==3


def test_cross_sheet_exact_copy_is_not_second_event():
    a=pd.DataFrame([
        line("C10",-1,12,7,"2010-12-01 09:00"),
        line("11",1,12,7,"2010-12-01 09:01"),
    ])
    b=pd.DataFrame([
        line("C10",-1,12,7,"2010-12-01 09:00"),
        line("11",1,12,7,"2010-12-01 09:01"),
    ])
    r=investigate_original_workbook({"A":a,"B":b})
    assert r["source_rows_accounted_for_in_provenance"]==4
    assert r["candidate_view_rows"]==2
    assert r["cross_sheet_canonical_links"]==2
    assert r["windows"]["5"]["no_known_customer_conflict_candidate_pairs"]==1


def test_no_candidates_or_missing_required_columns():
    r=investigate_bidirectional_m(prepared([line("9",1,3,1)]))
    assert r["windows"]["5"]["same_fields_ignoring_customer_pairs"]==0
    assert r["positive_positive_same_fields_descriptive_comparator"]["positive_positive_same_fields_5min_pairs"]==0
    with pytest.raises(ValueError,match="Missing required columns"):
        investigate_bidirectional_m(pd.DataFrame())

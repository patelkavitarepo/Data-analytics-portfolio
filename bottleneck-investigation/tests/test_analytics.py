import math
from pathlib import Path
import duckdb
import pandas as pd
import pytest
from src.analytics import aggregate, metrics, adjusted, persistent
from src.validation import validate, normalize

AS_OF = "2025-03-02T12:00:00Z"


def test_unresolved_and_exact_horizons(records):
    m = metrics(aggregate(records, AS_OF))
    assert m["requests"] == 5 and m["eligible7"] == m["eligible30"] == 4
    assert m["closed7"] == m["closed30"] == 1 and m["rate30"] == 0.25
    assert m["closed_valid"] == 3 and m["median_days"] == 7 and m["p90_days"] == 31


def test_sql_python_parity(records):
    con = duckdb.connect()
    con.register("requests", records)
    sql = (
        Path(__file__).resolve().parents[1] / "sql/cohort_aggregates.sql"
    ).read_text()
    actual = con.execute(sql, {"as_of": AS_OF}).df()
    expected = aggregate(records, AS_OF)
    cols = list(expected)
    keys = cols[:5]
    pd.testing.assert_frame_equal(
        actual[cols].sort_values(keys).reset_index(drop=True),
        expected.sort_values(keys).reset_index(drop=True),
        check_dtype=False,
    )


def test_empty(records):
    d = aggregate(records.iloc[:0], AS_OF)
    assert metrics(d)["requests"] == 0 and math.isnan(metrics(d)["rate30"])
    assert adjusted(d).empty and persistent(d).empty


def test_quality_fail_closed(records):
    assert validate(records, AS_OF)["negative_duration"] == 1
    for col, value in [("request_id", "TEST-0"), ("created_at", pd.NaT)]:
        d = records.copy()
        d.loc[1, col] = value
        with pytest.raises(ValueError):
            validate(d, AS_OF)


def test_status_inconsistency(records):
    d = records.copy()
    d.loc[0, "status"] = "open"
    d.loc[1, "status"] = "closed"
    d.loc[2, "closed_at"] = pd.Timestamp("2030-01-01", tz="UTC")
    q = validate(d, AS_OF)
    assert (
        q["nonclosed_with_date"] == q["closed_without_date"] == q["future_closed"] == 1
    )
    assert metrics(aggregate(d, AS_OF))["closed30"] == 0


def test_source_schema_and_dst():
    from src.ingest import MAPPING

    with pytest.raises(ValueError, match="schema"):
        normalize(pd.DataFrame({"wrong": []}), MAPPING)
    row = {v: None for v in MAPPING.values()}
    row.update(service_request_id="TEST", requested_datetime="2025-03-09T02:30:00")
    d = normalize(pd.DataFrame([row]), MAPPING)
    assert d.created_at.isna().all()
    with pytest.raises(ValueError):
        validate(d, AS_OF)


def synthetic_cube(closed_counts):
    rows = []
    for i, closed in enumerate(closed_counts, 1):
        for agency, n in [("TEST-A", closed), ("TEST-B", 80)]:
            rows.append(
                dict(
                    created_date=f"2025-{i:02}-01",
                    category="TEST",
                    agency=agency,
                    neighborhood="TEST",
                    duration_day=-1,
                    requests=100,
                    eligible7=100,
                    closed7=n,
                    eligible30=100,
                    closed30=n,
                    closed_valid=0,
                )
            )
    return pd.DataFrame(rows)


def test_persistence_sensitivity():
    d = synthetic_cube([68, 68, 80])
    ten = persistent(d, 10).set_index("agency")
    fifteen = persistent(d, 15).set_index("agency")
    assert bool(ten.loc["TEST-A", "candidate"]) and not bool(
        fifteen.loc["TEST-A", "candidate"]
    )
    assert ten.loc["TEST-A", "qualifying_months"] == 2
    assert not bool(
        persistent(synthetic_cube([60, 60]), 10)
        .set_index("agency")
        .loc["TEST-A", "candidate"]
    )


def test_peer_exclusion_overlap():
    d = synthetic_cube([60, 60, 60])
    a = adjusted(d).query("agency=='TEST-A'")
    assert a.peer_n.eq(100).all() and a.gap_pp.round(6).eq(-20).all()
    assert adjusted(d[d.agency.eq("TEST-A")]).empty
    d.loc[d.agency.eq("TEST-A"), "eligible30"] = 29
    assert adjusted(d).empty


def test_followup_boundary(records):
    start = records.created_at.iloc[0]
    d = records.iloc[:1]
    for h in [7, 30]:
        assert (
            metrics(
                aggregate(d, start + pd.Timedelta(days=h) - pd.Timedelta(seconds=1))
            )[f"eligible{h}"]
            == 0
        )
        assert metrics(aggregate(d, start + pd.Timedelta(days=h)))[f"eligible{h}"] == 1

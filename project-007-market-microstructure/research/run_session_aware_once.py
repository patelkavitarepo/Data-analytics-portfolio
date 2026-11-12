"""D008 one-off real quote session-label verification; never model fitting.

Exactly the pinned three-stock/five-day source panel; CC BY-NC 4.0.
No future-date prices, no raw market rows in output, no whole-archive download.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, download_member, pinned_source_url,
    checksum_from_sha256sums,
)
from microstructure.quant_arena_pilot import convert_quote_rows, file_sha256, PilotError
from microstructure.stockday_labels import labels_from_quotes
from microstructure.session_labels import exchange_session, session_labels_from_quotes
from microstructure.session_oracle import verify_session_labels
from microstructure.quote_quality_sensitivity import FROZEN_PRIMARY, _counts, _compare
from microstructure.gap_boundary_audit import _long_gap_edges, _spans
from run_quote_quality_sensitivity_once import (
    _checked_source, FROZEN_DAYS, FROZEN_MEMBERS, FROZEN_SHA256,
    FROZEN_OBSERVATIONS,
)
from run_quant_arena_panel_once import (
    ROOT, EXPECTED_REVISION, MAX_STOCK_BYTES, MAX_REMOTE_BYTES,
    _available_dates_only, _first_five_quote_rows,
)


def _per_day(labels, days):
    return {day: _counts(tuple(x for x in labels if x.trading_date == day))
            for day in days}


def _check_no_session_crossing(quotes, labels):
    violations = 0
    for label in labels:
        if label.classification is None:
            continue
        origin = quotes[label.row_index]
        origin_session = exchange_session(origin.available_at)
        for j in label.target_indices:
            target = quotes[j]
            if (target.symbol != origin.symbol
                    or target.trading_date != origin.trading_date
                    or exchange_session(target.available_at) != origin_session
                    or origin_session is None):
                violations += 1
    if violations:
        raise AssertionError("explicit session-aware label illegally crossed market session")
    return violations


def _one_stock(fetch, catalog, hashes, filename, private):
    member = catalog.get(ROOT+filename)
    if member is None or not 0 < member.size <= MAX_STOCK_BYTES:
        raise RangeSourceError("publisher stock file missing or over cap")
    if fetch.bytes_transferred + member.size > MAX_REMOTE_BYTES:
        raise RangeSourceError("one-stock range request exceeds predeclared budget")
    expected = checksum_from_sha256sums(hashes, ROOT+filename)
    if expected != FROZEN_SHA256[filename]:
        raise RangeSourceError("publisher SHA256 diverged from frozen previous study")
    bytes_ = download_member(fetch, member, max_bytes=MAX_STOCK_BYTES)
    if sha256(bytes_).hexdigest() != expected:
        raise RangeSourceError("selected stock file failed independent SHA256")
    file = private / filename
    file.write_bytes(bytes_)
    del bytes_
    symbol = filename.removesuffix(".parquet")
    days, date_counts, source_rows, source_dates = _available_dates_only(file)
    if tuple(days) != FROZEN_DAYS:
        raise PilotError("selected stock dates no longer match frozen prior source")
    raw = _first_five_quote_rows(file, days)
    quotes, qc = convert_quote_rows(raw, symbol, days)
    if len(quotes) != FROZEN_OBSERVATIONS[symbol] or qc["selected_rows_by_date"] != date_counts:
        raise PilotError("selected source row count disagrees with published predecessor")

    legacy = labels_from_quotes(quotes, 5, "0.002", max_gap_seconds=30)
    baseline = _counts(legacy)
    if tuple(baseline[x] for x in ("all", "up", "stationary", "down", "unlabelled")) != FROZEN_PRIMARY[symbol]:
        raise AssertionError("D005/D006/D007 strict label baseline mismatch")

    strict = session_labels_from_quotes(quotes, 5, "0.002", max_gap_seconds=30)
    loose = session_labels_from_quotes(quotes, 5, "0.002", max_gap_seconds=None)
    check_strict = verify_session_labels(quotes, 5, "0.002", max_gap_seconds=30)
    check_loose = verify_session_labels(quotes, 5, "0.002", max_gap_seconds=None)
    if any(x["mismatches"] != 0 for x in (check_strict, check_loose)):
        raise AssertionError("session-aware quote oracle disagrees")
    if _check_no_session_crossing(quotes, strict) or _check_no_session_crossing(quotes, loose):
        raise AssertionError("session crossing unexpectedly permitted")

    gaps = _long_gap_edges(quotes, symbol)
    if len(gaps) != 5:
        raise AssertionError("source long-gap count no longer matches D007")
    spans = {
        "strict":_spans(strict, gaps)["distinct_origins_crossing_any_long_gap"],
        "no_gap":_spans(loose, gaps)["distinct_origins_crossing_any_long_gap"],
    }
    if spans != {"strict": 0, "no_gap": 0}:
        raise AssertionError("explicit session segmentation failed to block midday gaps")

    outside = Counter()
    total_outside = 0
    for quote in quotes:
        if exchange_session(quote.available_at) is None:
            total_outside += 1
            outside[quote.trading_date] += 1
    if file_sha256(file) != expected:
        raise RangeSourceError("source checksum changed during D008 analysis")
    file.unlink()

    print("SOURCE_STOCK_SESSION_VERIFIED:", symbol, "outside_count", total_outside,flush=True)
    return {
        "symbol": symbol,
        "source_sha256": expected,
        "selected_rows": len(quotes),
        "dates": list(days),
        "rows_by_date": date_counts,
        "source_availability_metadata_rows": source_rows,
        "source_availability_metadata_days": source_dates,
        "outside_session_rows": total_outside,
        "outside_session_rows_by_day": dict(sorted(outside.items())),
        "legacy_strict_reference": baseline,
        "session_strict": _counts(strict),
        "session_no_gap_unsafe_diagnostic": _counts(loose),
        "session_strict_by_day": _per_day(strict,days),
        "session_no_gap_by_day": _per_day(loose,days),
        "session_strict_changes_vs_legacy": _compare(legacy,strict),
        "session_no_gap_changes_vs_legacy": _compare(legacy,loose),
        "session_no_gap_changes_vs_session_strict": _compare(strict,loose),
        "cross_lunch_labels": spans,
        "independent_label_oracle_checked": 2*len(quotes),
        "independent_label_oracle_mismatches": 0,
        "data_not_committed": True,
    }


def _pooled(stocks, attr):
    c = Counter()
    for result in stocks:
        for field in ("all","up","stationary","down","unlabelled","eligible"):
            c[field] += result[attr][field]
    c["stationary_pct_of_eligible"] = (
        round(100*c["stationary"]/c["eligible"], 4) if c["eligible"] else None
    )
    if c["all"] != 15233 or c["eligible"] + c["unlabelled"] != c["all"]:
        raise AssertionError("pooled source counts do not reconcile")
    return dict(c)


def main():
    source_url = pinned_source_url(EXPECTED_REVISION)
    fetch = HTTPRange(source_url)
    print("D008_PINNED_SOURCE_REVISION:", EXPECTED_REVISION, flush=True)
    catalog, hashes = _checked_source(fetch)
    results = []
    with tempfile.TemporaryDirectory(prefix="qa-session-private-") as tmp:
        for filename in FROZEN_MEMBERS:
            results.append(_one_stock(fetch,catalog,hashes,filename,Path(tmp)))
    if sum(x["selected_rows"] for x in results) != 15233:
        raise AssertionError("frozen source observation count changed")
    report = {
        "status":"D008_session_aware_source_validation_not_prediction",
        "dataset":"Quant-Arena Public L1, Ashitemaru / Quant Arena / LaPlace's Eye / Einsia AI",
        "license":"CC BY-NC 4.0, noncommercial research",
        "source_url":"https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1",
        "publisher_revision":EXPECTED_REVISION,
        "source_member_hashes":FROZEN_SHA256,
        "selected_dates":list(FROZEN_DAYS),
        "original_source_rows":15233,
        "source_bytes_transferred":fetch.bytes_transferred,
        "entire_archive_downloaded_or_hash_verified":False,
        "raw_quotes_committed_or_uploaded":False,
        "heldout_later_date_prices_read":False,
        "session_rules":{
            "timezone":"Asia/Shanghai UTC+08:00",
            "morning_inclusive":"09:30:00–11:30:00",
            "afternoon_inclusive":"13:00:00–15:00:00",
            "closing_auction_warning":"14:57–15:00 is a different market phase",
        },
        "label_rule":"arithmetic mean of next 5 midpoints, ±0.002, same stock/date/session, valid flags",
        "primary_max_gap_seconds":30,
        "legacy_strict_pooled":_pooled(results,"legacy_strict_reference"),
        "session_strict_pooled":_pooled(results,"session_strict"),
        "session_no_gap_unsafe_diagnostic_pooled":_pooled(results,"session_no_gap_unsafe_diagnostic"),
        "outside_session_source_rows":sum(x["outside_session_rows"] for x in results),
        "cross_lunch_label_count_strict":0,
        "cross_lunch_label_count_no_gap_session_aware":0,
        "independent_oracle_checks":2*15233,
        "independent_oracle_mismatches":0,
        "stocks":results,
        "limitations":[
            "Session boundaries are exchange-local operational definitions, not verified per-record exchange auction state.",
            "The 14:57–15:00 closing auction is a distinct phase; primary segmentation conservatively groups it with afternoon.",
            "No-gap case is only a diagnostic, not an endorsed labeling policy.",
            "Selected dates are observed sessions, not independently certified complete sessions.",
            "No FI-2010 original Helsinki publisher-label reconstruction or future-date quote evaluation.",
            "No forecasting, feature training, execution-cost or financial-profit evaluation.",
        ],
    }
    print("QUANT_ARENA_SESSION_AWARE_BEGIN",flush=True)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    print("QUANT_ARENA_SESSION_AWARE_END",flush=True)


if __name__=="__main__":
    main()

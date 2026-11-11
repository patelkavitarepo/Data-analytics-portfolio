"""Noncommercial Quant-Arena L1 local stock/day label reconstruction pilot.

DO NOT import a FI-2010 file here. This separate source contains CNY quote
snapshots from Shenzhen during 2022-2023 (declared CC BY-NC 4.0).
No provider credentials, remote requests, market prediction, P&L or output
of row-level vendor data are part of this module.
"""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from .paths import safe_report_output
from .stockday_labels import Quote, labels_from_quotes


class PilotError(ValueError):
    """Reject unverified source files, unexpected columns and invalid rows."""


REQUIRED_FIELDS = (
    "symbol", "available_at", "source_event_time", "bid_price_1", "ask_price_1",
    "stale", "missing_depth",
)
EXPECTED_TZ_OFFSET = timedelta(hours=8)
SOURCE_URL = "https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1"
SOURCE_LICENSE = "CC BY-NC 4.0"


def file_sha256(path):
    digest = sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _local_datetime(value, label):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != EXPECTED_TZ_OFFSET:
        raise PilotError(f"{label}: expected timezone-aware Asia/Shanghai +08:00 timestamp")
    return value


def convert_quote_rows(raw_rows, symbol, days):
    """Validate and convert only selected symbol/date source observations.

    The data must be ordered by exchange date/time within the per-stock source
    file; sorting/deduplication can hide genuine source anomalies and is banned.
    Do not assume there are records at each 15-second grid point.
    """
    if not isinstance(symbol, str) or not symbol.endswith(".SZ"):
        raise PilotError("expected a literal Shenzhen .SZ symbol")
    if not days or len(set(days)) != len(days) or len(days) > 2:
        raise PilotError("pilot requires one or two distinct requested days")
    for day in days:
        try:
            x = date.fromisoformat(day)
        except (TypeError, ValueError) as exc:
            raise PilotError("invalid requested ISO trading day") from exc
        if x.isoformat() != day or not 2022 <= x.year <= 2023:
            raise PilotError("days must be canonical ISO dates in 2022-2023")
    requested = set(days)
    results = []
    source_records = 0
    invalid_source_time = 0
    selected_counts = Counter()
    previous_availability = None
    for index, item in enumerate(raw_rows):
        source_records += 1
        if source_records > 1_500_000:
            raise PilotError("one-stock pilot source row limit exceeded")
        if not isinstance(item, dict) or any(field not in item for field in REQUIRED_FIELDS):
            raise PilotError(f"row {index}: missing or misnamed column")
        if item["symbol"] != symbol:
            raise PilotError(f"row {index}: source symbol differs from chosen stock")
        available_at = _local_datetime(item["available_at"], "available_at")
        if previous_availability is not None and available_at <= previous_availability:
            raise PilotError(f"row {index}: source timestamps repeated or reversed")
        previous_availability = available_at
        day = available_at.date().isoformat()
        event_at = item["source_event_time"]
        if event_at is not None:
            event_at = _local_datetime(event_at, "source_event_time")
            if event_at > available_at:
                raise PilotError(f"row {index}: source event occurs after its availability")
        else:
            invalid_source_time += 1
        if type(item["stale"]) not in (bool, type(None)) or type(item["missing_depth"]) not in (bool, type(None)):
            raise PilotError(f"row {index}: invalid quote quality flags")
        if day not in requested:
            continue
        selected_counts[day] += 1
        # Null flags must not be interpreted as healthy quotes.
        stale = item["stale"] is not False or event_at is None
        missing = item["missing_depth"] is not False
        results.append(Quote(
            symbol=symbol, trading_date=day, available_at=available_at,
            bid=item["bid_price_1"], ask=item["ask_price_1"],
            stale=stale, missing_depth=missing,
        ))
    # The generator enforces strictly increasing (day,symbol,availability);
    # input may cross missing or halted intervals but is never resorted.
    return results, {
        "source_rows_seen": source_records,
        "source_null_event_time": invalid_source_time,
        "selected_observations": len(results),
        "selected_rows_by_date": dict(sorted(selected_counts.items())),
    }


def pilot_summary(quotes, symbol, days, *, gap_seconds=30):
    """Predeclare horizons and count labels/exclusions without model training."""
    if len(quotes) < 2:
        raise PilotError("at least two selected quote rows are needed")
    per_horizon = {}
    for horizon in (1, 2, 3, 5, 10):
        results = labels_from_quotes(quotes, horizon, max_gap_seconds=gap_seconds)
        counts = Counter(item.classification for item in results)
        exclusions = Counter(item.excluded for item in results if item.excluded is not None)
        by_day = {}
        for day in sorted(days):
            daily = Counter(
                x.classification for x in results if x.trading_date == day
            )
            by_day[day] = {
                "up": daily[1],
                "stationary": daily[2],
                "down": daily[3],
                "unlabelled": daily[None],
            }
        per_horizon[str(horizon)] = {
            "up": counts[1],
            "stationary": counts[2],
            "down": counts[3],
            "unlabelled": counts[None],
            "excluded_reasons": dict(sorted(exclusions.items())),
            "stock_date_boundary_crossings": 0,
            "daily_class_counts": by_day,
        }
        if sum(counts.values()) != len(quotes):
            raise PilotError("class tallies do not reconcile to observations")
    # Descriptive source QC, computed without training or using future labels.
    issue_counts = Counter()
    previous = None
    for q in quotes:
        if q.stale:
            issue_counts["stale_or_missing_event_time"] += 1
        if q.missing_depth:
            issue_counts["missing_or_null_depth_flag"] += 1
        bid, ask = q.bid, q.ask
        if bid is None or ask is None:
            issue_counts["absent_best_quote"] += 1
        elif bid <= 0 or ask <= bid:
            issue_counts["nonpositive_or_locked_crossed_quote"] += 1
        if (
            previous is not None and previous.symbol == q.symbol
            and previous.trading_date == q.trading_date
            and (q.available_at - previous.available_at).total_seconds() > gap_seconds
        ):
            issue_counts["consecutive_quote_gap_exceeds_cutoff"] += 1
        previous = q
    return {
        "status": "source_identifiable_stockday_labels_no_forecast",
        "selected_observation_quality_counts": dict(sorted(issue_counts.items())),
        "source": SOURCE_URL,
        "license": SOURCE_LICENSE,
        "citation": "Quant-Arena Public L1, LaPlace's Eye / Einsia AI, 2026",
        "pilot_symbol": symbol,
        "pilot_dates": sorted(days),
        "pricing": "original publisher L1 quote prices (CNY, expected decimal128(28,4))",
        "sampling": "snapshot-time sequences, no resampling or interpolation by this pilot",
        "label_rule": "average of next k stock/day valid midpoint snapshots vs origin at +/-0.002",
        "gap_seconds": gap_seconds,
        "counts_by_horizon": per_horizon,
        "limitations": [
            "Different market, stocks, years and sampling from FI-2010; does NOT verify its labels.",
            "This is a noncommercial label-construction audit, not a prediction or trading backtest.",
            "Data can be stale, absent or irregular; original raw event feed not reconstructed.",
            "Missing/invalid/crossed/stale quotes and >gap cutoff interrupt segment; decisions are reported, not imputed.",
            "No original Shenzhen order queue, trade execution, slippage or P&L claims.",
        ],
    }


def audit_local_parquet(path, symbol, days, expected_sha256):
    """Read one manifest-confirmed stock parquet; never network or another stock."""
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.name != symbol + ".parquet":
        raise PilotError("use an ordinary local per-stock Parquet named SYMBOL.parquet")
    if path.stat().st_size <= 0 or path.stat().st_size > 150_000_000:
        raise PilotError("unexpected per-stock source-file size")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(x not in "0123456789abcdef" for x in expected_sha256.lower()):
        raise PilotError("expected manifest SHA-256 must be 64 hexadecimal characters")
    before = file_sha256(path)
    if before != expected_sha256.lower():
        raise PilotError("Parquet file hash differs from publisher's manifest")
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise PilotError("install pyarrow for the approved local-only Parquet pilot") from exc
    source = pq.ParquetFile(path)
    field_names = source.schema_arrow.names
    if len(set(field_names)) != len(field_names) or any(field not in field_names for field in REQUIRED_FIELDS):
        raise PilotError(f"unexpected source schema: required fields missing from {field_names!r}")
    if source.metadata.num_rows > 1_500_000:
        raise PilotError("per-stock row limit exceeded")
    # Only the minimum fields needed for independent label reconstruction.
    table = source.read(columns=list(REQUIRED_FIELDS))
    raw = table.to_pylist()
    rows, qc = convert_quote_rows(raw, symbol, days)
    report = pilot_summary(rows, symbol, days)
    after = file_sha256(path)
    if after != before:
        raise PilotError("source changed while being audited")
    report["source_provenance"] = {
        "file": path.name, "sha256": before,
        "file_bytes": path.stat().st_size,
        "actual_schema_columns": field_names,
        "available_rows": source.metadata.num_rows,
        "source_checksum_source": "publisher SHA256SUMS in pinned research TAR",
    }
    report["source_quality_counts"] = qc
    return report


def main():
    parser = argparse.ArgumentParser(description="Noncommercial local-only Quant-Arena quote label audit")
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--day", action="append", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        target = safe_report_output(args.output)
        report = audit_local_parquet(args.parquet, args.symbol, args.day, args.manifest_sha256)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (PilotError, ValueError, OSError) as exc:
        parser.error(str(exc))
    print("Local noncommercial stock/day descriptive label audit complete, no trading result.")


if __name__ == "__main__":
    main()

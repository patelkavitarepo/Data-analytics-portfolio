"""Row-level hard business rules and separately labeled advisory findings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

import pandas as pd

from .schema import CATEGORIES, COLUMNS, STATUSES


@dataclass(frozen=True)
class Finding:
    row_number: int
    record_id: str
    severity: str
    code: str
    message: str


@dataclass
class ValidationResult:
    accepted: list[dict]
    rejected: list[dict]
    findings: list[Finding]


def _timestamp(value: str) -> str:
    # ISO date + time only. Do not let pandas interpret epochs or ambiguous dates.
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)?",
        value,
    ):
        raise ValueError("Expected ISO 8601 date and time.")
    parsed = datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _quantity(value: str) -> int:
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Quantity must be an integer from 0 through 10000.") from exc
    if not number.is_finite() or number != number.to_integral_value() or not 0 <= number <= 10_000:
        raise ValueError("Quantity must be an integer from 0 through 10000.")
    return int(number)


def validate(frame: pd.DataFrame, existing_ids: set[str] | None = None) -> ValidationResult:
    """Partition rows exactly once; only accepted rows enter the outlier baseline.

    All copies of a repeated nonblank business ID are rejected within a batch.
    IDs already accepted in a prior different-content run are also rejected.
    Naive timestamps explicitly assume UTC; explicit offsets are converted to
    UTC. Outlier findings are advisory and never alter the accepted cohort.
    """
    if set(frame.columns) != set(COLUMNS) or len(frame.columns) != len(COLUMNS):
        raise ValueError("Validate requires exactly the schema columns; use an ingestion reader first.")
    existing_ids = existing_ids or set()
    cleaned = frame.fillna("").astype(str).map(lambda value: value.strip())
    duplicate_mask = cleaned["record_id"].duplicated(keep=False) & cleaned["record_id"].ne("")
    accepted = []
    rejected = []
    findings = []
    for position in range(len(cleaned)):
        row_number = position + 1
        row = {name: cleaned.iloc[position][name] for name in COLUMNS}
        raw_row = {"row_number": row_number, **{name: str(frame.iloc[position][name]) if pd.notna(frame.iloc[position][name]) else "" for name in COLUMNS}}
        row_findings = []

        def error(code: str, message: str) -> None:
            row_findings.append(Finding(row_number, row["record_id"], "error", code, message))

        for name in COLUMNS:
            if not row[name]:
                error("missing_value", f"{name} is required and cannot be blank.")
        if duplicate_mask.iloc[position]:
            error("duplicate_id", "Business ID appears more than once in this input; all copies are rejected.")
        if row["record_id"] and row["record_id"] in existing_ids:
            error("duplicate_existing", "Business ID was accepted in an earlier different-content run.")
        normalized_timestamp = None
        if row["event_timestamp_utc"]:
            try:
                normalized_timestamp = _timestamp(row["event_timestamp_utc"])
            except (ValueError, OverflowError):
                error("invalid_timestamp", "Use a valid ISO 8601 timestamp with seconds; naive timestamps assume UTC.")
        quantity = None
        if row["quantity"]:
            try:
                quantity = _quantity(row["quantity"])
            except ValueError as exc:
                error("invalid_quantity", str(exc))
        if row["category"] and row["category"] not in CATEGORIES:
            error("invalid_category", "category must be delivery, maintenance, or support.")
        if row["status"] and row["status"] not in STATUSES:
            error("invalid_status", "status must be pending, completed, or cancelled.")
        if quantity is not None and row["status"] in STATUSES:
            if (row["status"] == "cancelled" and quantity != 0) or (row["status"] != "cancelled" and quantity == 0):
                error("inconsistent_status", "Cancelled records require quantity 0; pending/completed records require positive quantity.")
        if row_findings:
            rejected.append(raw_row)
            findings.extend(row_findings)
        else:
            accepted.append({"row_number": row_number, **row, "event_timestamp_utc": normalized_timestamp, "quantity": quantity})
    if len(accepted) >= 8:
        quantities = pd.Series([row["quantity"] for row in accepted], dtype=float)
        median = quantities.median()
        mad = (quantities - median).abs().median()
        scores = (quantities - median).abs() * 0.6745 / max(float(mad), 1.0)
        for row, score in zip(accepted, scores):
            if score > 3.5:
                findings.append(Finding(row["row_number"], row["record_id"], "advisory", "quantity_outlier", "Quantity is unusual relative to this accepted batch (robust score > 3.5); review, not a proven error."))
    return ValidationResult(accepted=accepted, rejected=rejected, findings=findings)

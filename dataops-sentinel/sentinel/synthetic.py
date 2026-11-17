"""Reproduce the fictional operations fixture and its independent truth labels.

No records describe actual people, customers, locations, or business outcomes.
The truth manifest is an evaluation artifact; validation must not read its labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


SEED = 1729
FIELDS = (
    "record_id",
    "event_timestamp_utc",
    "location",
    "category",
    "quantity",
    "status",
)


def generate(seed: int = SEED) -> tuple[bytes, dict]:
    """Return deterministic CSV bytes and row-level truth for the given seed.

    Row numbers start at one *after* the CSV header. Both members of the
    duplicate pair are labeled hard errors because the validator rejects every
    member of an ambiguous within-file business-ID group.
    """
    rng = random.Random(seed)
    start = datetime(2026, 1, 5, 9, tzinfo=timezone.utc)
    rows: list[dict] = []
    labels: list[dict] = []

    def append(row: dict, *, hard_error: bool = False, advisory: bool = False,
               reason: str = "Synthetic baseline; no injected anomaly.") -> None:
        rows.append(row)
        labels.append({
            "row_number": len(rows),
            "record_id": row["record_id"],
            "hard_error": hard_error,
            "advisory": advisory,
            "reason": reason,
        })

    def base_row(number: int) -> dict:
        return {
            "record_id": f"SYN-{number:04d}",
            "event_timestamp_utc": (start + timedelta(minutes=15 * (number - 1)))
                .isoformat().replace("+00:00", "Z"),
            "location": rng.choice(("Synthetic Hub Amber", "Synthetic Hub Birch",
                                    "Synthetic Hub Cobalt")),
            "category": rng.choice(("delivery", "maintenance", "support")),
            "quantity": str(rng.randint(8, 12)),
            "status": rng.choice(("completed", "pending")),
        }

    for number in range(1, 41):
        append(base_row(number))

    row = base_row(41)
    row["location"] = ""
    append(row, hard_error=True, reason="Injected missing required location.")

    row = base_row(42)
    row["record_id"] = ""
    append(row, hard_error=True, reason="Injected missing required business ID.")

    for number in (43, 44):
        row = base_row(number)
        row["record_id"] = "SYN-DUPLICATE"
        append(row, hard_error=True,
               reason="Injected duplicate business ID; reject both group members.")

    row = base_row(45)
    row["event_timestamp_utc"] = "2026-02-30T09:00:00Z"
    append(row, hard_error=True, reason="Injected impossible calendar date.")

    row = base_row(46)
    row["quantity"] = "-3"
    append(row, hard_error=True, reason="Injected negative quantity.")

    row = base_row(47)
    row["quantity"] = "10001"
    append(row, hard_error=True, reason="Injected quantity above the 10000 maximum.")

    row = base_row(48)
    row.update(status="cancelled", quantity="10")
    append(row, hard_error=True,
           reason="Injected status inconsistency: cancelled records require zero quantity.")

    row = base_row(49)
    row["status"] = "mystery"
    append(row, hard_error=True, reason="Injected status outside the allowed vocabulary.")

    row = base_row(50)
    row.update(status="completed", quantity="500")
    append(row, advisory=True,
           reason="Injected suspicious but valid quantity; advisory only, remains accepted.")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    raw = output.getvalue().encode("utf-8")
    rejected = sum(label["hard_error"] for label in labels)
    manifest = {
        "synthetic": True,
        "seed": seed,
        "description": (
            "Entirely fictional operations records generated with Python random.Random. "
            "Labels describe deliberately injected anomalies, not empirical business findings. "
            "Data row numbers exclude the header. Advisory labels are not proven errors."
        ),
        "source_file": "synthetic_operations.csv",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "expected": {
            "input_count": len(rows),
            "accepted_count": len(rows) - rejected,
            "rejected_count": rejected,
            "advisory_count": sum(label["advisory"] for label in labels),
        },
        "labels": labels,
    }
    return raw, manifest


def write_fixture(output_dir: Path, seed: int = SEED) -> dict:
    """Write only the two named fixture artifacts; return the truth manifest."""
    raw, manifest = generate(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "synthetic_operations.csv").write_bytes(raw)
    (output_dir / "truth_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    manifest = write_fixture(args.output_dir, args.seed)
    print(json.dumps({"synthetic": True, "seed": args.seed,
                      "source_sha256": manifest["source_sha256"],
                      **manifest["expected"]}, indent=2))


if __name__ == "__main__":
    main()

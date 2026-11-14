"""Local-only CLI: python -m microstructure --messages ... --orderbook ..."""
import argparse
import json
from pathlib import Path
from .audit import AuditError, audit_pairs
from .paths import safe_report_output


def main():
    parser = argparse.ArgumentParser(description="Audit locally supplied LOBSTER paired CSVs")
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--orderbook", type=Path, required=True)
    parser.add_argument("--levels", type=int, default=1)
    limit = parser.add_mutually_exclusive_group()
    limit.add_argument("--max-events", type=int, default=10000)
    limit.add_argument("--full-file", action="store_true", help="Audit every paired row")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = safe_report_output(args.output)
        result = audit_pairs(args.messages, args.orderbook, args.levels, None if args.full_file else args.max_events)
    except (AuditError, OSError, ValueError) as exc:
        parser.error(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Audit complete; locally stored metadata only. Not a trading result.")


if __name__ == "__main__":
    main()

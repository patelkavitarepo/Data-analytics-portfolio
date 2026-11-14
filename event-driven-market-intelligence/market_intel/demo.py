"""Run deterministic, offline research fixture: python -m market_intel.demo."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .engine import replay
from .models import load_case

DEFAULT_CASE = Path(__file__).resolve().parent.parent / "data" / "synthetic_scenario.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="SYNTHETIC event-intelligence proof of concept")
    parser.add_argument("--as-of", help="Point-in-time cutoff (ISO-8601 with timezone)")
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    args = parser.parse_args()
    case = load_case(args.case)
    report = {"simulation_warning": "SYNTHETIC ONLY; no real company operational claims",
              "research_scope": "Point-in-time replay of assumed circular proximity and mock statements",
              "alert_revisions": replay(case, args.as_of)}
    data = json.dumps(report, sort_keys=True, indent=2)
    print(data)
    print("SHA256=" + hashlib.sha256(data.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()

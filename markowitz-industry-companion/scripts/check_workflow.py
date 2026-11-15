"""Validate only committed workflow configuration; never acquires source data."""
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from industry_companion.workflow_safety import validate_manual_workflow


if __name__ == '__main__':
    try:
        path = ROOT.parent / '.github/workflows/industry-companion-audit.yml'
        validate_manual_workflow(yaml.safe_load(path.read_text()))
        print('PASS: manual dispatcher is synthetic by default, pinned and restricted; live scope review is separate.')
    except Exception:
        print('UNSAFE_MANUAL_WORKFLOW')
        raise SystemExit(1)

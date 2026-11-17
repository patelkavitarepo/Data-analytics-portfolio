"""Small offline CLI using the same ingestion, storage and reporting as the UI."""

import argparse
import json
from pathlib import Path
import sqlite3

from .ingestion import IngestionError, read_csv_bytes, read_json_bytes
from .reporting import clean_csv, quality_report
from .repository import Repository


def main():
    parser = argparse.ArgumentParser(description='Audit a small offline CSV/JSON operations feed.')
    parser.add_argument('input', type=Path)
    parser.add_argument('--db', type=Path, required=True, help='Local SQLite audit path')
    parser.add_argument('--format', choices=('csv', 'json'), default='csv')
    parser.add_argument('--truth', type=Path, help='Synthetic truth manifest for this exact input')
    parser.add_argument('--report', type=Path, help='Write derived quality report JSON')
    parser.add_argument('--clean', type=Path, help='Write accepted records as spreadsheet-safe CSV')
    args = parser.parse_args()
    # Prevent accidentally overwriting the source, truth, audit, or another export.
    paths = [p.resolve() for p in (args.input, args.db, args.truth, args.report, args.clean) if p]
    if len(paths) != len(set(paths)):
        parser.error('Input, truth, database and export paths must be different.')
    run = None
    try:
        reader = read_csv_bytes if args.format == 'csv' else read_json_bytes
        # Read at most one byte past the limit, including for unexpectedly large files.
        from .schema import MAX_BYTES
        with args.input.open('rb') as source:
            batch = reader(source.read(MAX_BYTES + 1), source_name=args.input.name)
        truth = json.loads(args.truth.read_text(encoding='utf-8')) if args.truth else None
        if args.truth and not isinstance(truth, dict):
            raise ValueError('Truth manifest must be a JSON object.')
        run = Repository(args.db).ingest(batch)
        report = quality_report(run, truth=truth)
        if args.report:
            args.report.write_text(report, encoding='utf-8')
        if args.clean:
            args.clean.write_text(clean_csv(run), encoding='utf-8', newline='')
    except (OSError, ValueError, IngestionError, sqlite3.Error) as exc:
        saved = f' Audit {run["run_id"]} was saved; exact-input retry safely reuses it.' if run else ''
        parser.exit(2, f'Cannot complete audit/export: {exc}.{saved}\n')
    print(json.dumps({k: run[k] for k in (
        'run_id', 'input_count', 'accepted_count', 'rejected_count', 'advisory_count', 'reused',
    )}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

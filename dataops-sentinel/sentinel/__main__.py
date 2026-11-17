"""Small offline CLI using the same ingestion, storage and reporting as the UI."""

import argparse
from itertools import combinations
import json
from pathlib import Path
import sqlite3

from .ingestion import IngestionError, read_csv_bytes, read_json_bytes
from .reporting import clean_csv, quality_report
from .repository import Repository
from .schema import MAX_BYTES


def _same_file(left: Path, right: Path) -> bool:
    """Compare resolved names and existing inodes, including hardlink aliases."""
    return left == right or (left.exists() and right.exists() and left.samefile(right))


def main():
    parser = argparse.ArgumentParser(description='Audit a small offline CSV/JSON operations feed.')
    parser.add_argument('input', type=Path)
    parser.add_argument('--db', type=Path, required=True, help='Local SQLite audit path')
    parser.add_argument('--format', choices=('csv', 'json'), default='csv')
    parser.add_argument('--truth', type=Path, help='Synthetic truth manifest for this exact input')
    parser.add_argument('--report', type=Path, help='Write derived quality report JSON')
    parser.add_argument('--clean', type=Path, help='Write accepted records as spreadsheet-safe CSV')
    args = parser.parse_args()
    run = None
    try:
        # Protect both names and existing inodes before creating the audit or exports.
        try:
            paths = [p.resolve() for p in (args.input, args.db, args.truth, args.report, args.clean) if p]
            database = args.db.resolve()
        except RuntimeError as exc:
            raise ValueError(f'Cannot resolve audit paths: {exc}') from exc
        if any(_same_file(left, right) for left, right in combinations(paths, 2)):
            parser.error('Input, truth, database and export paths must be different.')
        companions = [Path(str(database) + suffix) for suffix in ('-journal', '-wal', '-shm')]
        if any(_same_file(path, companion) for path in paths for companion in companions):
            parser.error('Input, truth and export paths must not use SQLite database companion files.')
        reader = read_csv_bytes if args.format == 'csv' else read_json_bytes
        # Read at most one byte past the limit, including for unexpectedly large files.
        with args.input.open('rb') as source:
            batch = reader(source.read(MAX_BYTES + 1), source_name=args.input.name)
        truth = None
        if args.truth:
            with args.truth.open('rb') as source:
                truth_raw = source.read(MAX_BYTES + 1)
            if len(truth_raw) > MAX_BYTES:
                raise ValueError(f'Truth manifest exceeds the {MAX_BYTES:,}-byte (2 MiB) limit.')
            try:
                truth = json.loads(truth_raw.decode('utf-8'))
            except RecursionError as exc:
                raise ValueError('Truth manifest nesting is too deep; supply a JSON object with row labels.') from exc
            if not isinstance(truth, dict):
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

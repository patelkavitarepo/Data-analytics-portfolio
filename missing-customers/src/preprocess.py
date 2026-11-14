"""Bounded-memory UTC date slicing; does not deduplicate across chunks."""
import argparse
from pathlib import Path
import pandas as pd
from .analytics import REQUIRED


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--start', required=True, help='Inclusive UTC date YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='Inclusive UTC date YYYY-MM-DD')
    args = parser.parse_args()
    start = pd.Timestamp(args.start, tz='UTC')
    end = pd.Timestamp(args.end, tz='UTC') + pd.Timedelta(days=1)
    if start >= end:
        parser.error('start must be on or before end')
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        parser.error('output must be a new file')
    rows = 0
    try:
        with args.output.open('x') as target:
            first = True
            for chunk in pd.read_csv(args.input, dtype='string', chunksize=100_000):
                if REQUIRED - set(chunk.columns):
                    raise ValueError('Missing required columns')
                times = pd.to_datetime(pd.to_numeric(chunk.timestamp, errors='coerce'), unit='ms', utc=True, errors='coerce')
                part = chunk.loc[times.ge(start) & times.lt(end)]
                part.to_csv(target, index=False, header=first)
                first = False
                rows += len(part)
    except Exception:
        args.output.unlink(missing_ok=True)
        raise
    print(f'Wrote {rows} rows. This is a date slice, not a complete visitor history. Run the app audit; keep source provenance and original file.')


if __name__ == '__main__':
    main()

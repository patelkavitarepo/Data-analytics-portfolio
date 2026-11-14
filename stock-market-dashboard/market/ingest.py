"""Load a provenance-documented snapshot or a user-supplied OHLCV CSV."""
import argparse
from pathlib import Path
import pandas as pd
from market.store import ingest

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=ROOT / 'data/history.csv')
    parser.add_argument('--db', type=Path, default=ROOT / 'data/market.sqlite')
    args = parser.parse_args()
    print(f'Loaded {ingest(args.db, pd.read_csv(args.csv)):,} rows into {args.db}')


if __name__ == '__main__':
    main()

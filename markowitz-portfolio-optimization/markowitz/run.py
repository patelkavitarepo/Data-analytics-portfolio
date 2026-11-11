"""CLI: python -m markowitz.run --output work/run [--csv ... --source ...]."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path

from .data import TICKERS, audit_prices, download_prices, read_csv
from .research import PROTOCOL, evaluate, evaluate_validation


def main():
    parser = argparse.ArgumentParser(description='Real-data research only; no synthetic fallback.')
    parser.add_argument('--csv', type=Path)
    parser.add_argument('--source', help='Required CSV source, retrieval time and adjustment attestation')
    parser.add_argument('--output', type=Path, default=Path('work/run'))
    parser.add_argument('--reveal-holdout', action='store_true', help='Consumes the final holdout; do not tune after viewing')
    parser.add_argument('--cap', type=float, default=.35)
    parser.add_argument('--rf', type=float, default=.02, help='Constant effective annual assumption in decimal units')
    parser.add_argument('--cost-bps', type=float, default=10.)
    args = parser.parse_args()
    if args.csv and not args.source:
        parser.error('--source is required for CSV: supply only real split/dividend-adjusted prices with use rights')
    args.output.mkdir(parents=True, exist_ok=True)
    if args.csv:
        prices = read_csv(args.csv.read_bytes())
        provenance = {'vendor': 'user CSV', 'source': args.source, 'loaded_utc': datetime.now(timezone.utc).isoformat()}
    else:
        prices, provenance = download_prices()
    _, returns, audit, summary = audit_prices(prices)
    audit.to_csv(args.output / 'quality_audit.csv')
    manifest = {'protocol': PROTOCOL, 'provenance': provenance, 'quality': summary,
        'cap': args.cap, 'constant_effective_annual_rf_assumption': args.rf, 'cost_bps': args.cost_bps,
        'holdout_revealed': args.reveal_holdout,
        'versions': {p: version(p) for p in ('numpy', 'pandas', 'scipy', 'yfinance', 'exchange-calendars')}}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    if summary['lost_price_rows']:
        raise SystemExit('INCOMPLETE HISTORY: audit saved; no backtest run. No missing interval may be skipped.')
    evaluator = evaluate if args.reveal_holdout else evaluate_validation
    for cost in (0., args.cost_bps):
        results = evaluator(returns, list(TICKERS), args.cap, args.rf, cost)
        for period, result in results.items():
            for table in ('weights', 'metrics', 'returns', 'turnover'):
                result[table].to_csv(args.output / f'{period}_{cost:g}bps_{table}.csv')
            manifest[f'{period}_{cost:g}bps'] = {k: v for k, v in result.items() if k not in ('weights', 'metrics', 'returns', 'turnover')}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f'Research tables and provenance saved to {args.output}; owner interpretation required.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(f'RESEARCH BLOCKED: {exc}') from None

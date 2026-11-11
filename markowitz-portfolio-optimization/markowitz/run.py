"""CLI: python -m markowitz.run --output work/run [--csv ... --source ...]."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path

from .data import TICKERS, audit_prices, download_prices, read_csv
from .research import PROTOCOL, evaluate, evaluate_validation
from .verification import verify_source, source_review_template


def main():
    parser = argparse.ArgumentParser(description='Real-data research only; no synthetic fallback.')
    parser.add_argument('--csv', type=Path)
    parser.add_argument('--as-of', help='Explicit archived snapshot cutoff YYYY-MM-DD; required with --csv')
    parser.add_argument('--source-review', type=Path, help='Independent source/rights/spot-check review JSON required before evaluation')
    parser.add_argument('--source', help='Required CSV source, retrieval time and adjustment attestation')
    parser.add_argument('--output', type=Path, default=Path('work/run'))
    parser.add_argument('--reveal-holdout', action='store_true', help='Consumes the final holdout; do not tune after viewing')
    parser.add_argument('--cap', type=float, default=.35)
    parser.add_argument('--rf', type=float, default=.02, help='Constant effective annual assumption in decimal units')
    parser.add_argument('--cost-bps', type=float, default=10.)
    args = parser.parse_args()
    if args.csv and (not args.source or not args.as_of):
        parser.error('--source and --as-of are required for archived CSV analysis; analysis rights are separate from redistribution rights')
    args.output.mkdir(parents=True, exist_ok=True)
    if args.csv:
        prices = read_csv(args.csv.read_bytes())
        provenance = {'vendor': 'user CSV', 'source': args.source, 'loaded_utc': datetime.now(timezone.utc).isoformat()}
    else:
        prices, provenance = download_prices()
    _, returns, audit, summary = audit_prices(prices, as_of=args.as_of)
    audit.to_csv(args.output / 'quality_audit.csv')
    manifest = {'protocol': PROTOCOL, 'provenance': provenance, 'quality': summary,
        'as_of': summary['as_of'], 'cap': args.cap, 'constant_effective_annual_rf_assumption': args.rf, 'cost_bps': args.cost_bps,
        'holdout_revealed': args.reveal_holdout,
        'versions': {p: version(p) for p in ('numpy', 'pandas', 'scipy', 'yfinance', 'exchange-calendars')}}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    if summary['lost_price_rows']:
        raise SystemExit('INCOMPLETE HISTORY: audit saved; no backtest run. No missing interval may be skipped.')
    (args.output / 'source_review_template.json').write_text(json.dumps(source_review_template(summary), indent=2))
    if not args.source_review:
        raise SystemExit('SOURCE UNVERIFIED: audit saved; supply --source-review with adjustment, analysis rights and all-eight independent spot checks. No performance computed.')
    manifest['source_verification'] = verify_source(prices, summary, json.loads(args.source_review.read_text()))
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
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

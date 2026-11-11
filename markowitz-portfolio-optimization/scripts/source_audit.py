"""Ephemeral real-price acquisition audit only; never calculate/print performance.

No raw price artifact is retained/uploaded. Successful acquisition is not source
verification, entitlement confirmation, or authorization to reveal holdout.
"""
from datetime import datetime, timezone
import contextlib
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from markowitz.data import TICKERS, audit_prices, download_prices


def main():
    # Suppress third-party diagnostics to avoid vendor payloads in public logs.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            prices, metadata = download_prices()
            _, _, coverage, audit = audit_prices(prices)
            evidence = {'acquisition': 'success', 'provenance': metadata,
                'coverage': coverage.reset_index().to_dict(orient='records'),
                'audit': {k: audit[k] for k in ('as_of', 'snapshot_last_observed', 'expected_sessions',
                    'common_prices', 'lost_price_rows', 'duplicate_rows', 'nonpositive_prices',
                    'misaligned_sessions', 'sha256_canonical_prices')},
                'all_eight_etfs_present': set(TICKERS).issubset(prices.columns),
                'independent_reference_verification': 'pending; Nasdaq page probe returned 403 in initial runner check',
                'analysis_permissions': 'not established; source terms require human review',
                'redistribution_permissions': 'not established; no raw prices published',
                'validation_performance': 'NOT COMPUTED', 'holdout_performance': 'NOT COMPUTED'}
        except Exception as exc:
            evidence = {'acquisition': 'failed', 'error_type': type(exc).__name__,
                'validation_performance': 'NOT COMPUTED', 'holdout_performance': 'NOT COMPUTED'}
    print(json.dumps({'environment': 'GitHub-hosted Actions',
        'checked_utc': datetime.now(timezone.utc).isoformat(), **evidence}, indent=2))


if __name__ == '__main__':
    main()

"""Bounded, public documentation receipts on GitHub. No financial API access.

Only status, hash and predeclared phrase detections are printed. Detections are
not license decisions. Terms must be reviewed in full with applicable contracts.
"""
from datetime import datetime, timezone
import hashlib
import html
import json
import os
import re
import urllib.error
import urllib.request

DOCUMENTS = (
    ('yahoo_terms', 'https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html',
     {'prior_permission': r'express,?\s+prior\s+permission', 'automated_means': r'automated\s+means'}),
    ('yfinance_notice', 'https://ranaroussi.github.io/yfinance/',
     {'personal_use_only': r'personal\s+use\s+only', 'refer_to_yahoo_terms': r'terms\s+of\s+use'}),
    ('tiingo_terms', 'https://www.tiingo.com/tos/',
     {'derived_products': r'Derived\s+Products', 'starter_plan': r'Starter\s+Plan',
      'dataset_validation_restriction': r'validate,\s*reconcile,\s*or\s*confirm\s+another\s+dataset'}),
    ('eodhd_terms', 'https://eodhd.com/financial-apis/terms-conditions',
     {'private_noncommercial': r'private,?\s*non-commercial', 'redistribution_restriction': r'redistributing'}),
    ('eodhd_personal_use', 'https://eodhd.com/help/personal-use',
     {'publication_question': r'publish\s+only\s+derived', 'quality_checks': r'quality\s+checks'}),
    ('sharadar_terms', 'https://sharadar.com/terms',
     {'personal_use_license': r'Personal\s+Use\s+License', 'prior_approval': r'prior\s+written\s+approval'}),
    ('alpha_vantage_docs', 'https://www.alphavantage.co/documentation/',
     {'daily_adjusted': r'TIME_SERIES_DAILY_ADJUSTED', 'premium': r'premium\s+API'}),
)
MAX_BYTES = 2_000_000


def receipt(name, url, patterns, opener=None):
    opener = opener or urllib.request.build_opener()
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Project006-public-documentation-review/1.0'})
        with opener.open(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
            status = response.status
        if len(raw) > MAX_BYTES:
            return {'document': name, 'url': url, 'http_status': status, 'error': 'SizeLimitExceeded'}
        text = html.unescape(re.sub('<[^>]+>', ' ', raw.decode('utf-8', errors='replace')))
        text = re.sub(r'\s+', ' ', text)
        return {'document': name, 'url': url, 'http_status': status,
            'sha256': hashlib.sha256(raw).hexdigest(),
            'phrase_detections': {key: bool(re.search(pattern, text, flags=re.I)) for key, pattern in patterns.items()},
            'permission_granted': False, 'note': 'Receipt only; no automated legal conclusion.'}
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        return {'document': name, 'url': url, 'http_status': status}
    except Exception as exc:
        return {'document': name, 'url': url, 'http_status': None, 'error': type(exc).__name__}


def main():
    print(json.dumps({'environment': 'GitHub-hosted Actions' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'Codex/local',
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'market_data_collected': False, 'validation_computed': False, 'holdout_computed': False,
        'receipts': [receipt(*doc) for doc in DOCUMENTS]}, indent=2))


if __name__ == '__main__':
    main()

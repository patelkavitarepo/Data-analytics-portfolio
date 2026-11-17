"""Status-only public endpoint probes. No bodies, headers or credentials logged."""
from datetime import datetime, timezone
import json
import os
import urllib.error
import urllib.request

# Status probes are documentation-only. Do not probe Yahoo chart endpoints
# while collection permission is unestablished, even if the body is discarded.
ENDPOINTS = (
    ('legal.yahoo.com', 'https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html'),
    ('ranaroussi.github.io', 'https://ranaroussi.github.io/yfinance/'),
    ('www.alphavantage.co', 'https://www.alphavantage.co/terms_of_service/'),
    ('www.tiingo.com', 'https://www.tiingo.com/tos/'),
)



class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(host, url, opener=None):
    opener = opener or urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'Project006-connectivity-check/1.0'})
    try:
        with opener.open(request, timeout=15) as response:
            status = response.status
        return {'host': host, 'http_status': status, 'transport': 'http_response'}
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        return {'host': host, 'http_status': status, 'transport': 'http_response'}
    except Exception as exc:
        # Exception messages can contain URLs, headers or environment details.
        return {'host': host, 'http_status': None, 'transport': type(exc).__name__}


def main():
    environment = 'GitHub-hosted Actions' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'Codex/local execution'
    print(json.dumps({'environment': environment, 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'note': 'Status only. No response body read, no credentials used. HTTP access does not verify data or grant use rights.',
        'endpoints': [probe(host, url) for host, url in ENDPOINTS]}, indent=2))


if __name__ == '__main__':
    main()

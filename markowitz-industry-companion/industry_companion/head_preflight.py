"""One fixed-URL HEAD diagnosis; no response body/header consumption or parsing.

Only the explicitly authorized manual worker calls this function. HTTP response
processing is deliberately replaced so urllib never follows redirects or drains
their bodies. A HEAD result establishes neither GET access nor dataset rights.
"""
from datetime import datetime, timezone
import urllib.error
import urllib.request

from .parser import DataError
from .safeguards import SOURCE_URL


class _HeadStatusOnly(urllib.request.HTTPErrorProcessor):
    def http_response(self, request, response):
        if request.get_method() != 'HEAD' or request.full_url != SOURCE_URL:
            raise DataError('HEAD_ONLY_OFFICIAL_SOURCE_REQUIRED')
        # Do not call the parent: it invokes redirect/error handlers that may
        # inspect Location headers, follow destinations or consume error bodies.
        return response

    https_response = http_response


def check_connectivity():
    """Never read body/headers, retry, fall back to GET, persist or print data."""
    result = 'BLOCKED_OR_UNAVAILABLE'
    try:
        request = urllib.request.Request(SOURCE_URL, method='HEAD')
        if request.get_method() != 'HEAD' or request.full_url != SOURCE_URL or request.data is not None:
            raise DataError('HEAD_ONLY_OFFICIAL_SOURCE_REQUIRED')
        opener = urllib.request.build_opener(_HeadStatusOnly())
        with opener.open(request, timeout=20) as response:
            status = response.status
            result = ('REACHABLE_HEAD_2XX' if type(status) is int and 200 <= status < 300
                      else 'HEAD_UNSUPPORTED_OR_NON_2XX')
    except urllib.error.HTTPError as error:
        # Defensive fallback for an error raised before our status processor.
        # close() releases the response without reading its message/headers/body.
        try:
            error.close()
        except Exception:
            pass
        result = 'HEAD_UNSUPPORTED_OR_NON_2XX'
    except Exception:
        # No arbitrary exception repr, URL, proxy detail or header enters output.
        result = 'BLOCKED_OR_UNAVAILABLE'
    return dict(result=result, checked_at_utc=datetime.now(timezone.utc).isoformat())

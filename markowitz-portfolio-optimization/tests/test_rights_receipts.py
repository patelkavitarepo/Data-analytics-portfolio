import hashlib
import io
import urllib.error

from scripts import rights_receipts, network_probe


class Response:
    status = 200
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, count):
        assert count == rights_receipts.MAX_BYTES + 1
        return self.data


class Opener:
    def __init__(self, data=b'', error=None):
        self.data, self.error = data, error
    def open(self, request, timeout):
        assert timeout == 15
        assert request.get_header('Authorization') is None
        if self.error:
            raise self.error
        return Response(self.data)


def test_document_receipt_is_bounded_hashed_and_does_not_grant_permission():
    raw = b'<p>express, <b>prior</b> permission</p><p>PRIVATE BODY DO NOT PUBLISH</p>'
    r = rights_receipts.receipt('test', 'https://example.invalid/terms',
                               {'prior': r'express,\s+prior\s+permission'}, Opener(raw))
    assert r['phrase_detections']['prior']
    assert r['sha256'] == hashlib.sha256(raw).hexdigest()
    assert r['permission_granted'] is False
    assert 'PRIVATE BODY' not in str(r)


def test_large_document_not_hashed_or_printed():
    result = rights_receipts.receipt('test', 'https://example.invalid/terms', {},
                                    Opener(b'x' * (rights_receipts.MAX_BYTES + 1)))
    assert result['error'] == 'SizeLimitExceeded' and 'sha256' not in result


def test_document_failures_do_not_log_vendor_or_credential_content():
    err = urllib.error.HTTPError('https://example.invalid', 403, 'SECRET', {}, io.BytesIO(b'PRIVATE'))
    result = rights_receipts.receipt('test', 'https://example.invalid/terms', {}, Opener(error=err))
    assert result['http_status'] == 403 and 'SECRET' not in str(result)
    result = rights_receipts.receipt('test', 'https://example.invalid/terms', {}, Opener(error=TimeoutError('SECRET')))
    assert result['error'] == 'TimeoutError' and 'SECRET' not in str(result)


def test_current_workflow_requests_only_documentation_not_market_data():
    urls = [doc[1] for doc in rights_receipts.DOCUMENTS] + [url for _, url in network_probe.ENDPOINTS]
    assert not any('finance.yahoo.com' in url or '/query?' in url or '/api/' in url for url in urls)

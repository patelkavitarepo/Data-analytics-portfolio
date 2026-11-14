"""Explicit opt-in bounded retrieval; never automatic CI, imports or parser use."""
from datetime import datetime, timezone
import urllib.error
import urllib.request

from .parser import MAX_ARCHIVE, DataError, archive_member
from .safeguards import SOURCE_URL


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise DataError('UNAPPROVED_SOURCE_REDIRECT')


def acquire_private(store,*,permission_active=False):
    store.gate(permission_active=permission_active)
    request=urllib.request.Request(SOURCE_URL,headers={'User-Agent':'Educational industry audit; bounded single retrieval'})
    try:
        opener=urllib.request.build_opener(NoRedirect())
        with opener.open(request,timeout=20) as response:
            if response.status!=200:raise DataError('SOURCE_HTTP_'+str(response.status))
            data=response.read(MAX_ARCHIVE+1)
        archive_member(data)  # Container sanity only; no return observations inspected.
    except DataError:raise
    except urllib.error.HTTPError as exc:raise DataError('SOURCE_HTTP_'+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError):raise DataError('SOURCE_CONNECTION_BLOCKED_OR_UNAVAILABLE') from None
    store.gate(permission_active=permission_active)
    return store.snapshot(data,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),permission_active=permission_active,acquisition_method='bounded_direct_https')

"""Bounded HTTP Range reader and plain-TAR catalog scanner.

Use to select ONE Quant-Arena research Parquet, not its entire ~6.23GB TAR.
Reject unknown archive formats and HTTP 200 replies that ignore Range.
No network activity is initiated by importing this module.
"""
from dataclasses import dataclass
import json
import re
import urllib.request


class RangeSourceError(ValueError):
    """Remote range, TAR framing or provenance failed closed."""


CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")
REPO_ROOT = "https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1"
PUBLIC_SOURCE = REPO_ROOT + "/resolve/main/quant-arena-public-l1-v1.tar"
REPO_API = "https://huggingface.co/api/datasets/Ashitemaru/Quant-Arena-Public-L1"
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def pinned_source_url(revision):
    """Never claim a guessed/abbreviated commit is a verified source revision."""
    if not isinstance(revision, str) or REVISION_PATTERN.fullmatch(revision) is None:
        raise RangeSourceError("require full 40-hex publisher revision")
    return REPO_ROOT + "/resolve/" + revision + "/quant-arena-public-l1-v1.tar"


def discover_publisher_revision():
    """Fetch bounded dataset metadata and extract current immutable Git SHA.

    The returned exact SHA is pinned in every source-range request. This
    metadata call is NOT a data download and cannot validate archive bytes.
    """
    request = urllib.request.Request(REPO_API, headers={
        "Accept": "application/json",
        "User-Agent": "Project007-Noncommercial-PublisherMetadata/0.1",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise RangeSourceError("publisher metadata API unavailable")
            chunk = response.read(250_001)
            if len(chunk) > 250_000:
                raise RangeSourceError("publisher metadata exceeded bound")
            metadata = json.loads(chunk)
    except RangeSourceError:
        raise
    except Exception as exc:
        raise RangeSourceError(
            f"publisher metadata unavailable: {type(exc).__name__}"
        ) from exc
    revision = metadata.get("sha") if isinstance(metadata, dict) else None
    if not isinstance(revision, str) or REVISION_PATTERN.fullmatch(revision) is None:
        raise RangeSourceError("publisher did not supply a valid 40-hex revision")
    return revision
MAX_ARCHIVE = 8_000_000_000
MAX_MEMBER = 150_000_000
MAX_HEADERS = 500


class HTTPRange:
    """Range-only network adapter; check 206, range bounds and exact byte count."""

    def __init__(self, url=PUBLIC_SOURCE):
        if not url.startswith(REPO_ROOT + "/resolve/") or not url.endswith(
            "/quant-arena-public-l1-v1.tar"
        ):
            raise RangeSourceError("source must be the publisher's declared TAR path")
        self.url = url
        self.total_size = None
        self.bytes_transferred = 0

    def __call__(self, start, end):
        if type(start) is not int or type(end) is not int or start < 0 or end < start:
            raise RangeSourceError("invalid range request")
        if end - start + 1 > 1_000_000:
            raise RangeSourceError("single request exceeds 1MB")
        if self.total_size is not None and end >= self.total_size:
            raise RangeSourceError("request exceeds archive size")
        req = urllib.request.Request(self.url, headers={
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
            "User-Agent": "Project007-Noncommercial-SelectiveResearch/0.1",
        })
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                if response.status != 206:
                    raise RangeSourceError(
                        f"Range ignored (HTTP {response.status}); refuse full download"
                    )
                match = CONTENT_RANGE.fullmatch(
                    response.headers.get("Content-Range") or ""
                )
                if match is None:
                    raise RangeSourceError("missing or malformed Content-Range")
                a, b, total = map(int, match.groups())
                if (a, b) != (start, end) or not 1024 <= total <= MAX_ARCHIVE:
                    raise RangeSourceError("wrong range or implausible archive length")
                if self.total_size is not None and self.total_size != total:
                    raise RangeSourceError("archive changed during range reads")
                self.total_size = total
                data = response.read(end - start + 2)
                if len(data) != end - start + 1:
                    raise RangeSourceError("range body length mismatch")
                self.bytes_transferred += len(data)
                return data
        except RangeSourceError:
            raise
        except Exception as exc:
            raise RangeSourceError(
                f"network range failed: {type(exc).__name__}"
            ) from exc


def _string(buf):
    return buf.split(b"\0", 1)[0].decode("utf-8", errors="strict")


def _octal(buf):
    value = buf.strip(b"\0 ")
    try:
        return int(value, 8) if value else 0
    except ValueError as exc:
        raise RangeSourceError("invalid TAR octal integer") from exc


@dataclass(frozen=True)
class TarMember:
    name: str
    data_offset: int
    size: int


def scan_tar(fetch, max_entries=MAX_HEADERS):
    """Scan only TAR headers, skipping vendor rows by their declared lengths."""
    if type(max_entries) is not int or not 1 <= max_entries <= MAX_HEADERS:
        raise ValueError("invalid TAR scan cap")
    offset, zeros = 0, 0
    entries = []
    for _ in range(max_entries):
        header = fetch(offset, offset + 511)
        if len(header) != 512:
            raise RangeSourceError("short TAR header")
        if header == b"\0" * 512:
            zeros += 1
            if zeros == 2:
                return tuple(entries)
            offset += 512
            continue
        zeros = 0
        if header[257:262] != b"ustar":
            raise RangeSourceError("unknown TAR format or extension")
        if _octal(header[148:156]) != (
            sum(header[:148]) + 8 * ord(" ") + sum(header[156:])
        ):
            raise RangeSourceError("TAR header checksum mismatch")
        size = _octal(header[124:136])
        if not 0 <= size <= MAX_ARCHIVE:
            raise RangeSourceError("invalid TAR member length")
        flag = header[156:157]
        if flag not in (b"0", b"\0", b"5"):
            raise RangeSourceError(
                "TAR PAX/extension encountered; schema review required"
            )
        name = _string(header[:100])
        prefix = _string(header[345:500])
        if prefix:
            name = prefix + "/" + name
        if name.startswith("/") or ".." in name.split("/"):
            raise RangeSourceError("unsafe TAR path")
        if not name.startswith("quant-arena-public-l1-v1/"):
            raise RangeSourceError("TAR member outside publisher release")
        if flag != b"5":
            entries.append(TarMember(name, offset + 512, size))
        offset += 512 + ((size + 511) // 512) * 512
        if hasattr(fetch, "total_size") and fetch.total_size is not None:
            if offset > fetch.total_size:
                raise RangeSourceError("TAR member extends past archive end")
    raise RangeSourceError("TAR scan cap reached before archive end")


def download_member(fetch, member, max_bytes=MAX_MEMBER):
    if not 0 < member.size <= max_bytes:
        raise RangeSourceError("selected TAR member empty or oversized")
    chunks = []
    for start in range(0, member.size, 1_000_000):
        end = min(start + 1_000_000, member.size)
        chunks.append(
            fetch(member.data_offset + start, member.data_offset + end - 1)
        )
    return b"".join(chunks)

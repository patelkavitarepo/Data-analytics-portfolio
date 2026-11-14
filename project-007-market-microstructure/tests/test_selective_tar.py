"""Every TAR and HTTP response in these tests is synthetic; no provider calls."""
import io
import tarfile
import unittest
from unittest.mock import patch

from microstructure.selective_tar import (
    HTTPRange, RangeSourceError, scan_tar, download_member,
    pinned_source_url, checksum_from_sha256sums,
)


def tar_fixture():
    data = io.BytesIO()
    content = {
        "quant-arena-public-l1-v1/manifest.json": b'{"files": {"000012.SZ.parquet": {"sha256": "abc"}}}',
        "quant-arena-public-l1-v1/000012.SZ.parquet": b"PAR1" + b"x" * 512,
    }
    with tarfile.open(fileobj=data, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name, body in content.items():
            info = tarfile.TarInfo(name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
    return data.getvalue(), content


class TarRangeTests(unittest.TestCase):
    def test_skip_payload_and_read_one_member(self):
        data, expected = tar_fixture()
        def fake_range(start, end):
            return data[start:end+1]
        members = scan_tar(fake_range)
        self.assertEqual(len(members), 2)
        for item in members:
            self.assertEqual(download_member(fake_range, item), expected[item.name])
        self.assertTrue(data.startswith(b"quant-arena-public-l1-v1/"))

    def test_reject_corrupt_header_not_silent(self):
        data, _ = tar_fixture()
        data = bytearray(data)
        data[20] = ord("!")
        with self.assertRaisesRegex(RangeSourceError, "checksum"):
            scan_tar(lambda a,b: bytes(data[a:b+1]))

    def test_wrong_root_path_rejected(self):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w", format=tarfile.USTAR_FORMAT) as tar:
            info = tarfile.TarInfo("untrusted/000012.SZ.parquet")
            info.size = 3
            tar.addfile(info, io.BytesIO(b"abc"))
        stream = data.getvalue()
        with self.assertRaisesRegex(RangeSourceError, "outside publisher"):
            scan_tar(lambda a,b: stream[a:b+1])

    def test_reject_unbounded_member_and_header_limit(self):
        data, _ = tar_fixture()
        with self.assertRaisesRegex(RangeSourceError, "scan cap"):
            scan_tar(lambda a,b: data[a:b+1], max_entries=1)
        member = scan_tar(lambda a,b: data[a:b+1])[0]
        with self.assertRaisesRegex(RangeSourceError, "oversized"):
            download_member(lambda a,b: data[a:b+1], member, max_bytes=1)

    def test_pinned_revision_must_be_full_sha(self):
        for bad in ("main", "fa85d7b", "0"*39, "", None):
            with self.subTest(revision=bad), self.assertRaises(RangeSourceError):
                pinned_source_url(bad)
        uri = pinned_source_url("a" * 40)
        self.assertTrue(uri.endswith("/" + "a" * 40 + "/quant-arena-public-l1-v1.tar"))
        with self.assertRaises(RangeSourceError):
            HTTPRange("https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1/resolve/main/quant-arena-public-l1-v1.tar")

    def test_publisher_sha256sums_text_and_binary_conventions(self):
        good = "a" * 64
        data = (
            (good + "  ./000012.SZ.parquet\\n").replace("\\n", "\n") +
            ("b" * 64 + " *other.parquet\\n").replace("\\n", "\n")
        ).encode()
        selected = checksum_from_sha256sums(
            data, "quant-arena-public-l1-v1/000012.SZ.parquet"
        )
        self.assertEqual(selected, good)
        with self.assertRaisesRegex(RangeSourceError, "unique"):
            checksum_from_sha256sums(
                (good + "  000012.SZ.parquet\\n" + good + "  ./000012.SZ.parquet\\n").replace("\\n","\n").encode(),
                "quant-arena-public-l1-v1/000012.SZ.parquet",
            )

    def test_full_content_http_200_is_rejected_before_reading(self):
        class FakeResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *exc): return False
            def read(self, _=None): raise AssertionError("body must not be read")
        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            source = HTTPRange(pinned_source_url("a" * 40))
            with self.assertRaisesRegex(RangeSourceError, "Range ignored"):
                source(0, 511)
            self.assertEqual(source.bytes_transferred, 0)


if __name__ == "__main__":
    unittest.main()

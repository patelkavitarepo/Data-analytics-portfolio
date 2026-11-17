"""Metadata-only range probe for separate Quant-Arena stock/day quote dataset.

Bounded to 4096 data bytes. No full archive, stock quotes, user credentials,
paid access, or benchmark scoring. Repo source is public CC BY-NC 4.0.
"""
import urllib.error
import urllib.request

URI = "https://huggingface.co/datasets/Ashitemaru/Quant-Arena-Public-L1/resolve/main/quant-arena-public-l1-v1.tar"
MAX_READ = 4096


def probe():
    req = urllib.request.Request(URI, headers={
        "User-Agent": "Project007-Noncommercial-RangeProbe/0.1",
        "Range": "bytes=0-4095",
        "Accept": "application/octet-stream",
    })
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            payload = response.read(MAX_READ + 1)
            print("range_probe_status:", response.status)
            print("final_url_host:", response.url.split("/")[2])
            print("content_range:", response.headers.get("Content-Range"))
            print("content_length_header:", response.headers.get("Content-Length"))
            print("read_bytes:", len(payload))
            print("partial_content_supported:", response.status == 206)
            if response.status != 206 or len(payload) > MAX_READ:
                print("stopped_early:", True)
                return
            header = payload[:512]
            print("tar_header_magic:", header[257:265].decode("ascii", errors="replace"))
            print("first_member_name:", header[:100].rstrip(b"\0").decode("utf-8", errors="replace"))
            print("first_member_size_octal:", header[124:136].decode("ascii", errors="replace").strip("\0 "))
    except Exception as ex:
        print("range_probe_error:", type(ex).__name__, str(ex)[:250])


if __name__=="__main__":
    probe()

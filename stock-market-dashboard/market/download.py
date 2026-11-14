"""Reproduce the bundled snapshot from a pinned, checksum-verified public source."""
import hashlib
import io
import json
from pathlib import Path
import pandas as pd
import requests
from market.store import validate

ROOT = Path(__file__).resolve().parents[1]


def main():
    meta = json.loads((ROOT / 'data/provenance.json').read_text())
    response = requests.get(meta['source_url'], timeout=60)
    response.raise_for_status()
    if hashlib.sha256(response.content).hexdigest() != meta['source_sha256']:
        raise ValueError('Source checksum mismatch; existing snapshot was not changed')
    data = pd.read_csv(io.BytesIO(response.content))
    data = data[data.Name.isin(meta['coverage'])].rename(columns={'Name': 'symbol'})
    validate(data)
    payload = data.to_csv(index=False).encode()
    if hashlib.sha256(payload).hexdigest() != meta['subset_sha256']:
        raise ValueError('Subset checksum mismatch; existing snapshot was not changed')
    (ROOT / 'data/history.csv').write_bytes(payload)
    print(f'Reproduced {len(data):,} historical observations; run python -m market.ingest to load SQLite.')


if __name__ == '__main__':
    main()

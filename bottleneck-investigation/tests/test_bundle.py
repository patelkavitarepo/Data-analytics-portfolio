import hashlib, json
import pytest
from src.analytics import aggregate
from src.bundle import load_bundle


def test_pending(tmp_path):
    (tmp_path / "provenance.json").write_text('{"status":"evidence_pending"}')
    assert load_bundle(tmp_path)[1] is None


def test_hash_synthetic_gate(tmp_path, records):
    path = tmp_path / "cube.parquet"
    aggregate(records, "2025-03-02T12:00:00Z").to_parquet(path, index=False)
    meta = {
        "status": "verified_public_extract",
        "synthetic": False,
        "source_url": "https://example.invalid/TEST-ONLY",
        "extracted_at": "TEST ONLY",
        "rows": 5,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }

    def save():
        (tmp_path / "provenance.json").write_text(json.dumps(meta))

    save()
    assert load_bundle(tmp_path)[1].requests.sum() == 5
    meta["synthetic"] = True
    save()
    with pytest.raises(ValueError, match="provenance"):
        load_bundle(tmp_path)
    meta["synthetic"] = False
    save()
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash"):
        load_bundle(tmp_path)

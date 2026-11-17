import csv
import hashlib
import io
import json

from sentinel.synthetic import generate, write_fixture


def test_fixed_seed_reproduces_committed_csv_and_truth(example_path, manifest_path):
    raw, manifest = generate()
    assert raw == example_path.read_bytes()
    assert manifest == json.loads(manifest_path.read_text())
    assert manifest["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert generate() == (raw, manifest)


def test_manifest_labels_every_row_independently(example_path, manifest_path):
    rows = list(csv.DictReader(io.StringIO(example_path.read_text())))
    manifest = json.loads(manifest_path.read_text())
    labels = manifest["labels"]
    assert manifest["synthetic"] is True
    assert [label["row_number"] for label in labels] == list(range(1, 51))
    assert [label["record_id"] for label in labels] == [row["record_id"] for row in rows]
    assert sum(label["hard_error"] for label in labels) == 9
    assert sum(label["advisory"] for label in labels) == 1
    assert all(label["reason"] for label in labels)
    assert manifest["expected"] == {
        "input_count": 50, "accepted_count": 41, "rejected_count": 9, "advisory_count": 1
    }


def test_writer_creates_exact_replayable_fixture(tmp_path, example_path, manifest_path):
    output_dir = tmp_path / "new-fixture"
    manifest = write_fixture(output_dir)
    assert (output_dir / "synthetic_operations.csv").read_bytes() == example_path.read_bytes()
    assert json.loads((output_dir / "truth_manifest.json").read_text()) == manifest
    assert manifest == json.loads(manifest_path.read_text())


def test_seed_changes_baseline_without_changing_deliberate_anomaly_counts():
    raw, truth = generate(seed=42)
    default_raw, default_truth = generate()
    assert raw != default_raw
    assert truth["source_sha256"] != default_truth["source_sha256"]
    assert truth["expected"] == default_truth["expected"]

import copy
import csv
import io
import json

import pytest

from sentinel.ingestion import read_csv_bytes
from sentinel.reporting import clean_csv, evaluate_truth, findings_csv, quality_report
from sentinel.repository import Repository


def demo_run(tmp_path, example_path):
    return Repository(tmp_path / "audit.sqlite").ingest(read_csv_bytes(example_path.read_bytes()))


def test_quality_report_uses_explicit_denominators(tmp_path, example_path, manifest_path):
    run = demo_run(tmp_path, example_path)
    manifest = json.loads(manifest_path.read_text())
    report = json.loads(quality_report(run, truth=manifest))
    summary = report["summary"]
    assert summary["input_count"] == 50
    assert summary["accepted_count"] == 41
    assert summary["rejected_count"] == 9
    assert summary["advisory_count"] == 1
    assert summary["accepted_rate"] == pytest.approx(41 / 50)
    assert summary["rejected_rate"] == pytest.approx(9 / 50)
    assert summary["advisory_rate_per_input"] == pytest.approx(1 / 50)
    assert summary["advisory_rate_per_accepted"] == pytest.approx(1 / 41)
    assert report["findings"] == run["findings"]
    assert report["truth_evaluation"]["row_count"] == 50


def test_truth_evaluation_reports_real_fixture_confusion_counts(tmp_path, example_path, manifest_path):
    run = demo_run(tmp_path, example_path)
    manifest = json.loads(manifest_path.read_text())
    evaluation = evaluate_truth(run, manifest)
    assert evaluation["hard_errors"] == {"tp": 9, "fp": 0, "fn": 0, "tn": 41,
                                           "precision": 1.0, "recall": 1.0}
    assert evaluation["advisories"] == {"tp": 1, "fp": 0, "fn": 0, "tn": 49,
                                         "precision": 1.0, "recall": 1.0}


def test_evaluator_can_detect_false_positives_and_negatives(tmp_path, example_path, manifest_path):
    run = demo_run(tmp_path, example_path)
    manifest = json.loads(manifest_path.read_text())
    # Deliberately perturb test-only truth, to exercise non-perfect confusion tables.
    clean = next(label for label in manifest["labels"] if not label["hard_error"] and not label["advisory"])
    bad = next(label for label in manifest["labels"] if label["hard_error"])
    advisory = next(label for label in manifest["labels"] if label["advisory"])
    clean["hard_error"] = clean["advisory"] = True
    bad["hard_error"] = False
    advisory["advisory"] = False
    evaluation = evaluate_truth(run, manifest)
    assert evaluation["hard_errors"]["fp"] == evaluation["hard_errors"]["fn"] == 1
    assert evaluation["advisories"]["fp"] == evaluation["advisories"]["fn"] == 1
    assert evaluation["hard_errors"]["precision"] == pytest.approx(8 / 9)
    assert evaluation["advisories"]["recall"] == 0


@pytest.mark.parametrize("damage", ["hash", "missing", "duplicate", "non_boolean"])
def test_truth_must_match_source_and_complete_row_labels(damage, tmp_path, example_path, manifest_path):
    run = demo_run(tmp_path, example_path)
    manifest = json.loads(manifest_path.read_text())
    if damage == "hash":
        manifest["source_sha256"] = "0" * 64
    elif damage == "missing":
        manifest["labels"].pop()
    elif damage == "duplicate":
        manifest["labels"][-1] = copy.deepcopy(manifest["labels"][0])
    else:
        manifest["labels"][0]["hard_error"] = "false"
    with pytest.raises(ValueError):
        evaluate_truth(run, manifest)


@pytest.mark.parametrize("formula", ["=1+1", "+SUM(1,2)", "-1+2", "@SUM(1,2)", "  =1+1", "\t=1+1"])
def test_csv_exports_neutralize_spreadsheet_formulas(formula, tmp_path, make_row, csv_bytes):
    # Text that passes required-field validation can still be unsafe in spreadsheets.
    run = Repository(tmp_path / "audit.sqlite").ingest(
        read_csv_bytes(csv_bytes([make_row(formula, location=formula), make_row("bad", quantity="-1")]))
    )
    clean = list(csv.DictReader(io.StringIO(clean_csv(run))))
    assert len(clean) == 1
    assert clean[0]["record_id"].lstrip()[0] == "'"
    assert clean[0]["location"].lstrip()[0] == "'"
    # Export both ID and free-text message safely without changing the stored audit.
    stored_id = run["accepted"][0]["record_id"]
    run["findings"][0]["record_id"] = formula
    run["findings"][0]["message"] = formula
    exported_findings = list(csv.DictReader(io.StringIO(findings_csv(run))))
    assert exported_findings[0]["record_id"].lstrip()[0] == "'"
    assert exported_findings[0]["message"].lstrip()[0] == "'"
    assert run["accepted"][0]["record_id"] == stored_id


def test_empty_accepted_export_still_has_header(tmp_path, make_row, csv_bytes):
    run = Repository(tmp_path / "audit.sqlite").ingest(
        read_csv_bytes(csv_bytes([make_row(quantity="-1")]))
    )
    reader = csv.DictReader(io.StringIO(clean_csv(run)))
    assert "record_id" in reader.fieldnames
    assert list(reader) == []


@pytest.mark.parametrize("manifest", [[], None, "truth", 42])
def test_truth_manifest_requires_json_object(manifest, tmp_path, example_path):
    run = demo_run(tmp_path, example_path)
    with pytest.raises(ValueError):
        evaluate_truth(run, manifest)


@pytest.mark.parametrize("labels", [None, {}, [None], [[]], ["row"], [1]])
def test_truth_labels_require_array_of_objects(labels, tmp_path, example_path, manifest_path):
    run = demo_run(tmp_path, example_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["labels"] = labels
    with pytest.raises(ValueError):
        evaluate_truth(run, manifest)


def test_fixture_truth_evaluation_requires_fresh_audit_context(tmp_path, example_path, manifest_path):
    raw = example_path.read_bytes()
    # Accept the fixture's first business ID in a separate, different-content run.
    first_row_csv = b"\n".join(raw.splitlines()[:2]) + b"\n"
    repository = Repository(tmp_path / "audit.sqlite")
    assert repository.ingest(read_csv_bytes(first_row_csv))["accepted_count"] == 1
    run = repository.ingest(read_csv_bytes(raw))
    assert (run["input_count"], run["accepted_count"], run["rejected_count"]) == (50, 40, 10)
    assert any(finding["code"] == "duplicate_existing" for finding in run["findings"])
    # The extra rejection is correct for this audit history. Fresh-fixture truth
    # must not describe it as a detector false positive or show fixture scores.
    manifest = json.loads(manifest_path.read_text())
    with pytest.raises(ValueError):
        evaluate_truth(run, manifest)

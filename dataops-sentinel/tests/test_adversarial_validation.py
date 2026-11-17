"""Review boundary cases and demonstrate the limits of a batch advisory."""

import json

import pandas as pd
import pytest

from sentinel.ingestion import read_csv_bytes
from sentinel.reporting import quality_report
from sentinel.repository import Repository
from sentinel.validation import validate


@pytest.mark.parametrize('value,flagged', [(15, False), (16, True)])
def test_robust_score_threshold_on_eight_accepted_rows(value, flagged, make_row):
    rows = [make_row(f'normal-{i}') for i in range(7)]
    rows.append(make_row('boundary', quantity=str(value)))
    checked = validate(pd.DataFrame(rows))
    assert len(checked.accepted) == 8
    assert checked.rejected == []
    assert [f.row_number for f in checked.findings] == ([8] if flagged else [])
    assert all(f.severity == 'advisory' for f in checked.findings)


def test_advisory_can_flag_a_legitimate_cancellation_without_rejecting(make_row):
    rows = [make_row(f'normal-{i}') for i in range(7)]
    rows.append(make_row('cancelled', quantity='0', status='cancelled'))
    checked = validate(pd.DataFrame(rows))
    assert len(checked.accepted) == 8
    assert checked.rejected == []
    assert [(f.row_number, f.severity) for f in checked.findings] == [(8, 'advisory')]


def test_balanced_bimodal_batch_exposes_masking_limit(make_row):
    rows = [make_row(f'normal-{i}') for i in range(5)]
    rows += [make_row(f'large-{i}', quantity='500') for i in range(5)]
    checked = validate(pd.DataFrame(rows))
    assert len(checked.accepted) == 10
    assert checked.rejected == checked.findings == []


def test_reason_counts_are_rows_and_zero_accepted_denominator_is_null(
    tmp_path, csv_bytes,
):
    # One row has six missing-field findings. Neither cohort nor reason count is six.
    row = dict(record_id='', event_timestamp_utc='', location='', category='', quantity='', status='')
    run = Repository(tmp_path / 'audit.sqlite').ingest(read_csv_bytes(csv_bytes([row])))
    report = json.loads(quality_report(run))
    assert report['summary'] == {
        'input_count': 1, 'accepted_count': 0, 'rejected_count': 1, 'advisory_count': 0,
        'accepted_rate': 0.0, 'rejected_rate': 1.0,
        'advisory_rate_per_input': 0.0, 'advisory_rate_per_accepted': None,
    }
    assert report['reason_breakdown'] == [
        {'severity': 'error', 'code': 'missing_value', 'row_count': 1, 'rate_per_input': 1.0},
    ]
    assert len(report['findings']) == 6


@pytest.mark.parametrize('timestamp', [
    '0001-01-01T00:00:00+23:59', '9999-12-31T23:59:59-23:59',
    '2026-01-01T00:00:60Z', '2026-01-01T00:00:00+24:00',
])
def test_timestamp_extreme_offset_and_leap_second_fail_without_crash(timestamp, make_row):
    checked = validate(pd.DataFrame([make_row(event_timestamp_utc=timestamp)]))
    assert checked.accepted == []
    assert len(checked.rejected) == 1
    assert [f.code for f in checked.findings] == ['invalid_timestamp']

"""Derived metrics, synthetic truth evaluation and spreadsheet-safe CSV exports."""

from collections import defaultdict
import csv
import io
import json

from .schema import COLUMNS


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def evaluate_truth(run: dict, manifest: dict) -> dict:
    """Evaluate row labels only when bound to this exact input's SHA-256.

    These are fixture diagnostics, not estimates of performance on real feeds.
    Every input row is in each denominator, including rejected rows.
    """
    if not isinstance(manifest, dict):
        raise ValueError('Truth manifest must be a JSON object.')
    if manifest.get('synthetic') is not True:
        raise ValueError('Truth evaluation requires an explicitly synthetic manifest.')
    if manifest.get('source_sha256') != run['content_hash']:
        raise ValueError('Truth manifest SHA-256 does not match this input.')
    if any(f['code'] == 'duplicate_existing' for f in run['findings']):
        raise ValueError('Synthetic truth labels assume a fresh audit without prior accepted IDs.')
    labels = manifest.get('labels', [])
    if not isinstance(labels, list) or any(not isinstance(label, dict) for label in labels):
        raise ValueError('Truth labels must be an array of row-label objects.')
    expected = set(range(1, run['input_count'] + 1))
    if (len(labels) != run['input_count']
            or any(type(label.get('row_number')) is not int for label in labels)
            or {label['row_number'] for label in labels} != expected):
        raise ValueError('Truth must label every input row exactly once.')
    if any(type(label.get(k)) is not bool for label in labels for k in ('hard_error', 'advisory')):
        raise ValueError('Truth hard_error and advisory labels must be booleans.')
    actual_errors = {r['row_number'] for r in run['rejected']}
    actual_advisories = {f['row_number'] for f in run['findings'] if f['severity'] == 'advisory'}
    result = {'row_count': run['input_count']}
    for name, key, actual in (
        ('hard_errors', 'hard_error', actual_errors),
        ('advisories', 'advisory', actual_advisories),
    ):
        truth = {label['row_number'] for label in labels if label[key]}
        tp, fp, fn = len(actual & truth), len(actual - truth), len(truth - actual)
        result[name] = {
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': len(expected - (truth | actual)),
            'precision': _ratio(tp, tp + fp), 'recall': _ratio(tp, tp + fn),
        }
    return result


def quality_report(run: dict, truth: dict | None = None) -> str:
    total, accepted = run['input_count'], run['accepted_count']
    reasons = defaultdict(set)
    for f in run['findings']:
        reasons[(f['severity'], f['code'])].add(f['row_number'])
    result = {
        'description': 'DataOps Sentinel local quality audit; demo data is synthetic.',
        'provenance': {k: run[k] for k in (
            'run_id', 'content_hash', 'source_name', 'source_kind', 'byte_count',
            'created_at', 'ruleset_version',
        )},
        'summary': {
            **{k: run[k] for k in ('input_count', 'accepted_count', 'rejected_count', 'advisory_count')},
            'accepted_rate': _ratio(accepted, total),
            'rejected_rate': _ratio(run['rejected_count'], total),
            'advisory_rate_per_input': _ratio(run['advisory_count'], total),
            'advisory_rate_per_accepted': _ratio(run['advisory_count'], accepted),
        },
        'denominators': 'Rates are fractions. Reasons count unique rows per code / input rows; '
                        'a row can have multiple reasons. Advisory rows remain accepted.',
        'reason_breakdown': [
            {'severity': severity, 'code': code, 'row_count': len(rows),
             'rate_per_input': _ratio(len(rows), total)}
            for (severity, code), rows in sorted(reasons.items())
        ],
        'findings': run['findings'],
    }
    if truth is not None:
        result['truth_evaluation'] = evaluate_truth(run, truth)
    return json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + '\n'


def _safe_cell(value):
    """Quote spreadsheet formula prefixes, including whitespace-obscured ones."""
    text = str(value)
    if text.startswith(('\t', '\r', '\n')) or text.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + text
    return value


def _csv(rows, columns):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _safe_cell(row.get(k, '')) for k in columns})
    return output.getvalue()


def clean_csv(run: dict) -> str:
    """Accepted rows only. Advisory rows remain included. Export text is sanitized."""
    return _csv(run['accepted'], COLUMNS)


def findings_csv(run: dict) -> str:
    return _csv(run['findings'], ('row_number', 'record_id', 'severity', 'code', 'message'))

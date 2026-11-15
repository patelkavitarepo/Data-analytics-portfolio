"""Explicit hosted-memory audit; synthetic by default, live rights gate closed.

This is a separate storage threat model, not a bypass of desktop PrivateStore.
It reuses the unchanged parser, audit schema and bounded acquisition function.
No raw archive, manifest, receipt or parsed observations are written to disk.
"""
import argparse
import faulthandler
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from .audit import audit_dataset
from .parser import DataError, INDUSTRIES, MAX_ARCHIVE, parse_archive
from .safeguards import SCOPE, SOURCE_URL, utc

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'patelkavitarepo/Data-analytics-portfolio'
ALLOWED_REF = 'refs/heads/project-006-french-industry-ingestion'
OWNER = 'patelkavitarepo'
CONTEXT_KEYS = (
    'GITHUB_ACTIONS', 'GITHUB_EVENT_NAME', 'GITHUB_REPOSITORY', 'GITHUB_REF',
    'GITHUB_ACTOR', 'GITHUB_TRIGGERING_ACTOR', 'GITHUB_RUN_ATTEMPT',
    'RUNNER_ENVIRONMENT', 'REVIEWED_CODE_SHA', 'AUDIT_CODE_SHA_INPUT',
    'PERMISSION_ACTIVE_ACK', 'EPHEMERAL_PROCESSING_ACK',
    'HOSTED_PROCESSING_ENABLED', 'HEAD_ONLY_ACK',
    'ACTIONS_STEP_DEBUG', 'ACTIONS_RUNNER_DEBUG', 'RUNNER_DEBUG',
)


def _verify_running_revision(context):
    """Check immutable checkout and no tracked code/policy edits before access."""
    try:
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, check=True).stdout.strip()
        clean = subprocess.run(['git', '-C', str(ROOT), 'diff', '--quiet', 'HEAD', '--',
                                'industry_companion', 'github_actions_scope.json',
                                'requirements-lock.txt'], capture_output=True, check=False)
    except (OSError, subprocess.SubprocessError):
        raise DataError('CODE_REVISION_UNVERIFIED') from None
    if head != context.get('REVIEWED_CODE_SHA') or clean.returncode != 0:
        raise DataError('CODE_REVISION_UNVERIFIED')


def validate_dispatch_context(context):
    """Common manual execution gate, independent of raw-data permissions."""
    required = dict(GITHUB_ACTIONS='true', GITHUB_EVENT_NAME='workflow_dispatch',
                    GITHUB_REPOSITORY=REPOSITORY, GITHUB_REF=ALLOWED_REF,
                    GITHUB_ACTOR=OWNER, GITHUB_TRIGGERING_ACTOR=OWNER,
                    GITHUB_RUN_ATTEMPT='1', RUNNER_ENVIRONMENT='github-hosted')
    if any(context.get(k) != value for k, value in required.items()):
        raise DataError('LIVE_DISPATCH_CONTEXT_NOT_AUTHORIZED')
    if any(str(context.get(k, '')).casefold() not in ('', 'false', '0')
           for k in ('ACTIONS_STEP_DEBUG', 'ACTIONS_RUNNER_DEBUG', 'RUNNER_DEBUG')):
        raise DataError('DEBUG_LOGGING_FORBIDDEN')
    if faulthandler.is_enabled():
        raise DataError('DEBUG_LOGGING_FORBIDDEN')
    sha = context.get('REVIEWED_CODE_SHA', '')
    if not re.fullmatch(r'[0-9a-f]{40}', sha) or sha == '0' * 40 or context.get('AUDIT_CODE_SHA_INPUT') != sha:
        raise DataError('REVIEWED_CODE_ACKNOWLEDGEMENT_REQUIRED')
    _verify_running_revision(context)


def validate_live_context(context, policy):
    """Owner checkboxes never substitute for separately reviewed hosted scope."""
    if not isinstance(policy, dict) or not (
        type(policy.get('schema_version')) is int and policy['schema_version'] == 1
        and policy.get('dataset_scope') == SCOPE and policy.get('source_url') == SOURCE_URL
        and policy.get('status') == 'approved_github_hosted_ephemeral_processing'
        and policy.get('live_enabled') is True
        and policy.get('github_hosted_ephemeral_processing') is True
        and policy.get('raw_redistribution') is False
        and policy.get('rescission_possible') is True
        and isinstance(policy.get('evidence_reference'), str)
        and re.fullmatch(r'https://github\.com/patelkavitarepo/Data-analytics-portfolio/(?:issues|pull)/\d+#issuecomment-\d+', policy['evidence_reference'])
    ):
        raise DataError('HOSTED_PROCESSING_SCOPE_NOT_CLEARED')
    required = ('PERMISSION_ACTIVE_ACK', 'EPHEMERAL_PROCESSING_ACK', 'HOSTED_PROCESSING_ENABLED')
    if any(context.get(key) != 'true' for key in required):
        raise DataError('LIVE_DISPATCH_CONTEXT_NOT_AUTHORIZED')
    validate_dispatch_context(context)


def execute_head(context):
    """Explicit manual HEAD only; never invoke the raw acquisition/parse path."""
    if context.get('HEAD_ONLY_ACK') != 'true':
        raise DataError('EXPLICIT_HEAD_ONLY_ACKNOWLEDGEMENT_REQUIRED')
    validate_dispatch_context(context)
    from .head_preflight import check_connectivity
    return check_connectivity()


class EphemeralStore:
    """Memory-only acquisition adapter; never a retained private snapshot.

    References are released on close; this is not certified memory/VM erasure.
    The owner must separately review GitHub/cloud processing and platform terms.
    """
    def __init__(self, context, policy):
        self.context = context
        self.policy = policy
        self._data = None
        self._manifest = None
        self._closed = False

    def __repr__(self):
        return 'EphemeralIndustryBuffer(values=redacted, durable_snapshot=False)'

    def gate(self, *, permission_active=False):
        if permission_active is not True or self._closed:
            raise DataError('EPHEMERAL_ACCESS_NOT_AUTHORIZED')
        validate_live_context(self.context, self.policy)

    def snapshot(self, data, *, retrieved_at_utc, permission_active=False,
                 acquisition_method='bounded_direct_https'):
        self.gate(permission_active=permission_active)
        utc(retrieved_at_utc)
        if self._data is not None:
            raise DataError('EPHEMERAL_BUFFER_ALREADY_USED')
        if acquisition_method != 'bounded_direct_https' or not isinstance(data, bytes) or len(data) > MAX_ARCHIVE:
            raise DataError('EPHEMERAL_SOURCE_INVALID')
        digest = hashlib.sha256(data).hexdigest()
        self._data = data
        self._manifest = dict(source_url=SOURCE_URL, archive_sha256=digest,
                              retrieved_at_utc=retrieved_at_utc, acquisition_method=acquisition_method,
                              historical_release_availability_verified=False,
                              performance_cleared=False, raw_redistribution=False,
                              durable_snapshot_retained=False)
        return digest

    def load_snapshot(self, digest, *, permission_active=False):
        self.gate(permission_active=permission_active)
        if self._data is None or digest != hashlib.sha256(self._data).hexdigest():
            raise DataError('EPHEMERAL_FINGERPRINT_MISMATCH')
        return self._data, dict(self._manifest)

    def close(self):
        self._data = None
        self._manifest = None
        self._closed = True


def _execution_metadata(report, *, synthetic, code_sha=None):
    # All numerical content comes from the existing coverage-only audit schema.
    # No generic data frame serialization or arbitrary provider text is allowed.
    allowed = {'checkpoint', 'source', 'source_url', 'retrieved_at_utc', 'acquisition_method',
               'archive_sha256', 'member_sha256', 'publisher_crsp_vintage',
               'provenance_manifest_sha256', 'parser_sha256', 'versions',
               'panel_date_alignment_mismatches', 'scope', 'calendar_basis',
               'out_of_scope_rows_excluded', 'panels', 'coverage_complete',
               'point_in_time_verified', 'performance_cleared', 'raw_observations_in_output', 'limitations'}
    panel_fields = {'development_rows', 'industry_count', 'first_development_date',
                    'last_development_date', 'expected_sessions', 'missing_sessions',
                    'non_session_dates', 'duplicate_dates', 'missing_sentinels',
                    'nonfinite_values', 'impossible_simple_returns', 'valid_return_cells', 'strict_parse_passed'}
    if (set(report) != allowed or set(report['panels']) != {'value_weighted', 'equal_weighted'}
            or any(set(p) != panel_fields for p in report['panels'].values())
            or set(report['versions']) != {'python', 'exchange_calendars', 'pandas', 'numpy'}
            or set(report['scope']) != {'start', 'end', 'primary', 'equal_weighted'}
            or report['point_in_time_verified'] is not False
            or report['performance_cleared'] is not False
            or report['raw_observations_in_output'] is not False):
        raise DataError('UNSAFE_AUDIT_OUTPUT')
    report['evidence_kind'] = 'synthetic_format_fixture' if synthetic else 'authorized_live_coverage_audit'
    report['execution'] = dict(storage='process_memory_only', durable_snapshot_retained=False,
                               certified_erasure=False, reviewed_code_sha=code_sha)
    return report


def execute_live(context, policy):
    validate_live_context(context, policy)
    from .acquire import acquire_private  # This is the only possible network path.
    store = EphemeralStore(context, policy)
    try:
        digest = acquire_private(store, permission_active=True)
        data, manifest = store.load_snapshot(digest, permission_active=True)
        report = audit_dataset(parse_archive(data), manifest)
        store.gate(permission_active=True)  # Recheck before publication as well.
        return _execution_metadata(report, synthetic=False, code_sha=context['REVIEWED_CODE_SHA'])
    finally:
        store.close()


def _synthetic_archive():
    """Invented deterministic format bytes; no market observations or experiment."""
    header = ',' + ','.join(INDUSTRIES)
    outside = '20250101,returns in decimals,PRIVATEPOISON,NaN'
    lines = ['SYNTHETIC FORMAT FIXTURE: NOT MARKET EVIDENCE', 'Returns are in percent.']
    for weighting, invented in (('Value', '1.25'), ('Equal', '-2.5')):
        lines += [f'Average {weighting} Weighted Returns -- Daily', header,
                  '20160104,' + ','.join([invented] * 10),
                  '20241231,' + ','.join(['0.5'] * 10), outside, '']
    stream = io.BytesIO()
    entry = zipfile.ZipInfo('10_Industry_Portfolios_Daily.csv', date_time=(1980, 1, 1, 0, 0, 0))
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(entry, '\n'.join(lines))
    return stream.getvalue()


def execute_synthetic():
    dataset = parse_archive(_synthetic_archive())
    manifest = dict(source_url='not applicable: invented synthetic format fixture',
                    retrieved_at_utc='2000-01-01T00:00:00+00:00',
                    acquisition_method='synthetic_fixture')
    report = audit_dataset(dataset, manifest)
    report['source'] = 'Invented format fixture; not French market observations'
    return _execution_metadata(report, synthetic=True)


class _SafeArguments(argparse.ArgumentParser):
    def error(self, message):
        raise DataError('INVALID_AUDIT_ARGUMENTS')


def main(argv=None):
    try:
        parser = _SafeArguments(description=__doc__)
        parser.add_argument('--mode', choices=('synthetic', 'head', 'live'), default='synthetic')
        args = parser.parse_args(argv)
        if args.mode == 'synthetic':
            report = execute_synthetic()
        else:
            context = {key: os.environ.get(key, '') for key in CONTEXT_KEYS}
            if args.mode == 'head':
                report = execute_head(context)
            else:
                policy = json.loads((ROOT / 'github_actions_scope.json').read_text())
                report = execute_live(context, policy)
        print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        code = error.code if isinstance(error, DataError) else 'HOSTED_AUDIT_INTERNAL_ERROR'
        if not re.fullmatch(r'[A-Z][A-Z0-9_]{1,79}', code):
            code = 'HOSTED_AUDIT_INTERNAL_ERROR'
        print(json.dumps(dict(status='blocked', code=code, point_in_time_verified=False,
                              performance_cleared=False, raw_observations_in_output=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

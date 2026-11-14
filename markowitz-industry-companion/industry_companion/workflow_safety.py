"""Fail-closed offline review contract for the proposed manual dispatcher."""
import re

from .parser import DataError

CHECKOUT = 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683'
SETUP_PYTHON = 'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065'
MANUAL_IF = ("${{ github.event_name == 'workflow_dispatch' && "
             "github.repository == 'patelkavitarepo/Data-analytics-portfolio' && "
             "github.ref == 'refs/heads/project-006-french-industry-ingestion' && "
             "github.actor == 'patelkavitarepo' && github.triggering_actor == 'patelkavitarepo' && "
             "github.run_attempt == 1 }}")
RUNS = (
    'python -m pip install --disable-pip-version-check --no-cache-dir -r requirements-lock.txt',
    'python -m pytest -q',
    'python scripts/check_safety.py',
    'python scripts/check_workflow.py',
    'ulimit -c 0\npython -m industry_companion.actions_audit --mode "$AUDIT_MODE"\n',
)


def validate_manual_workflow(doc):
    """Reject changes that add triggers, mutable code, disclosure or extra steps.

    This contract is defense in depth for review, not protection against an owner
    intentionally editing both code and guard. Permission review is separate.
    """
    def require(condition):
        if not condition:
            raise DataError('UNSAFE_MANUAL_WORKFLOW')

    try:
        require(set(doc) == {'name', 'on', 'permissions', 'concurrency', 'jobs'})
        require(set(doc['on']) == {'workflow_dispatch'})
        inputs = doc['on']['workflow_dispatch']['inputs']
        require(set(inputs) == {'mode', 'head_only_ack', 'permission_active', 'ephemeral_processing_ack', 'reviewed_code_sha'})
        require(inputs['mode']['type'] == 'choice' and inputs['mode']['default'] == 'synthetic')
        require(inputs['mode']['options'] == ['synthetic', 'head', 'live'])
        require(all(inputs[k]['type'] == 'boolean' and inputs[k]['default'] is False
                   for k in ('head_only_ack', 'permission_active', 'ephemeral_processing_ack')))
        require(inputs['reviewed_code_sha']['type'] == 'string' and inputs['reviewed_code_sha']['default'] == '')
        require(doc['permissions'] == {'contents': 'read'})
        require(doc['concurrency'] == {'group': 'industry-companion-owner-audit', 'cancel-in-progress': False})
        require(set(doc['jobs']) == {'audit'})
        job = doc['jobs']['audit']
        require(set(job) == {'if', 'runs-on', 'timeout-minutes', 'defaults', 'env', 'steps'})
        require(job['if'] == MANUAL_IF and job['runs-on'] == 'ubuntu-24.04')
        require(job['timeout-minutes'] == 10)
        require(job['defaults'] == {'run': {'working-directory': 'markowitz-industry-companion', 'shell': 'bash --noprofile --norc -e -o pipefail {0}'}})
        env = dict(job['env'])
        sha = env.pop('REVIEWED_CODE_SHA')
        require(isinstance(sha, str) and re.fullmatch(r'[0-9a-f]{40}', sha) and sha != '0' * 40)
        require(env == {'AUDIT_MODE': '${{ inputs.mode }}',
                       'AUDIT_CODE_SHA_INPUT': '${{ inputs.reviewed_code_sha }}',
                       'HEAD_ONLY_ACK': '${{ inputs.head_only_ack }}',
                       'PERMISSION_ACTIVE_ACK': '${{ inputs.permission_active }}',
                       'EPHEMERAL_PROCESSING_ACK': '${{ inputs.ephemeral_processing_ack }}',
                       'HOSTED_PROCESSING_ENABLED': '${{ vars.FRENCH_INDUSTRY_EPHEMERAL_ENABLED }}',
                       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONFAULTHANDLER': ''})
        steps = job['steps']
        require(len(steps) == 2 + len(RUNS))
        require(steps[0] == {'uses': CHECKOUT, 'with': {
            'repository': 'patelkavitarepo/Data-analytics-portfolio',
            'ref': '${{ env.REVIEWED_CODE_SHA }}', 'persist-credentials': False,
            'fetch-depth': 1, 'submodules': False, 'lfs': False}})
        require(steps[1] == {'uses': SETUP_PYTHON, 'with': {'python-version': '3.12'}})
        require(steps[2:] == [{'run': run} for run in RUNS])
    except (AssertionError, KeyError, TypeError, AttributeError):
        raise DataError('UNSAFE_MANUAL_WORKFLOW') from None

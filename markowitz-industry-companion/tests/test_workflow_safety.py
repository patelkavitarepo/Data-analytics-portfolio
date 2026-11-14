"""Mutation tests of the manual workflow, never a live workflow dispatch."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys

import pytest
import yaml

from industry_companion.parser import DataError
from industry_companion.workflow_safety import validate_manual_workflow


def workflow():
    path=Path(__file__).resolve().parents[2]/'.github/workflows/industry-companion-audit.yml'
    return yaml.safe_load(path.read_text())


def test_manual_dispatch_is_synthetic_default_and_pinned():
    validate_manual_workflow(workflow())


@pytest.mark.parametrize('mutation', ['automatic_trigger','write_token','extra_job','extra_step','cache','moving_action','moving_code','debug','shell_input','reruns','runner','persistent_credentials','untrusted_repo','head_default','head_ack_default','automatic_head_step','get_method','method_input'])
def test_fail_closed_workflow_mutations(mutation):
    doc=deepcopy(workflow());job=doc['jobs']['audit']
    if mutation=='automatic_trigger':doc['on']['push']={}
    elif mutation=='write_token':doc['permissions']['contents']='write'
    elif mutation=='extra_job':doc['jobs']['callback']={'runs-on':'ubuntu-latest','steps':[{'run':'echo upload'}]}
    elif mutation=='extra_step':job['steps'].append({'run':'env'})
    elif mutation=='cache':job['steps'][1]['with']['cache']='pip'
    elif mutation=='moving_action':job['steps'][0]['uses']='actions/checkout@v4'
    elif mutation=='moving_code':job['env']['REVIEWED_CODE_SHA']='main'
    elif mutation=='debug':job['env']['ACTIONS_STEP_DEBUG']='true'
    elif mutation=='shell_input':job['steps'][-1]['run']='python -m industry_companion.actions_audit --mode ${{ inputs.mode }}'
    elif mutation=='reruns':job['if']=job['if'].replace("github.run_attempt == 1",'true')
    elif mutation=='runner':job['runs-on']='self-hosted'
    elif mutation=='persistent_credentials':job['steps'][0]['with']['persist-credentials']=True
    elif mutation=='untrusted_repo':job['steps'][0]['with']['repository']='someone/other-repo'
    elif mutation=='head_default':doc['on']['workflow_dispatch']['inputs']['mode']['default']='head'
    elif mutation=='head_ack_default':doc['on']['workflow_dispatch']['inputs']['head_only_ack']['default']=True
    elif mutation=='automatic_head_step':job['steps'].insert(3,{'run':'python -m industry_companion.actions_audit --mode head'})
    elif mutation=='get_method':job['steps'][-1]['run']='curl --request GET https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/10_Industry_Portfolios_daily_CSV.zip'
    elif mutation=='method_input':doc['on']['workflow_dispatch']['inputs']['method']={'type':'string','default':'GET'}
    with pytest.raises(DataError,match='UNSAFE_MANUAL_WORKFLOW'):
        validate_manual_workflow(doc)


def test_optimized_python_does_not_disable_safety_contract():
    doc=workflow();doc['permissions']['contents']='write'
    code="""
import json, sys
from industry_companion.workflow_safety import validate_manual_workflow
from industry_companion.parser import DataError
try:
    validate_manual_workflow(json.load(sys.stdin))
except DataError as error:
    print(error.code)
    raise SystemExit(1)
"""
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([sys.executable,'-O','-c',code],input=json.dumps(doc),
                          cwd=root,text=True,capture_output=True,check=False)
    assert result.returncode==1 and result.stdout.strip()=='UNSAFE_MANUAL_WORKFLOW'
    assert result.stderr==''

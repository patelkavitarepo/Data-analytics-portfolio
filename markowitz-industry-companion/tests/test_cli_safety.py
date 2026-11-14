"""CLI and tracked-data controls exercised using synthetic local files only."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from industry_companion import __main__ as cli
from industry_companion.safeguards import PrivateStore
from test_parser import text,zipped


def test_cli_local_registration_and_safe_audit(tmp_path,monkeypatch,capsys):
    import subprocess
    project=tmp_path/'project';project.mkdir()
    subprocess.run(['git','init','-q',str(project)],check=True,capture_output=True)
    (project/'.gitignore').write_text('private/\n')
    store=PrivateStore(project)
    monkeypatch.setattr(cli,'PrivateStore',lambda:store)
    def run(args):
        monkeypatch.setattr(sys,'argv',['industry_companion',*args])
        code=cli.main();return code,capsys.readouterr().out
    assert run(['record-permission','--permission-active'])[0]==0
    store.write('manual-download.zip',zipped(text()))
    code,out=run(['register-local','--local-name','manual-download.zip','--retrieved-at-utc','2026-11-14T00:00:00Z','--permission-active'])
    assert code==0;digest=json.loads(out)['snapshot_id']
    monkeypatch.setattr(cli,'audit_dataset',lambda dataset,metadata:dict(raw_observations_in_output=False,performance_cleared=False,coverage='SYNTHETIC test only'))
    code,out=run(['audit','--snapshot-id',digest,'--permission-active'])
    assert code==0 and json.loads(out)['raw_observations_in_output'] is False
    assert '0.0125' not in out and '-0.025' not in out
    code,out=run(['suspend']);assert code==0
    code,out=run(['audit','--snapshot-id',digest,'--permission-active'])
    assert code==1 and json.loads(out)['code']=='PERMISSION_SUSPENDED'


def test_cli_never_echoes_underlying_errors(monkeypatch,capsys):
    class Bad:
        def gate(self,**kwargs):raise RuntimeError('PRIVATEPOISON /private/email sender@example.invalid 20160104,raw')
    monkeypatch.setattr(cli,'PrivateStore',Bad)
    monkeypatch.setattr(sys,'argv',['industry_companion','register-local','--local-name','fixture.zip','--permission-active'])
    assert cli.main()==1
    out=capsys.readouterr().out
    assert json.loads(out)['code']=='CHECKPOINT_INTERNAL_ERROR'
    assert all(token not in out for token in ('PRIVATEPOISON','sender@','20160104','/private/'))


def test_production_ignore_and_non_network_ci_contract():
    import subprocess
    root=Path(__file__).resolve().parents[1]
    prospective=root/'private'/'untracked-fixture.zip'
    assert subprocess.run(['git','-C',str(root),'check-ignore','-q','--',str(prospective)],capture_output=True).returncode==0
    workflow=(root.parent/'.github/workflows/industry-companion-tests.yml').read_text()
    assert 'python -m pytest -q' in workflow and 'python scripts/check_safety.py' in workflow
    assert 'industry_companion acquire' not in workflow and 'upload-artifact' not in workflow and 'secrets.' not in workflow

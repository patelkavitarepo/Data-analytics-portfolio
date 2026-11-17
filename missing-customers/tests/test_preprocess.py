"""Synthetic-only offline preprocessing tests."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_cli_slice_and_refuse_overwrite(tmp_path):
    source = tmp_path/'synthetic.csv'
    target = tmp_path/'slice.csv'
    source.write_text('timestamp,visitorid,event,itemid\n1430000000000,test,view,x\n1431000000000,test,transaction,x\n')
    command = [sys.executable,'-m','src.preprocess',str(source),str(target),'--start','2015-04-25','--end','2015-04-26']
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert '1430000000000' in target.read_text()
    assert '1431000000000' not in target.read_text()
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    assert result.returncode != 0

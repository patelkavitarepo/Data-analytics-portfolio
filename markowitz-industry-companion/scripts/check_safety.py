"""Offline tracked-file/source guard. Does not import data or acquisition code."""
import ast
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def audit():
    result=subprocess.run(['git','-C',str(ROOT),'ls-files','--full-name','-z','--','.'],capture_output=True,check=True)
    repo=Path(subprocess.run(['git','-C',str(ROOT),'rev-parse','--show-toplevel'],capture_output=True,text=True,check=True).stdout.strip())
    files=[repo/path.decode() for path in result.stdout.split(b'\0') if path]
    forbidden={'.zip','.csv','.parquet','.feather','.pkl','.pickle','.eml','.msg','.xlsx'}
    for path in files:
        rel=path.relative_to(ROOT)
        if 'private' in rel.parts or 'work' in rel.parts or path.suffix.casefold() in forbidden:raise ValueError('TRACKED_PRIVATE_OR_DATA_FILE')
        raw=path.read_bytes()
        if raw.startswith(b'PK\x03\x04'):raise ValueError('TRACKED_ARCHIVE_CONTENT')
        # No actual daily return panel may hide under another extension.
        if re.search(rb'^\s*\d{8},(?:[^\n,]*,){8,}[^\n]*$',raw,re.MULTILINE):raise ValueError('TRACKED_RETURN_ROWS')
    for name in ('parser.py','audit.py','safeguards.py','__init__.py'):
        tree=ast.parse((ROOT/'industry_companion'/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
                if any(m.split('.')[0] in {'requests','urllib','http','yfinance','socket'} for m in modules):raise ValueError('NETWORK_IMPORT_IN_LOCAL_MODULE')
    print(f'PASS: {len(files)} tracked companion files; no private/raw files or network imports in local modules. Automatic CI is synthetic-only; manual live scope is separately gated.')


if __name__=='__main__':
    try:audit()
    except Exception as exc:
        print(str(exc) if isinstance(exc,ValueError) and str(exc).isupper() else 'SAFETY_CHECK_FAILED')
        raise SystemExit(1)

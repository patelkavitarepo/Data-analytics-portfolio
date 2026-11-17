"""Read-only offline source/evidence audit for the standalone synthetic exhibit."""
import ast
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from showcase_evidence import REPOSITORY, ROOT as EVIDENCE_ROOT, SPECS, WARNING, build_panels, load_reports

ALLOWED_IMPORTS={
    'synthetic_showcase.py':{'streamlit','plotly.express','showcase_evidence'},
    'showcase_evidence.py':{'hashlib','json','math','pathlib'},
}
FORBIDDEN_CALLS={'eval','exec','compile','__import__','open','read_csv','read_parquet','write_text','write_bytes',
    'file_uploader','text_input','number_input','slider','form','form_submit_button','page_link','switch_page',
    'read_sql','connect','urlopen','request','getenv','system','popen','run_grid','fit','simulate','optimize'}


def audit_sources(root=ROOT):
    """Allowlisted imports + banned active I/O/model routes; not a security sandbox."""
    checked=0
    for filename,allowed in ALLOWED_IMPORTS.items():
        tree=ast.parse((root/filename).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for name in node.names:
                    if name.name not in allowed:raise ValueError('Forbidden import: '+name.name)
            elif isinstance(node,ast.ImportFrom):
                if node.module not in allowed:raise ValueError('Forbidden import: '+str(node.module))
            elif isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else None
                if name in FORBIDDEN_CALLS:raise ValueError('Forbidden active call: '+name)
        checked+=1
    ui=ast.parse((root/'synthetic_showcase.py').read_text())
    pages=[n for n in ast.walk(ui) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Page']
    if len(pages)!=1 or not pages[0].args or not isinstance(pages[0].args[0],ast.Name) or pages[0].args[0].id!='render_showcase':
        raise ValueError('Navigation must include only the standalone callable, never sibling apps')
    return checked


def main():
    count=audit_sources()
    reports,raw=load_reports(with_bytes=True)
    panels=build_panels(reports)
    if list(panels)!=list(SPECS):raise ValueError('All five investigations must be present')
    rows=0
    for key,panel in panels.items():
        if not all(panel.get(field) for field in ('title','context','finding','blocks','limits','sources')):raise ValueError('Incomplete panel: '+key)
        if not (ROOT/SPECS[key]['findings']).is_file():raise ValueError('Missing findings link')
        for item in panel['blocks']:
            if not all(item.get(field) for field in ('title','unit','rows','note')):raise ValueError('Unlabelled/empty comparison')
            for row in item['rows']:
                if not row['label'] or not row['value']:raise ValueError('Missing observed display value')
                rows+=1
    for filename in ('CASE_STUDY.md','DECISION_QUALITY_FRAMEWORK.md','DATA_RIGHTS.md','ADJUSTMENT_REVIEW.md'):
        if not (ROOT/filename).is_file():raise ValueError('Broken documentation link: '+filename)
    print(f'PASS: {count} allowlisted source files; {len(reports)} pinned/labeled JSON reports; {len(panels)} panels; {rows} sourced display rows; 9 documentation links. No model execution or network access.')
    print(WARNING)


if __name__=='__main__':
    main()

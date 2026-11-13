"""Local browser audit of the read-only showcase; block all non-local requests."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright
from showcase_evidence import SPECS, WARNING

base=os.environ.get('SYNTHETIC_SHOWCASE_URL','http://127.0.0.1:8506').rstrip('/')
origin=urlparse(base).netloc
out=Path(__file__).resolve().parents[1]/'work'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.set_default_timeout(30000)
    errors=[];external=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def local_only(route):
        if urlparse(route.request.url).netloc==origin:route.continue_()
        else:
            external.append(route.request.url.split('?')[0]);route.abort()
    page.route('**/*',local_only)
    page.goto(base)
    page.get_by_role('heading',name='What makes a portfolio decision trustworthy?').wait_for()
    page.get_by_role('heading',name='What passed / what remains blocked').wait_for()
    assert page.get_by_text('The eight-ETF historical question is unanswered.',exact=False).count()>0
    assert page.get_by_text('2025+ real holdout is untouched',exact=False).count()>0
    for forbidden in ('Run synthetic experiment','Reveal final holdout (2025 onward)','Synthetic scenario lab','Synthetic robustness check'):
        assert page.get_by_text(forbidden,exact=True).count()==0
    page.screenshot(path=str(out/'showcase_overview_desktop.png'),full_page=True)
    for key,spec in SPECS.items():
        page.get_by_test_id('stSidebar').get_by_text(spec['title'],exact=True).click()
        page.get_by_role('heading',name=spec['title'],exact=True).wait_for()
        page.get_by_text('Limits ·',exact=False).wait_for()
        assert page.get_by_text(WARNING,exact=False).count()>=4
        button=page.get_by_role('button',name=WARNING+' · Download original '+spec['title'],exact=True)
        if not button.is_visible():page.get_by_text('Exact source selectors and unchanged report',exact=True).click()
        button.wait_for(state='visible')
        with page.expect_download() as info:button.click()
        download=info.value
        raw=Path(download.path()).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==spec['sha256']
        if not page.get_by_role('link',name='Project case study — CASE_STUDY.md').is_visible():
            page.get_by_text('Read the original evidence and research gates',exact=True).click()
        assert page.get_by_role('link',name='Project case study — CASE_STUDY.md').count()==1
        assert page.get_by_role('link',name='Decision Quality Framework — DECISION_QUALITY_FRAMEWORK.md').count()==1
        assert page.get_by_role('link',name=spec['title']+' — '+spec['findings']).count()==1
        print('Verified panel and original download:',key,flush=True)
    page.screenshot(path=str(out/'showcase_mechanism_desktop.png'),full_page=True)
    mobile=browser.new_page(viewport={'width':390,'height':844})
    mobile.on('pageerror',lambda e:errors.append(str(e)))
    mobile.route('**/*',local_only)
    mobile.goto(base)
    mobile.get_by_role('heading',name='Five investigations, including negative findings').wait_for()
    mobile.screenshot(path=str(out/'showcase_overview_mobile.png'),full_page=True)
    mobile.get_by_role('button',name='Open Shrinkage mechanism',exact=True).click()
    mobile.get_by_role('heading',name='Shrinkage mechanism',exact=True).wait_for()
    mobile.get_by_text('Exact source selectors and unchanged report',exact=True).click()
    mobile.get_by_role('button',name=WARNING+' · Download original Shrinkage mechanism',exact=True).wait_for(state='visible')
    assert mobile.evaluate('document.documentElement.scrollWidth')<=390
    mobile.get_by_role('heading',name='Counterexample: seed 7102 · rho=.35 · 504 rows',exact=True).scroll_into_view_if_needed()
    mobile.screenshot(path=str(out/'showcase_mobile.png'),full_page=True)
    assert not errors and not external
    print(json.dumps(dict(page_errors=errors,external_requests=external,download_hashes_verified=len(SPECS),
        panels_visited=len(SPECS),mobile_document_width=mobile.evaluate('document.documentElement.scrollWidth'))))
    browser.close()

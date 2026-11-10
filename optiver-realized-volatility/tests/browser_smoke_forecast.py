"""Explicit Chromium integration check; requires a separately running dashboard.

Synthetic unit tests are separate. This loads the actual 2015 research bundle.
"""
import os
import csv
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
root=Path(os.environ.get('SCREENSHOT_DIR','/tmp/forecast-browser'));root.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE'),headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(os.environ.get('APP_URL','http://127.0.0.1:8506'),wait_until='networkidle')
 page.get_by_text('87.74%',exact=True).wait_for(timeout=60000)
 assert page.get_by_test_id('stMetric').count()==3
 page.get_by_test_id('stPlotlyChart').first.wait_for(timeout=60000)
 page.wait_for_function("document.querySelectorAll('[data-testid=stSkeleton]').length === 0")
 page.screenshot(path=str(root/'desktop.png'),full_page=True)
 for tab in ['Metric disagreements','Failure lab','Coverage & methodology','Forecasts & performance']:
  page.get_by_role('tab',name=tab,exact=True).click()
  assert page.get_by_test_id('stException').count()==0
 page.get_by_text('Narrow',exact=True).click()
 page.get_by_text('56.77%',exact=True).wait_for(timeout=30000)
 page.get_by_text('MAE',exact=True).click()
 page.get_by_text('1.37 pp',exact=True).wait_for(timeout=30000)
 with page.expect_download() as event:
  page.get_by_role('button',name='Download displayed predictions (CSV)',exact=True).click()
 download=event.value;download.save_as(str(root/'download.csv'))
 assert Path(root/'download.csv').stat().st_size>1000
 page.get_by_test_id('stRadio').filter(has_text='Stock scope').get_by_text('Selected stocks',exact=True).click()
 page.get_by_text('1 stocks',exact=False).wait_for(timeout=30000)
 page.get_by_role('tab',name='Failure lab',exact=True).click()
 page.get_by_test_id('stSelectbox').filter(has_text='Forecast model').get_by_role('combobox').click()
 page.get_by_role('option',name='Historical volatility',exact=True).click()
 page.get_by_text('Percentage error',exact=True).click()
 # Streamlit can retain the prior chart briefly during a widget rerun.
 target_title=page.get_by_text('the five observed target returns',exact=False)
 expect(target_title).to_have_count(1,timeout=30000)
 target_title.wait_for(timeout=30000)
 page.screenshot(path=str(root/'failure-lab.png'),full_page=True)
 assert page.get_by_test_id('stException').count()==0
 page.get_by_role('tab',name='Coverage & methodology',exact=True).click()
 with page.expect_download() as event:
  page.get_by_role('button',name='Download full 2015 eligibility ledger (CSV)',exact=True).click()
 event.value.save_as(str(root/'full-eligibility.csv'))
 with (root/'full-eligibility.csv').open() as stream: ledger=list(csv.DictReader(stream))
 assert len(ledger)==127260 and len({r['stock'] for r in ledger})==505
 assert max(r['date'] for r in ledger).startswith('2015-12-31')
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
 mobile=context.new_page();mobile.on('pageerror',lambda e:errors.append(str(e)))
 mobile.goto(os.environ.get('APP_URL','http://127.0.0.1:8506'),wait_until='networkidle')
 mobile.get_by_text('87.74%',exact=True).wait_for(timeout=60000)
 mobile.get_by_test_id('stPlotlyChart').first.wait_for(timeout=60000)
 mobile.wait_for_function("document.querySelectorAll('[data-testid=stSkeleton]').length === 0")
 mobile.screenshot(path=str(root/'mobile.png'),full_page=True)
 assert mobile.get_by_test_id('stException').count()==0
 overflow=mobile.evaluate('document.documentElement.scrollWidth > window.innerWidth + 4')
 assert not overflow,'Horizontal page overflow'
 assert not errors,errors
 browser.close()
 print('Passed real Chromium: three cards, all tabs, policy switch, metric switch, stock filter, failure model/criterion, CSV download, 390px touch viewport, no app/JS errors.')

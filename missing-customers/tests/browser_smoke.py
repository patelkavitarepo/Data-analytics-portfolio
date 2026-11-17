"""Real Chromium smoke test. Uploaded records are SYNTHETIC test fixtures only.
Run with the app already listening on localhost:8501.
"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1280,'height':900})
    page.goto('http://127.0.0.1:8501')
    page.get_by_text('Awaiting evidence.', exact=False).wait_for()
    assert page.get_by_text('Human investigator interpretation: pending.', exact=False).is_visible()
    page.locator('input[type=file]').set_input_files({'name':'synthetic-test-only.csv','mimeType':'text/csv','buffer':b'timestamp,visitorid,event,itemid\n1430000000000,test,view,x\n1430000000001,test,addtocart,x\n1430000000002,test,transaction,x\n'})
    page.get_by_text('Accepted events: 3', exact=False).wait_for()
    page.get_by_role('tab',name='Evidence audit').click()
    with page.expect_download() as download:
        page.get_by_text('Download quality summary',exact=True).click()
    assert download.value.suggested_filename == 'quality-summary.json'
    page.get_by_role('tab',name='Shopping journey').click()
    page.get_by_text('Strict timestamp-ordered visitor journey',exact=True).wait_for()
    assert page.locator('[data-testid="stException"]').count() == 0
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_role('tab',name='Case overview',exact=True).click()
    assert page.locator('[data-testid="stException"]').count() == 0
    page.screenshot(path='work/mobile-smoke.png',full_page=True)
    page.locator('input[type=file]').set_input_files({'name':'invalid-test.csv','mimeType':'text/csv','buffer':b'wrong\nvalue\n'})
    page.get_by_text('Cannot load evidence: Missing required columns:',exact=False).wait_for()
    browser.close()
print('PASS: Chromium empty start, synthetic upload, quality download, journey tab, mobile viewport, invalid schema')

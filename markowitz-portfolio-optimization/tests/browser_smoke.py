import json
from pathlib import Path
from playwright.sync_api import sync_playwright

# Optional browser check against a running local app; no market data injected.
out = Path(__file__).resolve().parents[1] / 'work'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.set_default_timeout(20000)
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:8501')
    page.get_by_text('NO HISTORICAL DATA LOADED.', exact=False).wait_for()
    page.screenshot(path=str(out / 'desktop.png'), full_page=True)
    page.get_by_text('Upload adjusted-price CSV', exact=True).click()
    page.get_by_text('CSV source / adjustment method / retrieval date', exact=False).wait_for()
    page.screenshot(path=str(out / 'upload.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.reload()
    page.get_by_text('NO HISTORICAL DATA LOADED.', exact=False).wait_for()
    page.screenshot(path=str(out / 'mobile.png'), full_page=True)
    assert not errors
    assert page.evaluate('document.documentElement.scrollWidth') <= 390
    print(json.dumps({'page_errors': errors, 'title': page.title(), 'mobile_document_width': page.evaluate('document.documentElement.scrollWidth'), 'viewport_width':390}))
    browser.close()

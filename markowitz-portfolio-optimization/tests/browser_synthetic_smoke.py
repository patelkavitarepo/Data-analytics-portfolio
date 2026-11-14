"""Optional offline browser smoke against the running main app on port 8501."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

WARNING = 'SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
base_url = os.environ.get('SYNTHETIC_APP_URL', 'http://127.0.0.1:8501').rstrip('/')
out = Path(__file__).resolve().parents[1] / 'work'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.set_default_timeout(30000)
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    def local_only(route):
        if route.request.url.startswith(base_url + '/'):
            route.continue_()
        else:
            external.append(route.request.url.split('?')[0])
            route.abort()
    page.route('**/*', local_only)
    page.goto(base_url)
    page.get_by_text('Synthetic scenario lab — constructed data only', exact=True).click()
    page.get_by_text('No experiment run yet.', exact=False).wait_for()
    page.get_by_role('button', name='Run synthetic experiment', exact=True).click()
    page.get_by_text('Bootstrap summary', exact=False).wait_for()
    assert page.get_by_text(WARNING, exact=False).count() >= 15
    page.screenshot(path=str(out / 'synthetic_desktop.png'), full_page=True)
    assert page.get_by_text('Reveal final holdout (2025 onward)', exact=True).count() == 0
    page.set_viewport_size({'width': 390, 'height': 844})
    page.screenshot(path=str(out / 'synthetic_mobile.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth') <= 390
    assert not errors
    print(json.dumps({'page_errors': errors, 'external_requests_blocked': external,
        'mobile_document_width': page.evaluate('document.documentElement.scrollWidth'), 'warning_labels': page.get_by_text(WARNING, exact=False).count()}))
    browser.close()

"""Optional local browser smoke: read-only synthetic report, all external requests blocked."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

WARNING = 'SYNTHETIC DATA — NOT EMPIRICAL RESULTS'
base = os.environ.get('SYNTHETIC_APP_URL', 'http://127.0.0.1:8501').rstrip('/')
out = Path(__file__).resolve().parents[1] / 'work'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.set_default_timeout(30000)
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    def local_only(route):
        if route.request.url.startswith(base + '/'):
            route.continue_()
        else:
            external.append(route.request.url.split('?')[0])
            route.abort()
    page.route('**/*', local_only)
    page.goto(base)
    page.get_by_text('Synthetic robustness check', exact=True).click()
    page.get_by_role('heading', name='Focused synthetic robustness check', exact=True).wait_for()
    page.get_by_text('Finite-path direction counts', exact=False).wait_for()
    assert page.get_by_text(WARNING, exact=False).count() >= 15
    assert page.get_by_text('Reveal final holdout (2025 onward)', exact=True).count() == 0
    assert page.get_by_role('button', name='Run synthetic experiment', exact=True).count() == 0
    page.screenshot(path=str(out / 'robustness_desktop.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.get_by_text('Known future volatility inflation on unchanged targets', exact=False).first.scroll_into_view_if_needed()
    page.screenshot(path=str(out / 'robustness_mobile.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth') <= 390
    assert not errors and not external
    print(json.dumps({'page_errors': errors, 'external_requests': external,
                      'warning_labels': page.get_by_text(WARNING, exact=False).count(),
                      'mobile_document_width': page.evaluate('document.documentElement.scrollWidth')}))
    browser.close()

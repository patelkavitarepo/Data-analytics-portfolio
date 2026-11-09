"""Run against a separately started local Streamlit server."""
import os
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        executable = os.environ.get('CHROMIUM_EXECUTABLE')
        browser = p.chromium.launch(executable_path=executable, headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1080})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(os.environ.get('APP_URL', 'http://127.0.0.1:8501'), wait_until='networkidle')
        page.get_by_text('Growth of $100', exact=False).wait_for(timeout=30000)
        assert page.get_by_test_id('stMetric').count() == 4
        for tab, title in [('Risk & relationships', 'Daily return correlation'),
                           ('Price explorer', 'daily share volume')]:
            page.get_by_role('tab', name=tab).click()
            page.get_by_text(title, exact=False).wait_for()
        page.get_by_role('tab', name='Data & methodology').click()
        assert page.get_by_role('button', name='Download filtered observations (CSV)').is_visible()
        assert page.get_by_test_id('stException').count() == 0
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.get_by_role('heading', name='Stock Market Analytics Dashboard').is_visible()
        assert not errors, errors
        browser.close()
        print('Browser smoke passed: tabs, metrics, download, mobile viewport, no JavaScript errors.')


if __name__ == '__main__':
    main()

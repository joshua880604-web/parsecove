"""Discovery, keyboard navigation and responsive workspace regression checks."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3011').rstrip('/')
OUT = Path('/workspace/work/parsecove-ui-refresh-qa')
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE)
    expect(page.locator('.nav-group')).to_have_count(4)
    expect(page.locator('nav[aria-label="Tools"] a')).to_have_count(15)
    expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(15)
    page.locator('[data-category="2"]').click()
    expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(4)
    expect(page.locator('#filter-status')).to_have_text('4 tools found')
    page.locator('#tool-filter').fill('rem')
    expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(2)
    page.locator('[data-category="0"]').click()
    expect(page.locator('#filter-empty')).to_be_visible()
    page.locator('#tool-filter-clear').click()
    expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(5)
    expect(page.locator('#tool-filter')).to_be_focused()
    page.locator('[data-category="all"]').click()
    expect(page.locator('.tool-group-heading:visible')).to_have_count(4)
    page.keyboard.press('Control+k')
    expect(page.locator('#search-dialog')).to_be_visible()
    expect(page.locator('#global-search')).to_be_focused()
    page.locator('#global-search').fill('timestamp')
    expect(page.locator('#search-list a[href="/unix-timestamp-converter/"]')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.locator('#search-dialog')).not_to_be_visible()

    # Drawer removes the obscured page from keyboard navigation and restores focus.
    page.set_viewport_size({'width': 390, 'height': 844})
    expect(page.locator('#sidebar')).to_have_js_property('inert', True)
    page.locator('.mobile-menu').click()
    expect(page.locator('.mobile-menu')).to_have_attribute('aria-expanded', 'true')
    expect(page.locator('.sidebar-close')).to_be_focused()
    expect(page.locator('.app-shell')).to_have_js_property('inert', True)
    page.keyboard.press('Shift+Tab')
    expect(page.locator('.privacy-link')).to_be_focused()
    page.keyboard.press('Tab')
    expect(page.locator('.sidebar-close')).to_be_focused()
    page.screenshot(path=str(OUT/'after-mobile-navigation.png'))
    page.keyboard.press('Escape')
    expect(page.locator('.mobile-menu')).to_be_focused()
    expect(page.locator('.app-shell')).to_have_js_property('inert', False)
    page.locator('.mobile-menu').click()
    page.locator('.sidebar-overlay').click(position={'x': 365, 'y': 100})
    expect(page.locator('.mobile-menu')).to_have_attribute('aria-expanded', 'false')
    page.locator('.mobile-menu').click()
    page.set_viewport_size({'width': 1440, 'height': 1000})
    expect(page.locator('#sidebar')).to_have_js_property('inert', False)
    expect(page.locator('.app-shell')).to_have_js_property('inert', False)

    # Static links remain available when scripting is disabled.
    nojs = browser.new_context(java_script_enabled=False, viewport={'width': 1440, 'height': 1000})
    static = nojs.new_page()
    static.goto(BASE)
    expect(static.locator('.tools-grid a:visible')).to_have_count(15)
    nojs.close()

    samples = [('', 'home'), ('csv-to-json/', 'csv'), ('hex-to-rgba/', 'rgba'),
               ('unix-timestamp-converter/', 'timestamp'), ('guides/yaml-vs-json/', 'guide')]
    layouts = []
    for width in [320, 390, 768, 1024, 1440, 1920]:
        page.set_viewport_size({'width': width, 'height': 1000 if width > 800 else 844})
        for route, name in samples:
            page.goto(BASE+'/'+route)
            if name == 'csv':
                expect(page.locator('#data-output')).not_to_have_value('')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (route, width)
            header = page.locator('.topbar').bounding_box()
            page.evaluate('window.scrollTo(0,400)')
            assert abs(page.locator('.topbar').bounding_box()['y']) < 1, (route, width, 'sticky header')
            page.evaluate('window.scrollTo(0,0)')
            if width in [390, 1440]:
                suffix = '-mobile' if width == 390 else ''
                page.screenshot(path=str(OUT/f'after-{name}{suffix}.png'))
            layouts.append({'route': '/'+route, 'width': width, 'overflow': False, 'sticky_header': True})
    assert not errors, errors
    (OUT/'ui-checks.json').write_text(json.dumps({'errors': errors, 'layouts': layouts,
        'discovery': 'category and query combination, clear, no matches',
        'navigation': 'grouped links, modal search, drawer focus trap, Escape, backdrop, resize',
        'no_javascript': 'all 15 tool cards remain available'}, indent=2))
    browser.close()
print('UI checks passed: discovery, keyboard navigation, 30 responsive layouts, no JavaScript links.')

"""Browser regressions for the two CSS converter entry points."""
import csv
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000').rstrip('/')
OUT = Path('/workspace/work/parsecove-rem-qa')
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True,
                                  permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((BASE, 'blob:', 'data:')) else None)

    def output(value):
        expect(page.locator('#px-output')).to_have_value(value)

    def reference(value, result):
        cells = page.locator('#px-table td').all_text_contents()
        index = cells.index(value)
        assert cells[index + 1] == result, (value, cells[index + 1], result)

    def downloaded_rows(filename):
        with page.expect_download() as pending:
            page.locator('#px-download').click()
        assert pending.value.suggested_filename == filename
        path = OUT / filename
        pending.value.save_as(str(path))
        with path.open(newline='') as f:
            return list(csv.reader(f))

    assert page.goto(BASE + '/rem-to-px/').status == 200
    expect(page.locator('h1')).to_have_text('REM to PX converter')
    expect(page.locator('#px-modes [data-mode="rem"]')).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('#px-input-label')).to_have_text('REM values')
    output('24px')
    expect(page.locator('#px-equation')).to_have_text('1.5rem × 16 = 24px')
    reference('1.5rem', '24px')
    page.locator('[data-copy="px-output"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == '24px'
    page.screenshot(path=str(OUT / 'rem-desktop.png'), full_page=True)

    # The root belongs to the page being measured; it is never assumed to be 16px.
    for root, result in [('10', '15px'), ('20', '30px'), ('16', '24px')]:
        page.locator('#px-base').fill(root)
        output(result)
        reference('1.5rem', result)
        expect(page.locator('#px-table-base')).to_have_text(f'At a {root}px root size')

    page.locator('#px-input').fill('0.75, 0.875\n1.25; 1.5 0 -2')
    output('12px\n14px\n20px\n24px\n0px\n-32px')
    rows = downloaded_rows('parsecove-rem-to-px.csv')
    assert rows == [['input', 'input_unit', 'root_px', 'output', 'output_unit'],
                    ['0.75', 'rem', '16', '12', 'px'], ['0.875', 'rem', '16', '14', 'px'],
                    ['1.25', 'rem', '16', '20', 'px'], ['1.5', 'rem', '16', '24', 'px'],
                    ['0', 'rem', '16', '0', 'px'], ['-2', 'rem', '16', '-32', 'px']]

    page.locator('#px-input').fill('0.123456789')
    for precision, result in [('2', '1.98px'), ('0', '2px'), ('8', '1.97530862px'), ('4', '1.9753px')]:
        page.locator('#px-precision').select_option(precision)
        output(result)

    # Invalid values never leave an old copyable result or downloadable CSV behind.
    for invalid in ['1.5rem', 'hello', 'NaN', '1e3', '1000000001', ' '.join(['1'] * 1001)]:
        page.locator('#px-input').fill(invalid)
        expect(page.locator('#px-error')).to_be_visible()
        output('')
        expect(page.locator('#px-value')).to_be_empty()
        expect(page.locator('#px-download')).to_be_disabled()
        reference('1.5rem', '24px')
    page.locator('#px-input').fill(' '.join(['1'] * 1000))
    assert page.locator('#px-output').input_value().splitlines() == ['16px'] * 1000
    page.locator('#px-input').fill('1.5')
    for invalid in ['0', '-1', '', '10001']:
        page.locator('#px-base').fill(invalid)
        expect(page.locator('#px-error')).to_be_visible()
        output('')
        expect(page.locator('#px-table tr')).to_have_count(0)
        expect(page.locator('#px-download')).to_be_disabled()
    page.locator('#px-base').fill('20')
    output('30px')
    expect(page.locator('#px-error')).to_be_hidden()

    page.locator('#px-modes [data-mode="px"]').click()
    page.locator('#px-input').fill('14 80 150')
    output('0.7rem\n4rem\n7.5rem')
    # The REM reference table keeps its labelled direction even when the input mode changes.
    reference('1.5rem', '30px')
    rows = downloaded_rows('parsecove-px-to-rem.csv')
    assert rows[1:] == [['14', 'px', '20', '0.7', 'rem'], ['80', 'px', '20', '4', 'rem'],
                        ['150', 'px', '20', '7.5', 'rem']]
    for value, result in [('1', '20px'), ('1.5', '30px'), ('1.25', '25px'), ('0.75', '15px'), ('0.875', '17.5px')]:
        page.locator('#px-modes [data-mode="px"]').click()
        page.locator(f'[data-rem-quick="{value}"]').click()
        output(result)
        expect(page.locator('#px-input-label')).to_have_text('REM values')
    page.locator('#px-clear').click()
    output('')
    expect(page.locator('#px-error')).to_be_hidden()
    expect(page.locator('#px-download')).to_be_disabled()
    page.locator('#px-sample').click()
    output('5px\n10px\n15px\n20px\n30px\n40px\n60px\n80px')

    # Keep the original entry point's defaults, table orientation and controls intact.
    page.goto(BASE + '/px-to-rem/')
    output('1.5rem')
    reference('150px', '9.375rem')
    page.locator('#px-base').fill('20')
    page.locator('#px-modes [data-mode="rem"]').click()
    page.locator('#px-input').fill('1.5')
    output('30px')
    page.locator('[data-px-quick="80"]').click()
    output('4rem')
    reference('150px', '7.5rem')
    expect(page.locator('main a[href="/rem-to-px/"]')).to_have_count(2)

    # Both entry points are discoverable through the site directory and search.
    page.goto(BASE + '/')
    page.locator('#tool-filter').fill('rem')
    expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(2)
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('REM to PX')
    expect(page.locator('#search-list a:visible')).to_have_count(1)
    page.locator('#search-list a[href="/rem-to-px/"]').click()
    expect(page.locator('h1')).to_have_text('REM to PX converter')

    checks = 0
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for route in ['/px-to-rem/', '/rem-to-px/']:
            page.goto(BASE + route)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route)
            page.locator('#px-input').fill('0.75, 0.875, 1.25, 1.5')
            expect(page.locator('#px-download')).to_be_enabled()
            if route == '/rem-to-px/' and width == 390:
                page.screenshot(path=str(OUT / 'rem-mobile.png'), full_page=True)
            checks += 1
    page.set_viewport_size({'width': 390, 'height': 640})
    page.locator('.mobile-menu').click()
    page.locator('#sidebar a[href="/rem-to-px/"]').scroll_into_view_if_needed()
    expect(page.locator('#sidebar a[href="/rem-to-px/"]')).to_be_in_viewport()
    page.locator('.sidebar-bottom a').scroll_into_view_if_needed()
    expect(page.locator('.sidebar-bottom a')).to_be_in_viewport()

    # The content, selected direction and example table also exist before JavaScript runs.
    static = browser.new_context(java_script_enabled=False)
    static_page = static.new_page()
    static_page.goto(BASE + '/rem-to-px/')
    expect(static_page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://parsecove.com/rem-to-px/')
    assert 'REM to PX' in static_page.title()
    assert 'custom root font size' in static_page.locator('meta[name="description"]').get_attribute('content')
    expect(static_page.locator('#px-input')).to_have_value('1.5')
    expect(static_page.locator('#px-output')).to_have_value('24px')
    expect(static_page.locator('#px-modes [data-mode="rem"]')).to_have_attribute('aria-pressed', 'true')
    expect(static_page.locator('#px-table')).to_contain_text('0.875rem')
    expect(static_page.locator('#rem-examples')).to_contain_text('1.25 × 16 = 20px')
    expect(static_page.locator('#find-root-size pre code')).to_contain_text('getComputedStyle(document.documentElement).fontSize')
    structured = json.loads(static_page.locator('script[type="application/ld+json"]').text_content())
    structured = next(x for x in structured['@graph'] if x['@type'] == 'WebApplication')
    assert structured['@type'] == 'WebApplication'
    assert structured['url'] == 'https://parsecove.com/rem-to-px/'
    static.close()
    assert not errors, errors
    assert not external, external
    report = {'conversion_and_batch': 'passed', 'root_and_rounding': 'passed',
              'clipboard_and_csv': 'passed', 'validation_and_clear': 'passed',
              'both_entry_points': 'passed', 'static_content_and_metadata': 'passed',
              'responsive_checks': checks, 'page_errors': errors, 'external_requests': external}
    (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    browser.close()

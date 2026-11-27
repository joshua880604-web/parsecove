"""Timestamp-unit troubleshooting, published code and explicit-unit tool links."""
import json
import os
from pathlib import Path
import subprocess
import sys

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000').rstrip('/')
OUT = Path('/workspace/work/parsecove-timestamp-guide-qa')
OUT.mkdir(parents=True, exist_ok=True)
ROUTE = '/guides/unix-timestamp-seconds-vs-milliseconds/'
UTC = '2023-11-14T22:13:20.000Z'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, timezone_id='Asia/Shanghai',
                                  permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external, mutations = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((BASE, 'blob:', 'data:')) else None)
    page.on('request', lambda r: mutations.append(r.url) if r.method != 'GET' else None)

    assert page.goto(BASE + ROUTE).status == 200
    expect(page.locator('h1')).to_have_text('Unix timestamps: seconds vs milliseconds')
    expect(page.locator('#epoch-guide-seconds')).to_have_value(UTC)
    expect(page.locator('#epoch-guide-milliseconds')).to_have_value('1970-01-20T16:13:20.000Z')
    page.locator('[data-copy="epoch-guide-seconds"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == UTC
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(OUT / 'timestamp-guide-desktop.png'), full_page=True)
    page.locator('#compare-epoch-units').screenshot(path=str(OUT / 'comparison-desktop.png'), style='.skip:not(:focus){visibility:hidden}')

    cases = [
        ('1700000000', UTC, '1970-01-20T16:13:20.000Z'),
        ('1700000000000', '+055840-11-08T22:13:20.000Z', UTC),
        ('999', '1970-01-01T00:16:39.000Z', '1970-01-01T00:00:00.999Z'),
        ('-1', '1969-12-31T23:59:59.000Z', '1969-12-31T23:59:59.999Z'),
        ('0', '1970-01-01T00:00:00.000Z', '1970-01-01T00:00:00.000Z'),
        ('100000000000000', None, '5138-11-16T09:46:40.000Z'),
        ('8640000000000000', None, '+275760-09-13T00:00:00.000Z'),
        ('8640000000000001', None, None),
    ]
    for value, seconds, milliseconds in cases:
        page.locator('#epoch-guide-input').fill(value)
        for unit, expected in [('seconds', seconds), ('milliseconds', milliseconds)]:
            expect(page.locator('#epoch-guide-' + unit)).to_have_value(expected or '')
            if expected is None:
                expect(page.locator('#epoch-guide-' + unit + '-error')).to_be_visible()
                expect(page.locator(f'[data-copy="epoch-guide-{unit}"]')).to_be_disabled()
            else:
                expect(page.locator('#epoch-guide-' + unit + '-error')).to_be_hidden()
                expect(page.locator(f'[data-copy="epoch-guide-{unit}"]')).to_be_enabled()
        expect(page.locator('#epoch-guide-error')).to_be_hidden()
        assert page.url == BASE + ROUTE
    for key, value in [('seconds', '1700000000'), ('milliseconds', '1700000000000'),
                        ('early', '999'), ('negative', '-1')]:
        page.locator(f'[data-epoch-example="{key}"]').click()
        expect(page.locator('#epoch-guide-input')).to_have_value(value)
    page.locator('[data-copy="epoch-guide-milliseconds"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == '1969-12-31T23:59:59.999Z'

    for invalid in ['NaN', '1e3', '1.5', '+1', '--1', '<img src=x>']:
        page.locator('#epoch-guide-input').fill(invalid)
        expect(page.locator('#epoch-guide-error')).to_be_visible()
        for unit in ['seconds', 'milliseconds']:
            expect(page.locator('#epoch-guide-' + unit)).to_have_value('')
            expect(page.locator(f'[data-copy="epoch-guide-{unit}"]')).to_be_disabled()
            expect(page.locator('#epoch-guide-' + unit + '-error')).to_be_hidden()
    page.evaluate("document.querySelector('#epoch-guide-input').value = '1'.repeat(25)")
    page.locator('#epoch-guide-input').dispatch_event('input')
    expect(page.locator('#epoch-guide-error')).to_be_visible()
    page.locator('#epoch-guide-clear').click()
    expect(page.locator('#epoch-guide-error')).to_be_hidden()
    expect(page.locator('#epoch-guide-seconds')).to_have_value('')
    expect(page.locator('[data-copy="epoch-guide-seconds"]')).to_be_disabled()
    page.locator('#epoch-guide-reset').click()
    expect(page.locator('#epoch-guide-seconds')).to_have_value(UTC)

    # Run the exact printed snippets; fixed instants make all outputs reproducible.
    snippets = {}
    for selector, command, expected in [
        ('#epoch-js-example', ['node', '--input-type=module', '-e'],
         [UTC, UTC, '1970-01-20T16:13:20.000Z', '2023-11-14T22:13:20.123Z']),
        ('#epoch-python-example', [sys.executable, '-c'],
         ['2023-11-14T22:13:20.000+00:00', '2023-11-14T22:13:20.123+00:00',
          '1969-12-31T23:59:59.999+00:00']),
        ('#epoch-zone-example', ['node', '--input-type=module', '-e'], ['true', '1700000000000']),
    ]:
        code = page.locator(selector + ' pre code').inner_text()
        result = subprocess.run(command + [code], text=True, capture_output=True, check=True)
        assert result.stdout.splitlines() == expected, (selector, result.stdout)
        snippets[selector] = result.stdout.splitlines()
    (OUT / 'published-code-results.json').write_text(json.dumps(snippets, indent=2) + '\n')

    for unit, value in [('seconds', '1700000000'), ('milliseconds', '1700000000000')]:
        page.goto(BASE + ROUTE)
        page.locator(f'#compare-epoch-units a[href="/unix-timestamp-converter/?example={unit}"]').click()
        expect(page.locator('#timestamp-input')).to_have_value(value)
        expect(page.locator('#time-unit')).to_have_value(unit)
        expect(page.locator('#time-detected')).to_have_text(unit)
        expect(page.locator('#time-iso')).to_have_text(UTC)
    for value in ['unknown', '__proto__', 'https%3A%2F%2Fexample.invalid%2Ftime']:
        page.goto(BASE + '/unix-timestamp-converter/?example=' + value)
        expect(page.locator('#time-unit')).to_have_value('auto')
        expect(page.locator('#timestamp-input')).to_have_value('1700000000')
        expect(page.locator('#time-iso')).to_have_text(UTC)
    page.goto(BASE + '/unix-timestamp-converter/')
    expect(page.locator('.guide-teaser a')).to_have_attribute('href', ROUTE)
    page.goto(BASE + '/')
    expect(page.locator('.guides-preview .guide-card')).to_have_count(4)
    page.goto(BASE + '/guides/')
    expect(page.locator('.guide-card')).to_have_count(4)
    page.locator('.guide-card[href="' + ROUTE + '"]').click()
    expect(page.locator('#timestamp-faq details')).to_have_count(4)
    page.locator('#timestamp-faq summary').first.click()
    expect(page.locator('#timestamp-faq details').first).to_contain_text('digit count is only a clue')
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('seconds vs milliseconds')
    expect(page.locator('#search-list a:visible')).to_have_count(1)
    page.locator('#search-list a:visible').click()

    checks = 0
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for route in ['/guides/', ROUTE, '/unix-timestamp-converter/?example=milliseconds']:
            assert page.goto(BASE + route).status == 200
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route)
            expect(page.locator('h1')).to_have_count(1)
            expect(page.locator('[data-ad-slot]')).to_have_count(0)
            if route == ROUTE:
                page.locator('#epoch-guide-input').fill('100000000000000')
                expect(page.locator('#epoch-guide-seconds-error')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.locator('[data-epoch-example="early"]').click()
                if width == 390:
                    page.evaluate('window.scrollTo(0,0)')
                    page.screenshot(path=str(OUT / 'timestamp-guide-mobile.png'), full_page=True)
                    page.locator('#compare-epoch-units').screenshot(path=str(OUT / 'comparison-mobile.png'), style='.skip:not(:focus){visibility:hidden}')
            checks += 1

    static = browser.new_context(java_script_enabled=False)
    static_page = static.new_page()
    static_page.goto(BASE + ROUTE)
    expect(static_page.locator('h1')).to_have_text('Unix timestamps: seconds vs milliseconds')
    expect(static_page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://parsecove.com' + ROUTE)
    expect(static_page.locator('meta[property="og:type"]')).to_have_attribute('content', 'article')
    expect(static_page.locator('#epoch-guide-seconds')).to_have_value(UTC)
    expect(static_page.locator('#epoch-guide-milliseconds')).to_have_value('1970-01-20T16:13:20.000Z')
    expect(static_page.locator('#timestamp-terms dt')).to_have_count(4)
    expect(static_page.locator('#epoch-python-example')).to_contain_text('divmod')
    graph = json.loads(static_page.locator('script[type="application/ld+json"]').inner_text())['@graph']
    article = next(x for x in graph if x['@type'] == 'TechArticle')
    assert article['headline'] == static_page.locator('h1').inner_text()
    assert article['url'] == 'https://parsecove.com' + ROUTE
    assert article['datePublished'] == article['dateModified'] == '2026-11-27'
    breadcrumb = next(x for x in graph if x['@type'] == 'BreadcrumbList')
    assert breadcrumb['itemListElement'][-1]['name'] == 'Unix timestamp units'
    static.close()
    assert not errors, errors
    assert not external, external
    assert not mutations, mutations
    report = {'fixed_unit_cases': len(cases), 'invalid_input_and_stale_copy': 'passed',
              'published_code_snippets': len(snippets), 'explicit_unit_presets': 'passed',
              'unknown_presets': 'ignored', 'navigation_and_links': 'passed',
              'static_content_and_schema': 'passed', 'responsive_checks': checks,
              'page_errors': errors, 'external_requests': external, 'input_upload_requests': mutations}
    (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    browser.close()

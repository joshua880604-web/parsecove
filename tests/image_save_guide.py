"""Execute the published guide examples and verify their original PNG bytes."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000').rstrip('/')
OUT = Path('/workspace/work/parsecove-image-guide-qa')
OUT.mkdir(parents=True, exist_ok=True)
ROUTE = '/guides/save-base64-image/'
ORIGINAL = Path('dist/assets/examples/sample.png').read_bytes()
DATA_URL = 'data:image/png;base64,' + base64.b64encode(ORIGINAL).decode()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True,
                                  permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external, mutations = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((BASE, 'blob:', 'data:')) else None)
    page.on('request', lambda r: mutations.append(r.url) if r.method != 'GET' else None)

    def verify_download(pending, save_as, expected=ORIGINAL):
        target = OUT / save_as
        pending.value.save_as(str(target))
        assert target.read_bytes() == expected, save_as
        return pending.value.suggested_filename

    assert page.goto(BASE + ROUTE).status == 200
    expect(page.locator('h1')).to_have_text('How to save a Base64 image to a file')
    expect(page.locator('#save-image-sample')).to_have_value(DATA_URL)
    assert base64.b64decode(page.locator('#save-image-sample').input_value().split(',', 1)[1]) == ORIGINAL
    expect(page.locator('.save-sample-facts')).to_contain_text('2,824 bytes')
    expect(page.locator('.save-sample-facts')).to_contain_text('3,768 characters')
    page.locator('[data-copy="save-image-sample"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == DATA_URL
    with page.expect_download() as pending:
        page.locator('#save-original-png').click()
    assert verify_download(pending, 'direct-original.png') == 'parsecove-example.png'
    page.locator('.save-checksum summary').click()
    expect(page.locator('#save-image-sha')).to_have_text(hashlib.sha256(ORIGINAL).hexdigest())
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(OUT / 'save-image-desktop.png'), full_page=True)
    page.locator('#complete-sample').screenshot(path=str(OUT / 'sample-desktop.png'), style='.skip:not(:focus){visibility:hidden}')

    # Execute the exact JavaScript printed in the article, not a test reimplementation.
    javascript = page.locator('#save-js-example pre code').inner_text()
    with page.expect_download() as pending:
        page.evaluate('()=>{' + javascript + '\n}')
    assert verify_download(pending, 'javascript-example.png') == 'parsecove-example.png'
    python = page.locator('#save-python-example pre code').inner_text()
    python_dir = OUT / 'python-example'
    python_dir.mkdir(exist_ok=True)
    subprocess.run([sys.executable, '-c', python], input=DATA_URL + '\n', text=True,
                   cwd=python_dir, capture_output=True, check=True)
    assert (python_dir / 'parsecove-example.png').read_bytes() == ORIGINAL

    # The expandable HTML contains the complete image and renders at its real dimensions.
    page.locator('.save-html-example summary').click()
    html = page.locator('#save-html-code pre code').inner_text()
    preview = context.new_page()
    preview.set_content(html)
    preview.locator('img').evaluate('(img)=>img.decode()')
    assert preview.locator('img').evaluate('(img)=>[img.naturalWidth,img.naturalHeight]') == [320, 180]
    expect(preview.locator('img')).to_have_attribute('src', DATA_URL)
    preview.close()

    # Guide navigation loads the public fixture directly into the existing viewer.
    page.locator('#save-open-viewer').click()
    expect(page.locator('#image-status')).to_have_text('Ready')
    expect(page.locator('#image-input')).to_have_value(DATA_URL)
    expect(page.locator('#image-mime')).to_have_text('image/png')
    expect(page.locator('#image-dimensions')).to_have_text('320 × 180')
    with page.expect_download() as pending:
        page.locator('#image-download').click()
    assert verify_download(pending, 'viewer-example.png') == 'parsecove-image.png'

    # Each supported preset uses original local bytes on both image entry points.
    preset_checks = 0
    for route in ['/base64-to-image/', '/image-to-base64/']:
        for key, extension, mime in [('png', 'png', 'image/png'), ('jpeg', 'jpg', 'image/jpeg'),
                                      ('webp', 'webp', 'image/webp')]:
            page.goto(BASE + route + '?example=' + key)
            expect(page.locator('#image-status')).to_have_text('Ready')
            expect(page.locator('#image-mime')).to_have_text(mime)
            expected = Path('dist/assets/examples/sample.' + extension).read_bytes()
            with page.expect_download() as pending:
                page.locator('#image-download').click()
            verify_download(pending, f'{route.strip("/")}-{key}.{extension}', expected)
            if route == '/image-to-base64/':
                expect(page.locator('#image-text')).to_have_value('data:' + mime + ';base64,' + base64.b64encode(expected).decode())
            preset_checks += 1
    for value in ['https%3A%2F%2Fexample.invalid%2Fsample.png', '__proto__', 'unknown']:
        page.goto(BASE + '/base64-to-image/?example=' + value)
        expect(page.locator('#image-status')).to_have_text('Waiting for input')
        expect(page.locator('#image-input')).to_have_value('')
        expect(page.locator('#image-download')).to_be_hidden()

    for route in ['/base64-to-image/', '/image-to-base64/']:
        page.goto(BASE + route)
        expect(page.locator('.guide-teaser a')).to_have_attribute('href', ROUTE)
    page.goto(BASE + '/')
    expect(page.locator('.guides-preview .guide-card')).to_have_count(4)
    page.goto(BASE + '/guides/')
    expect(page.locator('.guide-card')).to_have_count(4)
    page.locator('.guide-card[href="' + ROUTE + '"]').click()
    expect(page.locator('#save-faq details')).to_have_count(4)
    expect(page.locator('#save-terms dt')).to_have_count(4)
    page.locator('#save-faq summary').first.click()
    expect(page.locator('#save-faq details').first).to_contain_text('filename extension alone')
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('save a base64 image')
    expect(page.locator('#search-list a:visible')).to_have_count(1)
    page.locator('#search-list a:visible').click()
    assert page.url == BASE + ROUTE

    checks = 0
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for route in ['/guides/', ROUTE, '/base64-to-image/?example=png']:
            assert page.goto(BASE + route).status == 200
            if '?example' in route:
                expect(page.locator('#image-status')).to_have_text('Ready')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route)
            expect(page.locator('h1')).to_have_count(1)
            expect(page.locator('[data-ad-slot]')).to_have_count(0)
            if width == 390 and route == ROUTE:
                page.locator('.save-checksum summary').click()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.evaluate('window.scrollTo(0,0)')
                page.screenshot(path=str(OUT / 'save-image-mobile.png'), full_page=True)
                page.locator('#complete-sample').screenshot(path=str(OUT / 'sample-mobile.png'), style='.skip:not(:focus){visibility:hidden}')
            checks += 1

    static = browser.new_context(java_script_enabled=False)
    static_page = static.new_page()
    static_page.goto(BASE + ROUTE)
    expect(static_page.locator('#save-image-sample')).to_have_value(DATA_URL)
    expect(static_page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://parsecove.com' + ROUTE)
    expect(static_page.locator('meta[property="og:type"]')).to_have_attribute('content', 'article')
    expect(static_page.locator('#save-image-sha')).to_have_text(hashlib.sha256(ORIGINAL).hexdigest())
    expect(static_page.locator('#save-python-example')).to_contain_text('write_bytes')
    graph = json.loads(static_page.locator('script[type="application/ld+json"]').inner_text())['@graph']
    article = next(x for x in graph if x['@type'] == 'TechArticle')
    assert article['headline'] == static_page.locator('h1').inner_text()
    assert article['url'] == 'https://parsecove.com' + ROUTE
    breadcrumb = next(x for x in graph if x['@type'] == 'BreadcrumbList')
    assert breadcrumb['itemListElement'][-1]['name'] == 'Save a Base64 image'
    assert article['datePublished'] == article['dateModified'] == '2026-11-27'
    static.close()
    assert not errors, errors
    assert not external, external
    assert not mutations, mutations
    report = {'complete_fixture_and_clipboard': 'passed', 'published_javascript': 'passed',
              'published_python': 'passed', 'complete_html_preview': 'passed',
              'byte_identical_downloads': 'passed', 'image_route_presets': preset_checks,
              'unknown_presets': 'ignored', 'navigation_and_links': 'passed',
              'static_content_and_schema': 'passed', 'responsive_checks': checks,
              'page_errors': errors, 'external_requests': external, 'input_upload_requests': mutations}
    (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    browser.close()

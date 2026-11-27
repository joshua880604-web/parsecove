"""Check published Base64 diagnosis examples, byte/text stages and tool handoffs."""
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urljoin, urlparse, unquote
import xml.etree.ElementTree as ET

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000').rstrip('/')
OUT = Path('/workspace/work/parsecove-base64-errors-guide-qa')
OUT.mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[1]
ROUTE = '/guides/fix-invalid-base64/'
EXPECTED_CODE = ['Zg==: f', 'Zg: f', 'Zg=: rejected', 'a$bc: rejected',
                 'Zh==: rejected', '+//v: valid bytes; not UTF-8 text', '8J-YgA: rejected']
CASES = [
    ('bad-padding', 'Zg=', None, None),
    ('padded', 'Zg==', '66', 'f'),
    ('unpadded', 'Zg', '66', 'f'),
    ('bad-character', 'a$bc', None, None),
    ('url-wrong', '8J-YgA', None, None),
    ('url-right', '8J-YgA', 'f0 9f 98 80', '😀'),
    ('trailing-bits', 'Zh==', None, None),
    ('binary', '+//v', 'fb ff ef', None),
    ('data-url', 'data:text/plain;base64,Zg==', None, None),
]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True,
                                  permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external, mutations = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((BASE, 'blob:', 'data:')) else None)
    page.on('request', lambda r: mutations.append(r.url) if r.method != 'GET' else None)
    assert page.goto(BASE + ROUTE).status == 200
    expect(page.locator('#b64-case-select option')).to_have_count(9)
    expect(page.locator('#b64-case-input')).to_have_attribute('readonly', '')
    expect(page.locator('#b64-case-text')).to_have_attribute('readonly', '')
    expect(page.locator('#b64-case-parser-message')).to_have_text('Invalid Base64 length or padding.')
    page.locator('[data-copy="b64-case-input"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == 'Zg='
    page.locator('#base64-error-examples').screenshot(path=str(OUT / 'diagnosis-desktop.png'),
                                                    style='.skip:not(:focus){visibility:hidden}')
    links = {}
    # Visit a successful case before every case to catch stale decoded output.
    for key, value, hex_value, plain in CASES:
        page.locator('#b64-case-select').select_option('url-right')
        page.locator('#b64-case-select').select_option(key)
        expect(page.locator('#b64-case-input')).to_have_value(value)
        expect(page.locator('#b64-case-encoding')).to_have_text('Accepted' if hex_value else 'Rejected')
        expect(page.locator('#b64-case-encoding')).to_have_attribute('data-state', 'pass' if hex_value else 'fail')
        expect(page.locator('#b64-case-utf8')).to_have_text(
            'Not attempted' if hex_value is None else 'Not UTF-8 text' if plain is None else 'Valid UTF-8')
        expect(page.locator('#b64-case-hex')).to_have_text(hex_value or '')
        expect(page.locator('#b64-case-text')).to_have_value(plain or '')
        if hex_value:
            expect(page.locator('#b64-case-bytes-wrap')).to_be_visible()
        else:
            expect(page.locator('#b64-case-bytes-wrap')).to_be_hidden()
        if plain:
            expect(page.locator('#b64-case-text-wrap')).to_be_visible()
            expect(page.locator('[data-copy="b64-case-text"]')).to_be_enabled()
        else:
            expect(page.locator('#b64-case-text-wrap')).to_be_hidden()
            expect(page.locator('[data-copy="b64-case-text"]')).to_be_disabled()
        if key == 'trailing-bits':
            expect(page.locator('#b64-case-parser-message')).to_contain_text('Non-canonical Base64')
        links[key] = page.locator('#b64-case-next').get_attribute('href')
    page.locator('#b64-case-select').select_option('url-right')
    page.locator('[data-copy="b64-case-text"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == '😀'
    page.locator('#b64-case-select').select_option('binary')
    page.locator('#base64-error-examples').screenshot(path=str(OUT / 'binary-desktop.png'),
                                                    style='.skip:not(:focus){visibility:hidden}')

    # Run the exact snippets readers copy from the built article, not parallel test implementations.
    for selector, executable, filename in [('#base64-error-js pre code', 'node', 'published-check.mjs'),
                                           ('#base64-error-python pre code', sys.executable, 'published-check.py')]:
        source = page.locator(selector).inner_text()
        path = OUT / filename
        path.write_text(source + '\n')
        result = subprocess.run([executable, str(path)], capture_output=True, text=True, check=True)
        assert result.stdout.strip().splitlines() == EXPECTED_CODE, result.stdout

    for key in ['bad-padding', 'padded', 'unpadded', 'bad-character', 'url-wrong', 'url-right', 'trailing-bits', 'data-url']:
        page.goto(urljoin(BASE, links[key]))
        expected_input = {'bad-padding': 'Zg=', 'padded': 'Zg==', 'unpadded': 'Zg',
                          'bad-character': 'a$bc', 'url-wrong': '8J-YgA', 'url-right': '8J-YgA',
                          'trailing-bits': 'Zh==', 'data-url': 'Zg=='}[key]
        expect(page.locator('#b64-input')).to_have_value(expected_input)
        expect(page.locator('#b64-variant')).to_have_value('url' if key in ['url-wrong', 'url-right'] else 'standard')
        if key in ['bad-padding', 'bad-character', 'trailing-bits']:
            expect(page.locator('#b64-error')).to_be_visible()
            expect(page.locator('#b64-output')).to_have_value('')
        else:
            expect(page.locator('#b64-error')).to_be_hidden()
            expect(page.locator('#b64-output')).to_have_value('😀' if key in ['url-wrong', 'url-right'] else 'f')
    page.goto(urljoin(BASE, links['binary']))
    expect(page.locator('#url-format')).to_have_value('hex')
    expect(page.locator('#url-input')).to_have_value('-__v')
    expect(page.locator('#url-output')).to_have_value('fb ff ef')
    expect(page.locator('#url-standard')).to_have_value('+//v')
    with page.expect_download() as download:
        page.locator('#url-bytes-download').click()
    assert Path(download.value.path()).read_bytes() == bytes.fromhex('fb ff ef')
    for example, value in [('emoji', '😀'), ('json', '{"message":"Hello"}')]:
        page.goto(BASE + '/base64url-decode/?example=' + example)
        expect(page.locator('#url-output')).to_have_value(value)
    for route, input_id, output_id in [('/base64/', '#b64-input', '#b64-output'),
                                       ('/base64url-decode/', '#url-input', '#url-output')]:
        page.goto(BASE + route)
        initial_input, initial_output = page.locator(input_id).input_value(), page.locator(output_id).input_value()
        expect(page.locator('.guide-teaser a')).to_have_attribute('href', ROUTE)
        for value in ['unknown', '__proto__', 'https%3A%2F%2Fexample.invalid%2F', 'input%3Dsecret']:
            page.goto(BASE + route + '?example=' + value)
            expect(page.locator(input_id)).to_have_value(initial_input)
            expect(page.locator(output_id)).to_have_value(initial_output)

    page.goto(BASE + '/')
    expect(page.locator('.guides-preview .guide-card')).to_have_count(6)
    page.goto(BASE + '/guides/')
    expect(page.locator('.guide-card')).to_have_count(6)
    page.locator('.guide-card[href="' + ROUTE + '"]').click()
    expect(page.locator('#base64-error-faq details')).to_have_count(4)
    page.locator('#base64-error-faq summary').first.click()
    expect(page.locator('#base64-error-faq details').first).to_contain_text('No. Some formats allow unpadded')
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('Invalid Base64 String')
    expect(page.locator('#search-list a:visible')).to_have_count(1)
    expect(page.locator('#search-list a:visible')).to_have_attribute('href', ROUTE)
    page.locator('#search-close').click()
    page.goto(BASE + '/guides/save-base64-image/')
    expect(page.locator('#image-errors a[href="' + ROUTE + '"]')).to_have_count(1)

    responsive_checks = 0
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        for route in ['/guides/', ROUTE, '/base64/?example=url-safe']:
            page.goto(BASE + route)
            if route == ROUTE:
                for key in ['bad-padding', 'url-right', 'binary']:
                    page.locator('#b64-case-select').select_option(key)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, key)
                if width == 390:
                    page.locator('#base64-error-examples').screenshot(path=str(OUT / 'diagnosis-mobile.png'),
                                                                    style='.skip:not(:focus){visibility:hidden}')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route)
            expect(page.locator('h1')).to_have_count(1)
            expect(page.locator('[data-ad-slot]')).to_have_count(0)
            responsive_checks += 1

    static = browser.new_context(java_script_enabled=False)
    nojs = static.new_page()
    nojs.goto(BASE + ROUTE)
    expect(nojs.locator('#b64-case-select option')).to_have_count(9)
    expect(nojs.locator('#b64-case-input')).to_have_value('Zg=')
    expect(nojs.locator('#b64-case-encoding')).to_have_text('Rejected')
    expect(nojs.locator('#base64-error-terms dt')).to_have_count(4)
    expect(nojs.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://parsecove.com' + ROUTE)
    expect(nojs.locator('meta[property="og:type"]')).to_have_attribute('content', 'article')
    graph = json.loads(nojs.locator('script[type="application/ld+json"]').inner_text())['@graph']
    article = next(x for x in graph if x['@type'] == 'TechArticle')
    assert article['url'] == 'https://parsecove.com' + ROUTE
    assert article['headline'] == nojs.locator('h1').inner_text()
    assert article['datePublished'] == article['dateModified'] == '2026-11-27'
    assert article['author']['name'] == 'ParseCove'
    assert len(next(x for x in graph if x['@type'] == 'BreadcrumbList')['itemListElement']) == 3
    static.close()

    # Check every built local navigation target, including query presets and fragments.
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.links = []; self.ids = set()
        def handle_starttag(self, tag, attrs):
            attr = dict(attrs)
            if 'id' in attr: self.ids.add(attr['id'])
            if tag == 'a' and 'href' in attr: self.links.append(attr['href'])
    docs = {}
    for path in (ROOT / 'dist').rglob('*.html'):
        parser = Links(); parser.feed(path.read_text()); docs[path] = parser
    link_checks = 0
    for path, parser in docs.items():
        route = '/' + str(path.relative_to(ROOT / 'dist')).replace('index.html', '')
        for href in parser.links:
            dest = urlparse(urljoin('https://parsecove.com' + route, href))
            if dest.scheme not in ['http', 'https'] or dest.netloc != 'parsecove.com': continue
            target = ROOT / 'dist' / dest.path.lstrip('/')
            if target.is_dir(): target /= 'index.html'
            assert target.exists(), (path, href)
            if dest.fragment and target in docs:
                assert unquote(dest.fragment) in docs[target].ids, (path, href)
            link_checks += 1
    sitemap = ET.parse(ROOT / 'dist/sitemap.xml')
    urls = [n.text for n in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    assert 'https://parsecove.com' + ROUTE in urls
    assert len(urls) == len(set(urls)) == 23
    assert len(docs) == 24
    assert not errors, errors
    assert not external, external
    assert not mutations, mutations
    report = {'diagnosis_cases': len(CASES), 'published_code_snippets': 2, 'tool_handoffs': 9,
              'binary_download': 'fb ff ef', 'clipboard_and_stale_output': 'passed',
              'unknown_presets_ignored': 'passed', 'static_article_and_schema': 'passed',
              'responsive_checks': responsive_checks, 'html_files': len(docs), 'sitemap_urls': len(urls),
              'internal_link_checks': link_checks, 'page_errors': errors, 'external_requests': external,
              'input_upload_requests': mutations}
    (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    browser.close()

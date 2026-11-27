"""Base64URL user flows, strict validation and byte-preserving downloads."""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000').rstrip('/')
OUT = Path('/workspace/work/parsecove-base64url-qa')
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True,
                                  permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external, mutations = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((BASE, 'blob:', 'data:')) else None)
    page.on('request', lambda r: mutations.append(r.url) if r.method != 'GET' else None)

    def output(value):
        expect(page.locator('#url-output')).to_have_value(value)

    def decode(value):
        page.locator('#url-input').fill(value)
        page.locator('#url-convert').click()

    def download(selector, name):
        with page.expect_download() as pending:
            page.locator(selector).click()
        assert pending.value.suggested_filename == name
        path = OUT / name
        pending.value.save_as(str(path))
        return path.read_bytes()

    assert page.goto(BASE + '/base64url-decode/').status == 200
    expect(page.locator('h1')).to_have_text('Base64URL decoder & encoder')
    output('Hello, world!')
    expect(page.locator('#url-standard')).to_have_value('SGVsbG8sIHdvcmxkIQ==')
    expect(page.locator('#url-stats')).to_have_text('13 decoded bytes · unpadded input')
    expect(page.locator('#url-padding-wrap')).to_be_hidden()
    page.locator('[data-copy="url-output"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == 'Hello, world!'
    assert download('#url-download', 'parsecove-decoded.txt') == b'Hello, world!'
    assert download('#url-bytes-download', 'parsecove-decoded.bin') == b'Hello, world!'
    page.evaluate('window.scrollTo(0, 0)')
    page.screenshot(path=str(OUT / 'base64url-desktop.png'), full_page=True)

    # RFC 4648 vectors, with padding and whitespace handled explicitly.
    for encoded, plain in [('Zg', 'f'), ('Zg==', 'f'), ('Zm8', 'fo'), ('Zm9v', 'foo'),
                           ('Zm9vYg', 'foob'), ('Zm9vYmE', 'fooba'), ('Zm9vYmFy', 'foobar'),
                           ('8J-YgA', '😀'), (' 8J-\nYgA==\t', '😀')]:
        decode(encoded)
        output(plain)
    page.locator('#url-modes [data-mode="encode"]').click()
    output('8J-YgA')
    expect(page.locator('#url-input')).to_have_value('😀')
    expect(page.locator('#url-padding')).not_to_be_checked()
    expect(page.locator('#url-standard')).to_have_value('8J+YgA==')
    assert download('#url-download', 'parsecove-base64url.txt') == b'8J-YgA'
    assert download('#url-bytes-download', 'parsecove-decoded.bin') == '😀'.encode()
    page.locator('#url-padding').check()
    output('8J-YgA==')
    page.locator('#url-padding').uncheck()
    output('8J-YgA')
    page.locator('#url-modes [data-mode="decode"]').click()
    output('😀')

    page.locator('[data-url-example="json"]').click()
    output('{"message":"Hello"}')
    expect(page.locator('#url-input')).to_have_value('eyJtZXNzYWdlIjoiSGVsbG8ifQ')
    page.locator('[data-url-example="binary"]').click()
    output('fb ff ef')
    expect(page.locator('#url-output-label')).to_have_text('DECODED HEX BYTES')
    expect(page.locator('#url-standard')).to_have_value('+//v')
    assert download('#url-download', 'parsecove-decoded-hex.txt') == b'fb ff ef'
    assert download('#url-bytes-download', 'parsecove-decoded.bin') == bytes([251, 255, 239])
    page.locator('[data-copy="url-standard"]').click()
    assert page.evaluate('navigator.clipboard.readText()') == '+//v'

    # Valid binary is not silently replaced with lossy UTF-8 text.
    page.locator('#url-format').select_option('text')
    output('')
    expect(page.locator('#url-note')).to_contain_text('not UTF-8 text')
    expect(page.locator('#url-error')).to_be_hidden()
    expect(page.locator('#url-download')).to_be_disabled()
    expect(page.locator('#url-bytes-download')).to_be_enabled()
    page.locator('#url-modes [data-mode="encode"]').click()
    expect(page.locator('#url-input')).to_have_value('')
    output('')
    expect(page.locator('#url-bytes-download')).to_be_disabled()
    page.locator('#url-modes [data-mode="decode"]').click()
    decode('_w==')
    expect(page.locator('#url-note')).to_be_visible()
    expect(page.locator('#url-standard')).to_have_value('/w==')
    page.locator('#url-format').select_option('hex')
    output('ff')

    # All byte values survive the URL-safe decoder and original-byte download.
    original = bytes(range(256))
    decode(base64.urlsafe_b64encode(original).decode().rstrip('='))
    output(' '.join(f'{b:02x}' for b in original))
    assert download('#url-bytes-download', 'parsecove-decoded.bin') == original

    invalid_values = ['Z', 'Zg=', 'Zh', '8J-YgB', '8J+YgA==', '_w/+', 'a.b.c', '−w',
                      '%2F', 'data:text/plain;base64,Zg==', 'Zg===', 'Z=g=']
    for invalid in invalid_values:
        decode(invalid)
        expect(page.locator('#url-error')).to_be_visible()
        output('')
        expect(page.locator('#url-standard')).to_have_value('')
        expect(page.locator('#url-stats')).to_be_empty()
        expect(page.locator('#url-download')).to_be_disabled()
        expect(page.locator('#url-bytes-download')).to_be_disabled()
    page.locator('[data-url-example="emoji"]').click()
    output('😀')
    page.locator('#url-input').fill('not converted yet')
    output('')
    expect(page.locator('#url-standard')).to_have_value('')
    expect(page.locator('#url-bytes-download')).to_be_disabled()

    # Text is displayed as text, including markup, rather than inserted into the DOM.
    markup = '<img src="https://example.invalid/test" onerror="window.bad=true">'
    decode(base64.urlsafe_b64encode(markup.encode()).decode().rstrip('='))
    output(markup)
    expect(page.locator('main img')).to_have_count(0)
    assert page.evaluate('window.bad === undefined')
    assert page.url == BASE + '/base64url-decode/'

    page.evaluate("document.querySelector('#url-input').value = 'A'.repeat(2000001)")
    page.locator('#url-convert').click()
    expect(page.locator('#url-error')).to_contain_text('2 million')
    output('')
    expect(page.locator('#url-bytes-download')).to_be_disabled()
    page.locator('#url-modes [data-mode="encode"]').click()
    # The text limit is measured in UTF-8 bytes, not JS string length.
    page.locator('#url-input').fill('😀' * 250001)
    page.locator('#url-convert').click()
    expect(page.locator('#url-error')).to_contain_text('1,000,000 bytes')
    output('')
    page.locator('#url-input').fill('😀' * 250000)
    page.locator('#url-convert').click()
    expect(page.locator('#url-error')).to_be_hidden()
    expected = base64.urlsafe_b64encode(('😀' * 250000).encode()).decode().rstrip('=')
    assert page.locator('#url-output').input_value() == expected
    page.locator('#url-clear').click()
    output('')
    expect(page.locator('#url-standard')).to_have_value('')
    expect(page.locator('#url-error')).to_be_hidden()
    expect(page.locator('#url-bytes-download')).to_be_disabled()

    page.goto(BASE + '/')
    page.locator('#tool-filter').fill('base64url')
    expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(1)
    page.locator('.tools-grid a[href="/base64url-decode/"]').click()
    output('Hello, world!')
    page.goto(BASE + '/base64/')
    # Contextual help and task recommendations both offer the URL-safe workflow.
    expect(page.locator('main a[href="/base64url-decode/"]:not(.tool-card)')).to_have_count(2)
    expect(page.locator('.related a[href="/base64url-decode/"]')).to_have_count(1)
    expect(page.locator('#b64-output')).to_have_value('Hello, world!')

    checks = 0
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        page.goto(BASE + '/base64url-decode/')
        for mode in ['decode', 'encode']:
            page.locator(f'#url-modes [data-mode="{mode}"]').click()
            page.locator('[data-url-example="emoji"]').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, mode)
            expect(page.locator('#url-convert')).to_be_visible()
            checks += 1
            if width == 390 and mode == 'encode':
                page.evaluate('window.scrollTo(0, 0)')
                page.screenshot(path=str(OUT / 'base64url-mobile.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 640})
    page.locator('.mobile-menu').click()
    page.locator('#sidebar a[href="/base64url-decode/"]').scroll_into_view_if_needed()
    expect(page.locator('#sidebar a[href="/base64url-decode/"]')).to_be_in_viewport()
    page.locator('.sidebar-bottom a').scroll_into_view_if_needed()
    expect(page.locator('.sidebar-bottom a')).to_be_in_viewport()

    static = browser.new_context(java_script_enabled=False)
    static_page = static.new_page()
    static_page.goto(BASE + '/base64url-decode/')
    expect(static_page.locator('h1')).to_have_text('Base64URL decoder & encoder')
    expect(static_page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://parsecove.com/base64url-decode/')
    assert 'Base64URL Decoder' in static_page.title()
    assert 'optional padding' in static_page.locator('meta[name="description"]').get_attribute('content')
    expect(static_page.locator('#url-output')).to_have_value('Hello, world!')
    expect(static_page.locator('#base64url-padding')).to_contain_text('Zg==')
    expect(static_page.locator('#base64url-examples')).to_contain_text('-__v')
    expect(static_page.locator('#base64url-code')).to_contain_text('base64.urlsafe_b64decode')
    structured = json.loads(static_page.locator('script[type="application/ld+json"]').text_content())
    assert structured['@type'] == 'WebApplication'
    assert structured['url'] == 'https://parsecove.com/base64url-decode/'
    static.close()
    assert not errors, errors
    assert not external, external
    assert not mutations, mutations
    report = {'rfc_vectors_and_unicode': 'passed', 'strict_invalid_cases': len(invalid_values),
              'all_byte_values_roundtrip': 'passed', 'text_hex_and_byte_downloads': 'passed',
              'clipboard_and_mode_changes': 'passed', 'limits_and_stale_result_clear': 'passed',
              'static_content_and_metadata': 'passed', 'responsive_checks': checks,
              'page_errors': errors, 'external_requests': external, 'input_upload_requests': mutations}
    (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    browser.close()

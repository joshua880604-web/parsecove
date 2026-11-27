"""Exercise the dedicated encoder through actual file, clipboard and download flows."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import base64
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/workspace/work/parsecove-image-encoder-qa')
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get('PARSECOVE_TEST_URL', 'http://127.0.0.1:3000')
fixtures = [
    ('png', 'image/png', (ROOT/'dist/assets/examples/sample.png').read_bytes()),
    ('jpeg', 'image/jpeg', (ROOT/'dist/assets/examples/sample.jpg').read_bytes()),
    ('webp', 'image/webp', (ROOT/'dist/assets/examples/sample.webp').read_bytes()),
    ('gif', 'image/gif', base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')),
]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000}, permissions=['clipboard-read','clipboard-write'], accept_downloads=True)
    page = context.new_page()
    errors, external, mutations = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: external.append(request.url) if not request.url.startswith((BASE, 'blob:', 'data:')) else None)
    page.on('request', lambda request: mutations.append(request.url) if request.method not in ('GET','HEAD') else None)
    assert page.goto(BASE+'/image-to-base64/').status == 200
    expect(page.locator('#image-encode-input')).to_be_visible()
    expect(page.locator('#image-decode-input')).to_be_hidden()
    expect(page.locator('#image-modes button').first).to_have_attribute('data-mode','encode')
    expect(page.locator('#image-modes button').first).to_have_attribute('aria-pressed','true')
    expect(page.locator('#image-text')).to_be_visible()
    expect(page.locator('#image-text-copy')).to_be_disabled()
    expect(page.locator('#image-text-download')).to_be_disabled()
    expect(page.locator('#image-text-download')).to_have_class(re.compile(r'\bprimary\b'))

    for key, mime, original in fixtures:
        page.locator('#image-format').select_option('uri')
        page.locator('#image-file').set_input_files({'name':'input.'+key,'mimeType':mime,'buffer':original})
        expect(page.locator('#image-status')).to_have_text('Ready')
        expect(page.locator('#image-mime')).to_have_text(mime)
        expected = f'data:{mime};base64,'+base64.b64encode(original).decode()
        expect(page.locator('#image-text')).to_have_value(expected)
        assert base64.b64decode(page.locator('#image-text').input_value().split(',',1)[1]) == original

    original = fixtures[0][2]
    raw = base64.b64encode(original).decode()
    uri = 'data:image/png;base64,'+raw
    page.locator('#image-file').set_input_files({'name':'input.png','mimeType':'image/png','buffer':original})
    expect(page.locator('#image-status')).to_have_text('Ready')
    for format_name, expected, extension in [
        ('uri', uri, '.txt'), ('raw', raw, '.txt'),
        ('html', f'<img src="{uri}" alt="">', '.html'),
        ('css', f'background-image: url("{uri}");', '.css'),
    ]:
        page.locator('#image-format').select_option(format_name)
        expect(page.locator('#image-text')).to_have_value(expected)
        page.locator('#image-text-copy').click()
        assert page.evaluate('navigator.clipboard.readText()') == expected
        with page.expect_download() as pending:
            page.locator('#image-text-download').click()
        download = pending.value
        assert download.suggested_filename.endswith(extension)
        saved = OUT/('output-'+format_name+extension)
        download.save_as(str(saved))
        assert saved.read_text() == expected

    page.locator('#image-format').select_option('uri')
    page.screenshot(path=str(OUT/'encoder-desktop.png'), full_page=True)
    for name, payload, mime in [
        ('not-image.txt', b'Hello world', 'text/plain'),
        ('vector.svg', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>', 'image/svg+xml'),
        ('truncated.png', b'\x89PNG\r\n\x1a\n', 'image/png'),
        ('too-large.png', b'0'*(10485760+1), 'image/png'),
    ]:
        page.locator('#image-file').set_input_files({'name':name,'mimeType':mime,'buffer':payload})
        expect(page.locator('#image-error')).to_be_visible()
        expect(page.locator('#image-text')).to_have_value('')
        expect(page.locator('#image-text-copy')).to_be_disabled()
        expect(page.locator('#image-text-download')).to_be_disabled()
        expect(page.locator('#image-output')).to_be_hidden()
        expect(page.locator('#image-download')).to_be_hidden()

    for key in ['png','jpeg','webp']:
        page.locator(f'[data-image-encode-example="{key}"]').click()
        expect(page.locator('#image-status')).to_have_text('Ready')
        expect(page.locator('#image-text-copy')).to_be_enabled()
        expect(page.locator('#image-dimensions')).to_have_text('320 × 180')
        assert page.locator('#image-text').input_value().startswith('data:image/')

    page.evaluate('''({payload}) => {
      const transfer = new DataTransfer();
      transfer.items.add(new File([Uint8Array.from(atob(payload), c => c.charCodeAt(0))], 'dropped.png', {type:'image/png'}));
      document.querySelector('#image-drop').dispatchEvent(new DragEvent('drop', {dataTransfer:transfer, bubbles:true}));
    }''', {'payload':raw})
    expect(page.locator('#image-status')).to_have_text('Ready')
    expect(page.locator('#image-file-name')).to_have_text('dropped.png')
    expect(page.locator('#image-text')).to_have_value(uri)
    page.evaluate('''() => {
      const transfer = new DataTransfer();
      transfer.items.add(new File(['a'], 'one.png')); transfer.items.add(new File(['b'], 'two.png'));
      document.querySelector('#image-drop').dispatchEvent(new DragEvent('drop', {dataTransfer:transfer, bubbles:true}));
    }''')
    expect(page.locator('#image-error')).to_contain_text('one image at a time')
    expect(page.locator('#image-text')).to_have_value('')

    page.locator('[data-image-encode-example="png"]').click()
    expect(page.locator('#image-status')).to_have_text('Ready')
    page.locator('#image-clear').click()
    expect(page.locator('#image-text')).to_have_value('')
    expect(page.locator('#image-text-download')).to_be_disabled()
    page.locator('#image-modes [data-mode="decode"]').click()
    expect(page.locator('#image-decode-input')).to_be_visible()
    page.locator('#image-input').fill(uri)
    page.locator('#image-convert').click()
    expect(page.locator('#image-status')).to_have_text('Ready')
    expect(page.locator('#image-text-wrap')).to_be_hidden()
    expect(page.locator('#image-dimensions')).to_have_text('320 × 180')
    expect(page.locator('#image-download')).to_have_class(re.compile(r'\bprimary\b'))
    page.locator('#image-modes [data-mode="encode"]').click()
    expect(page.locator('#image-text')).to_have_value('')
    expect(page.locator('#image-text-download')).to_be_disabled()

    assert page.goto(BASE+'/base64-to-image/').status == 200
    page.locator('#image-sample').click()
    expect(page.locator('#image-status')).to_have_text('Ready')
    expect(page.locator('#image-error-link')).to_have_attribute('href','#image-troubleshooting')
    page.locator('#image-modes [data-mode="encode"]').click()
    page.locator('[data-image-encode-example="png"]').click()
    expect(page.locator('#image-status')).to_have_text('Ready')
    expect(page.locator('#image-text')).to_have_value(uri)

    for width in [320,390,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        for route in ['/','/base64-to-image/','/image-to-base64/']:
            assert page.goto(BASE+route).status == 200
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route)
        page.locator('[data-image-encode-example="png"]').click()
        expect(page.locator('#image-status')).to_have_text('Ready')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,'encoded-output')
    page.set_viewport_size({'width':390,'height':950})
    page.screenshot(path=str(OUT/'encoder-mobile.png'),full_page=True)
    page.locator('.result-panel').screenshot(path=str(OUT/'encoder-mobile-result.png'))
    page.locator('.mobile-menu').click()
    expect(page.locator('#sidebar')).to_have_class(re.compile('open'))
    page.locator('.sidebar-close').click()
    page.locator('.search-trigger').click()
    page.locator('#global-search').fill('image to base64')
    expect(page.locator('#search-list a:visible')).to_have_count(1)
    expect(page.locator('#search-list a:visible')).to_have_attribute('href','/image-to-base64/')
    page.locator('#search-close').click()

    nojs = browser.new_context(java_script_enabled=False)
    static_page = nojs.new_page()
    static_page.goto(BASE+'/image-to-base64/')
    expect(static_page.locator('#image-encode-input')).to_be_visible()
    expect(static_page.locator('h1')).to_have_text('Image to Base64 converter')
    expect(static_page.locator('#image-encoding-reference')).to_be_visible()
    expect(static_page.locator('link[rel="canonical"]')).to_have_attribute('href','https://parsecove.com/image-to-base64/')
    nojs.close()
    assert not errors,errors
    assert not external,external
    assert not mutations,mutations
    print(json.dumps({'file_roundtrips':4,'clipboard_and_download_formats':4,'local_examples':3,'invalid_file_cases':4,'drag_and_drop':'passed','both_image_routes':'passed','responsive_widths':[320,390,768,1024,1440],'static_no_js_content':'passed','page_errors':errors,'external_requests':external,'input_upload_requests':mutations,'artifacts':str(OUT)}))
    browser.close()

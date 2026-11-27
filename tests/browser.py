from playwright.sync_api import sync_playwright,expect
from pathlib import Path
import json
out=Path('/workspace/work/bytebench')
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
 page=context.new_page();errors=[];external=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('http://127.0.0.1:3000','blob:','data:')) else None)
 base='http://127.0.0.1:3000'
 assert page.goto(base).status==200
 page.screenshot(path=str(out/'home-desktop.png'),full_page=True)
 page.locator('#tool-filter').fill('image');expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(2)
 page.get_by_role('link',name='Base64 to image',exact=False).last # no click needed
 page.goto(base+'/unix-timestamp-converter/')
 expect(page.locator('#time-iso')).to_have_text('2023-11-14T22:13:20.000Z')
 page.locator('#timestamp-input').fill('1700000000000');page.locator('#time-convert').click();expect(page.locator('#time-detected')).to_contain_text('milliseconds')
 page.locator('#time-zone').select_option('America/New_York');expect(page.locator('#time-readable')).to_contain_text('17:13:20')
 page.locator('#timestamp-input').fill('wrong');page.locator('#time-convert').click();expect(page.locator('#time-error')).to_be_visible();expect(page.locator('#time-iso')).to_be_empty()
 page.get_by_role('button',name='Date to timestamp',exact=True).click();page.locator('#iso-input').fill('2023-02-29T00:00:00Z');page.locator('#time-convert').click();expect(page.locator('#time-error')).to_be_visible()
 page.get_by_role('button',name='Batch convert',exact=True).click();page.locator('#batch-input').fill('1700000000\nwrong\n0');page.locator('#time-convert').click();expect(page.locator('#batch-summary')).to_have_text('2 converted · 1 invalid · UTC output')
 with page.expect_download() as d:page.locator('#batch-download').click()
 assert d.value.suggested_filename.endswith('.csv')
 page.goto(base+'/px-to-rem/');expect(page.locator('#px-output')).to_have_value('1.5rem')
 page.locator('#px-base').fill('20');expect(page.locator('#px-output')).to_have_value('1.2rem')
 page.locator('#px-input').fill('20,40\n60');expect(page.locator('#px-output')).to_have_value('1rem\n2rem\n3rem')
 page.locator('#px-base').fill('0');expect(page.locator('#px-error')).to_be_visible();expect(page.locator('#px-output')).to_have_value('')
 page.goto(base+'/base64/');expect(page.locator('#b64-output')).to_have_value('Hello, world!')
 page.locator('#b64-sample').click();expect(page.locator('#b64-output')).to_have_value('Hello, 世界 👋')
 page.get_by_role('button',name='Encode',exact=True).click();expect(page.locator('#b64-output')).to_have_value('SGVsbG8sIOS4lueVjCDwn5GL')
 page.get_by_role('button',name='Decode',exact=True).click();expect(page.locator('#b64-output')).to_have_value('Hello, 世界 👋')
 page.locator('#b64-input').fill('Zh==');page.locator('#b64-convert').click();expect(page.locator('#b64-error')).to_be_visible();expect(page.locator('#b64-output')).to_have_value('')
 page.goto(base+'/base64-to-image/');page.locator('#image-sample').click();expect(page.locator('#image-status')).to_have_text('Ready');expect(page.locator('#image-dimensions')).to_have_text('320 × 180')
 with page.expect_download() as d:page.locator('#image-download').click()
 saved=out/'sample.png';d.value.save_as(str(saved));assert saved.read_bytes().startswith(b'\x89PNG')
 page.screenshot(path=str(out/'image-desktop.png'),full_page=True)
 page.get_by_role('button',name='Image to Base64',exact=True).click();page.locator('#image-file').set_input_files(str(saved));expect(page.locator('#image-status')).to_have_text('Ready');expect(page.locator('#image-text')).to_have_value(__import__('re').compile('^data:image/png;base64,'))
 page.locator('#image-format').select_option('html');expect(page.locator('#image-text')).to_have_value(__import__('re').compile('^<img src='))
 page.get_by_role('button',name='Base64 to image',exact=True).click();page.locator('#image-input').fill('PHN2Zz48L3N2Zz4=');page.locator('#image-convert').click();expect(page.locator('#image-error')).to_be_visible();expect(page.locator('#image-download')).to_be_hidden()
 for width in [1440,390]:
  page.set_viewport_size({'width':width,'height':900})
  for route in ['/','/unix-timestamp-converter/','/px-to-rem/','/base64/','/base64-to-image/','/image-to-base64/','/privacy/','/about/']:
   r=page.goto(base+route);assert r.status==200
   assert page.locator('h1').count()==1
   assert page.locator('link[rel=canonical]').count()==1
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route,'horizontal overflow')
  if width==390:
   page.goto(base);page.screenshot(path=str(out/'home-mobile.png'),full_page=True)
   page.locator('.mobile-menu').click();expect(page.locator('#sidebar')).to_have_class(__import__('re').compile('open'))
   page.locator('.sidebar-close').click()
   page.locator('.search-trigger').click();page.locator('#global-search').fill('base64');expect(page.locator('#search-list a:visible')).to_have_count(3);page.locator('#search-close').click()
 assert not errors,errors
 assert not external,external
 print(json.dumps({'browser_checks':'passed','viewport_widths':[1440,390],'external_app_requests':external,'page_errors':errors,'screenshots':str(out)}))
 browser.close()

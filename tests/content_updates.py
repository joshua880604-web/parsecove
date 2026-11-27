from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from datetime import datetime,timezone
import hashlib,json,re,os
out=Path('/workspace/work/parsecove-content-qa');out.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'],accept_downloads=True)
 page=context.new_page();errors=[];external=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 base=os.environ.get('PARSECOVE_TEST_URL','http://127.0.0.1:3000').rstrip('/')
 page.on('request',lambda r:external.append(r.url) if not r.url.startswith((base,'blob:','data:')) else None)
 page.clock.install(time=datetime(2026,11,26,12,0,tzinfo=timezone.utc))
 page.goto(base+'/unix-timestamp-converter/')
 first=page.locator('#clock-ms').input_value();assert len(first)==13
 page.clock.run_for(1100);assert int(page.locator('#clock-ms').input_value())>int(first)
 page.locator('#clock-toggle').click();paused=page.locator('#clock-ms').input_value();page.clock.run_for(2100);expect(page.locator('#clock-ms')).to_have_value(paused)
 page.locator('#clock-toggle').click();page.clock.run_for(1100);assert int(page.locator('#clock-ms').input_value())>int(paused)
 page.locator('[data-copy="clock-seconds"]').click();expect(page.locator('#clock-toggle')).to_have_text('Resume updates')
 copied=page.evaluate('navigator.clipboard.readText()');assert copied==page.locator('#clock-seconds').input_value();page.clock.run_for(2100);expect(page.locator('#clock-seconds')).to_have_value(copied)
 expect(page.locator('#timestamp-input')).to_have_value('1700000000')
 page.locator('#time-modes [data-mode="date"]').click();page.locator('#iso-input').fill('2023-11-14T22:13:20Z');page.locator('#time-convert').click();expect(page.locator('#time-seconds')).to_have_text('1700000000')
 expect(page.locator('#epoch-reference')).to_contain_text('1700000000000')
 page.screenshot(path=str(out/'timestamp-desktop.png'),full_page=True)
 page.goto(base+'/px-to-rem/')
 page.locator('[data-px-quick="14"]').click();expect(page.locator('#px-output')).to_have_value('0.875rem')
 page.locator('[data-px-quick="150"]').click();expect(page.locator('#px-output')).to_have_value('9.375rem')
 expect(page.locator('#px-table')).to_contain_text('150px')
 page.locator('#px-base').fill('20');expect(page.locator('#px-output')).to_have_value('7.5rem')
 tr=page.locator('#px-table tr').filter(has=page.locator('td',has_text='150px'));expect(tr).to_contain_text('7.5rem')
 page.locator('#px-modes [data-mode="rem"]').click();page.locator('[data-px-quick="80"]').click();expect(page.locator('#px-modes [data-mode="px"]')).to_have_attribute('aria-pressed','true');expect(page.locator('#px-output')).to_have_value('4rem')
 page.goto(base+'/base64-to-image/')
 expect(page.locator('[data-image-example]')).to_have_count(3)
 for key,mime,ext in [('png','image/png','png'),('jpeg','image/jpeg','jpg'),('webp','image/webp','webp')]:
  page.locator(f'[data-image-example="{key}"]').click();expect(page.locator('#image-status')).to_have_text('Ready');expect(page.locator('#image-mime')).to_have_text(mime);expect(page.locator('#image-dimensions')).to_have_text('320 × 180')
  with page.expect_download() as down:page.locator('#image-download').click()
  save=out/('download.'+ext);down.value.save_as(str(save));assert save.read_bytes()==Path('dist/assets/examples/sample.'+ext).read_bytes()
  if key=='png':png=page.locator('#image-input').input_value()
 expect(page.locator('#image-preservation')).to_be_visible()
 page.locator('#image-input').fill(png.replace('data:image/png;','data:image/jpeg;'));page.locator('#image-convert').click();expect(page.locator('#image-warning')).to_be_visible();expect(page.locator('#image-mime')).to_have_text('image/png')
 expect(page.locator('#image-download')).to_have_attribute('download','parsecove-image.png')
 page.locator('#image-input').fill('SGVsbG8=');page.locator('#image-convert').click();expect(page.locator('#image-error')).to_be_visible();expect(page.locator('#image-error-help')).to_be_visible();expect(page.locator('#image-download')).to_be_hidden();expect(page.locator('#image-preservation')).to_be_hidden()
 page.locator('[data-image-example="png"]').click();expect(page.locator('#image-status')).to_have_text('Ready');expect(page.locator('#image-error-help')).to_be_hidden()
 page.screenshot(path=str(out/'image-desktop.png'),full_page=True)
 checks=0
 for width in [320,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':950})
  for route in ['/','/unix-timestamp-converter/','/px-to-rem/','/rem-to-px/','/base64/','/base64url-decode/','/base64-to-image/','/image-to-base64/','/guides/','/guides/rem-vs-em/','/guides/save-base64-image/','/guides/unix-timestamp-seconds-vs-milliseconds/']:
   assert page.goto(base+route).status==200
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route,'overflow')
   expect(page.locator('[data-ad-slot]')).to_have_count(0)
   assert page.locator('h1').count()==1
   checks+=1
 page.set_viewport_size({'width':390,'height':950});page.goto(base+'/base64-to-image/');page.locator('[data-image-example="png"]').click();expect(page.locator('#image-status')).to_have_text('Ready');page.screenshot(path=str(out/'image-mobile.png'),full_page=True)
 assert not errors,errors
 assert not external,external
 print(json.dumps({'responsive_checks':checks,'clock_pause_copy':'passed','sample_download_original_bytes':'passed (PNG/JPEG/WebP)','invalid_image_and_mime_mismatch':'passed','px_root_and_quick_values':'passed','page_errors':errors,'external_requests':external}))
 browser.close()

"""Run after serving dist on :3000 and an isolated ad preview on :3001."""
from playwright.sync_api import sync_playwright, expect
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ad_slots import load_config,render_slot

routes=['/','/unix-timestamp-converter/','/px-to-rem/','/base64/','/base64-to-image/']
widths=[320,390,768,1024,1440]
output=Path('/workspace/work/parsecove-ad-qa');output.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];external=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('http://127.0.0.1:3000','http://127.0.0.1:3001','blob:','data:')) else None)
 checked=0
 for width in widths:
  page.set_viewport_size({'width':width,'height':1000})
  for route in routes:
   baseline=None
   for port in [3000,3001]:
    assert page.goto(f'http://127.0.0.1:{port}'+route).status==200
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route,port)
    area=page.locator('#tools' if route=='/' else '.workbench')
    bounds=area.bounding_box()
    if port==3000:
     expect(page.locator('[data-ad-slot]')).to_have_count(0)
     baseline=bounds
    else:
     expect(page.locator('[data-ad-slot]')).to_have_count(1)
     ad=page.locator('[data-ad-slot]');expect(ad).to_be_visible()
     assert abs(bounds['y']-baseline['y'])<1 and abs(bounds['height']-baseline['height'])<1,(width,route,'work area changed')
     adbox=ad.bounding_box();assert adbox['y']>=bounds['y']+bounds['height']+24,(width,route,'ad too close to work area')
     assert page.locator('.workbench [data-ad-slot], .sidebar [data-ad-slot]').count()==0
     surface=page.locator('.ad-slot__surface').bounding_box()
     expected=90 if width>=1120 else 60 if width>=900 else 100
     assert surface['height']==expected,(width,route,surface)
     after=page.locator('.principles' if route=='/' else '.learn')
     beforeY=after.bounding_box()['y']
     page.locator('.ad-slot__surface').evaluate("el=>{const n=document.createElement('div');n.textContent='Test creative';n.style.cssText='width:100%;height:100%;background:#e9eef8';el.replaceChildren(n)}")
     assert abs(after.bounding_box()['y']-beforeY)<1,(width,route,'slot population shifted content')
    checked+=1
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto('http://127.0.0.1:3001/unix-timestamp-converter/')
 config=load_config('ad-slots.json');config['placements']['tool_secondary']=True
 secondary=render_slot('tool_secondary',config,preview=True)
 page.locator('.related').evaluate('(el,markup)=>el.insertAdjacentHTML("beforebegin",markup)',secondary)
 expect(page.locator('[data-ad-slot="tool_secondary"]')).to_be_visible()
 page.set_viewport_size({'width':390,'height':900});expect(page.locator('[data-ad-slot="tool_secondary"]')).to_be_hidden()
 for route in ['/privacy/','/about/']:
  page.goto('http://127.0.0.1:3001'+route);expect(page.locator('[data-ad-slot]')).to_have_count(0)
 page.set_viewport_size({'width':1440,'height':1000});page.goto('http://127.0.0.1:3001/base64/');page.screenshot(path=str(output/'desktop-preview.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':900});page.goto('http://127.0.0.1:3001/base64-to-image/');page.screenshot(path=str(output/'mobile-preview.png'),full_page=True)
 page.goto('http://127.0.0.1:3000/base64/');expect(page.locator('#b64-output')).to_have_value('Hello, world!')
 assert not errors,errors
 assert not external,external
 result={'page_viewport_checks':checked,'widths':widths,'ad_requests':0,'external_requests':external,'page_errors':errors,'disabled_slots':0,'preview_slot_population_shift_px':0}
 (output/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));browser.close()

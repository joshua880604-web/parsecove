"""End-to-end conversion results, exact bytes, safe output and discoverability."""
import json,os,re
from pathlib import Path
from urllib.parse import urlparse,urljoin,unquote
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright,expect
BASE=os.environ.get('PARSECOVE_TEST_URL','http://127.0.0.1:3000').rstrip('/')
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/workspace/work/parsecove-new-tools-qa');OUT.mkdir(exist_ok=True,parents=True)
ROUTES=['/hex-to-rgb/','/json-unescape/','/hex-to-text/']
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'],accept_downloads=True)
 page=context.new_page();errors=[];external=[];mutations=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:requests.append(r.url))
 page.on('request',lambda r:external.append(r.url) if not r.url.startswith((BASE,'blob:','data:')) else None)
 page.on('request',lambda r:mutations.append(r.url) if r.method!='GET' else None)
 page.goto(BASE+'/');expect(page.locator('.tools-grid .tool-card')).to_have_count(10)
 assert not any('/assets/new-tools.js' in u or '/assets/conversion-core.js' in u for u in requests)
 for route in ROUTES:expect(page.locator('.tools-grid a[href="'+route+'"]').first).to_be_visible()
 page.goto(BASE+ROUTES[0]);expect(page.locator('#color-note')).to_contain_text('Add an alpha')
 expect(page.locator('#color-rgb-output')).to_have_value('rgb(36, 76, 218)')
 page.locator('[data-copy="color-rgb-output"]').click();assert page.evaluate('navigator.clipboard.readText()')=='rgb(36, 76, 218)'
 for raw,hex_value,rgb in [('#abc','#AABBCC','rgb(170, 187, 204)'),('#0f08','#00FF0088','rgba(0, 255, 0, 0.533333)'),('#33669980','#33669980','rgba(51, 102, 153, 0.501961)')]:
  page.locator('#color-input').fill(raw);expect(page.locator('#color-hex-output')).to_have_value(hex_value);expect(page.locator('#color-rgb-output')).to_have_value(rgb)
 page.locator('#color-modes [data-mode=rgb]').click()
 for key,value in [('r','51'),('g','102'),('b','153'),('a','0.5')]:page.locator('#color-'+key).fill(value)
 expect(page.locator('#color-hex-output')).to_have_value('#33669980');expect(page.locator('#color-note')).to_contain_text('rounded')
 page.locator('#color-r').fill('256');expect(page.locator('#color-error')).to_be_visible();expect(page.locator('#color-rgb-output')).to_have_value('');expect(page.locator('[data-copy="color-rgb-output"]')).to_be_disabled()
 page.locator('[data-color-example="#244cda"]').click();expect(page.locator('#color-rgb-output')).to_have_value('rgb(36, 76, 218)')
 page.locator('#color-input').fill('red');expect(page.locator('#color-error')).to_be_visible();expect(page.locator('#color-hex-output')).to_have_value('')
 expect(page.locator('#color-fill')).to_have_css('background-color','rgba(0, 0, 0, 0)')
 page.locator('#color-clear').click();expect(page.locator('#color-error')).to_be_hidden()
 page.goto(BASE+ROUTES[1]);expect(page.locator('#json-stats')).to_contain_text('one layer decoded')
 expect(page.locator('#json-output')).to_have_value('Hello\nworld!')
 page.locator('[data-copy="json-copy"]').click();assert page.evaluate('navigator.clipboard.readText()')=='Hello\nworld!'
 page.locator('[data-json-example=double]').click();expect(page.locator('#json-output')).to_have_value(json.dumps('{"ok":true}'));expect(page.locator('#json-next-layer')).to_be_visible()
 page.locator('#json-next-layer').click();expect(page.locator('#json-output')).to_have_value('{"ok":true}');expect(page.locator('#json-next-layer')).to_be_hidden()
 page.locator('[data-json-example=content]').click();expect(page.locator('#json-output')).to_have_value('Line 1\nLine 2\t"quoted"')
 page.locator('#json-input-kind').select_option('literal')
 for raw in ['{}','[]','null','"\\x41"','"\\ud800"']:
  page.locator('#json-input').fill(raw);page.locator('#json-convert').click();expect(page.locator('#json-error')).to_be_visible();expect(page.locator('#json-output')).to_have_value('');expect(page.locator('#json-download')).to_be_disabled()
 payload='<img src="https://example.invalid/leak" onerror="alert(1)">'
 page.locator('#json-input').fill(json.dumps(payload));page.locator('#json-convert').click();expect(page.locator('#json-output')).to_have_value(payload);expect(page.locator('img')).to_have_count(0)
 page.locator('[data-json-example=empty]').click();expect(page.locator('#json-stats')).to_contain_text('valid empty string');expect(page.locator('[data-copy="json-copy"]')).to_be_disabled()
 with page.expect_download() as d:page.locator('#json-download').click()
 assert Path(d.value.path()).read_bytes()==b''
 page.locator('#json-modes [data-mode=escape]').click();expect(page.locator('#json-output')).to_have_value('""')
 page.locator('#json-input').fill('a"b\\c\nd');page.locator('#json-convert').click();expect(page.locator('#json-output')).to_have_value(json.dumps('a"b\\c\nd',ensure_ascii=False))
 page.locator('#json-wrap').uncheck();expect(page.locator('#json-output')).to_have_value(json.dumps('a"b\\c\nd')[1:-1])
 page.locator('#json-modes [data-mode=unescape]').click();expect(page.locator('#json-input-kind')).to_have_value('content');expect(page.locator('#json-output')).to_have_value('a"b\\c\nd')
 # Textarea display normalizes CRLF. Copy/download must retain the actual decoded characters.
 page.locator('#json-input-kind').select_option('literal');page.locator('#json-input').fill(r'"A\r\nB\u0000"');page.locator('#json-convert').click()
 page.evaluate('navigator.clipboard.writeText=async value=>{window.__copied=value;}')
 page.locator('[data-copy="json-copy"]').click();assert page.evaluate('window.__copied')=='A\r\nB\0'
 with page.expect_download() as d:page.locator('#json-download').click()
 assert Path(d.value.path()).read_bytes()==b'A\r\nB\0'
 page.locator('#json-clear').click();expect(page.locator('#json-output')).to_have_value('');expect(page.locator('#json-download')).to_be_disabled()
 page.goto(BASE+ROUTES[2]);expect(page.locator('#hex-stats')).to_contain_text('5 bytes');expect(page.locator('#hex-output')).to_have_value('Hello')
 page.locator('[data-copy="hex-copy"]').click();assert page.evaluate('navigator.clipboard.readText()')=='Hello'
 page.locator('[data-hex-example=unicode]').click();expect(page.locator('#hex-output')).to_have_value('中文 👋')
 page.locator('#hex-modes [data-mode=encode]').click();expect(page.locator('#hex-output')).to_have_value('e4 b8 ad e6 96 87 20 f0 9f 91 8b')
 page.locator('#hex-uppercase').check();page.locator('#hex-spaced').uncheck();expect(page.locator('#hex-output')).to_have_value('E4B8ADE6968720F09F918B')
 page.locator('#hex-modes [data-mode=decode]').click();expect(page.locator('#hex-output')).to_have_value('中文 👋')
 page.locator('[data-hex-example=binary]').click();expect(page.locator('#hex-output')).to_have_value('');expect(page.locator('#hex-note')).to_be_visible();expect(page.locator('#hex-normalized')).to_have_value('FBFFEF')
 expect(page.locator('#hex-download')).to_be_disabled();expect(page.locator('[data-copy="hex-copy"]')).to_be_disabled()
 with page.expect_download() as d:page.locator('#hex-bytes-download').click()
 assert Path(d.value.path()).read_bytes()==bytes.fromhex('fbffef')
 page.locator('#hex-input').fill('4 8');page.locator('#hex-convert').click();expect(page.locator('#hex-error')).to_be_visible();expect(page.locator('#hex-normalized')).to_have_value('');expect(page.locator('#hex-note')).to_be_hidden();expect(page.locator('#hex-bytes-download')).to_be_disabled()
 raw=bytes.fromhex('efbbbf410d0a4200');page.locator('#hex-input').fill(raw.hex());page.locator('#hex-convert').click()
 expect(page.locator('#hex-error')).to_be_hidden()
 page.evaluate('navigator.clipboard.writeText=async value=>{window.__copied=value;}');page.locator('[data-copy="hex-copy"]').click()
 assert page.evaluate('window.__copied')=='\ufeffA\r\nB\0'
 with page.expect_download() as d:page.locator('#hex-download').click()
 assert Path(d.value.path()).read_bytes()==raw
 page.locator('#hex-clear').click();page.locator('#hex-convert').click();expect(page.locator('#hex-stats')).to_contain_text('empty string')
 with page.expect_download() as d:page.locator('#hex-bytes-download').click()
 assert Path(d.value.path()).read_bytes()==b''
 page.locator('.search-trigger').click();page.locator('#global-search').fill('hex')
 found=page.locator('#search-list a:visible').evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))')
 assert '/hex-to-text/' in found and '/hex-to-rgb/' in found
 page.locator('#search-close').click()
 checks=0
 for width in [320,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':1000})
  for route in ROUTES:
   page.goto(BASE+route)
   ready={'/hex-to-rgb/':'#color-note','/json-unescape/':'#json-stats','/hex-to-text/':'#hex-stats'}[route]
   expect(page.locator(ready)).not_to_be_empty()
   if route=='/hex-to-rgb/':page.locator('[data-color-example="#33669980"]').click()
   elif route=='/json-unescape/':page.locator('[data-json-example=double]').click()
   else:page.locator('[data-hex-example=binary]').click()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route)
   expect(page.locator('h1')).to_have_count(1)
   expect(page.locator('link[rel=canonical]')).to_have_attribute('href','https://parsecove.com'+route)
   schema=json.loads(page.locator('script[type="application/ld+json"]').inner_text());assert schema['@type']=='WebApplication'
   expect(page.locator('[data-ad-slot]')).to_have_count(0)
   if width in [390,1440]:
    page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/(route.strip('/')+'-'+str(width)+'.png')),full_page=True,style='.skip:not(:focus){visibility:hidden}')
   if route=='/hex-to-rgb/':
    page.locator('#color-modes [data-mode=rgb]').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   checks+=1
 static=browser.new_context(java_script_enabled=False);nojs=static.new_page()
 for route in ROUTES:
  nojs.goto(BASE+route);expect(nojs.locator('.learn')).to_be_visible();assert nojs.locator('.faq details').count()>=5
 static.close()
 class Doc(HTMLParser):
  def __init__(self):super().__init__();self.links=[];self.ids=[]
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if 'id' in a:self.ids.append(a['id'])
   if tag=='a' and 'href' in a:self.links.append(a['href'])
 docs={}
 for f in (ROOT/'dist').rglob('*.html'):
  doc=Doc();doc.feed(f.read_text());assert len(doc.ids)==len(set(doc.ids)),f;docs[f]=doc
 link_checks=0
 for f,doc in docs.items():
  route='/'+str(f.relative_to(ROOT/'dist')).replace('index.html','')
  for href in doc.links:
   u=urlparse(urljoin('https://parsecove.com'+route,href))
   if u.scheme not in ['http','https'] or u.netloc!='parsecove.com':continue
   target=ROOT/'dist'/u.path.lstrip('/')
   if target.is_dir():target/='index.html'
   assert target.exists(),(f,href)
   if u.fragment and target in docs:assert unquote(u.fragment) in docs[target].ids,(f,href)
   link_checks+=1
 urls=[n.text for n in ET.parse(ROOT/'dist/sitemap.xml').findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
 assert len(urls)==len(set(urls))==18 and len(docs)==19
 for route in ROUTES:assert 'https://parsecove.com'+route in urls
 assert not errors,errors
 assert not external,external
 assert not mutations,mutations
 report={'new_routes':ROUTES,'color_alpha_and_validation':'passed','JSON_formats_empty_and_layers':'passed','HEX_binary_and_UTF8':'passed','exact_CRLF_BOM_NUL_copy_and_download':'passed','clipboard_and_downloads':'passed','safe_text_output':'passed','lazy_module_loading':'passed','static_content_and_metadata':'passed','responsive_checks':checks,'internal_link_checks':link_checks,'sitemap_urls':18,'html_files':19,'page_errors':errors,'external_requests':external,'input_upload_requests':mutations}
 (OUT/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));browser.close()

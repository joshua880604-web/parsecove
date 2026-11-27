"""Data tool flows, exact file/clipboard bytes, local requests and static discovery."""
import json, os
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright, expect
BASE=os.environ.get('PARSECOVE_TEST_URL','http://127.0.0.1:3000').rstrip('/')
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/workspace/work/parsecove-data-tools-qa');OUT.mkdir(parents=True,exist_ok=True)
ROUTES=['/yaml-to-json/','/csv-to-json/']
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'],accept_downloads=True)
 page=context.new_page();errors=[];external=[];mutations=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:requests.append(r.url))
 page.on('request',lambda r:external.append(r.url) if not r.url.startswith((BASE,'blob:','data:')) else None)
 page.on('request',lambda r:mutations.append(r.url) if r.method!='GET' else None)
 def run(value):
  page.locator('#data-input').fill(value);page.locator('#data-convert').click()
 def output():return page.locator('#data-output').input_value()
 def exact():return page.locator('#data-copy').text_content()
 def download():
  with page.expect_download() as d:page.locator('#data-download').click()
  return Path(d.value.path()).read_bytes(),d.value.suggested_filename
 page.goto(BASE+'/');expect(page.locator('.tools-grid .tool-card')).to_have_count(15)
 assert not any('/assets/vendor/' in u or '/assets/data-tools.js' in u for u in requests)
 for route in ROUTES:expect(page.locator('.tools-grid a[href="'+route+'"]').first).to_be_visible()
 page.locator('#tool-filter').fill('YAML');expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(1)
 before=len(requests);page.goto(BASE+ROUTES[0]);expect(page.locator('#data-status')).to_contain_text('YAML 1.2')
 assert json.loads(output())['owner']['id']=='001'
 current=requests[before:];assert any('/vendor/yaml.js' in u for u in current) and not any('/vendor/papaparse.js' in u for u in current)
 page.locator('[data-copy=data-copy]').click();assert json.loads(page.evaluate('navigator.clipboard.readText()'))['ready'] is True
 page.locator('[data-data-example=types]').click();assert json.loads(output())=={'enabled':True,'answer':'yes','id':'001','date':'2026-11-27','missing':None}
 page.locator('#data-indent').select_option('0');page.locator('#data-convert').click();expect(page.locator('#data-output')).to_have_value('{"enabled":true,"answer":"yes","id":"001","date":"2026-11-27","missing":null}')
 # Changing options clears stale output until Convert is selected again.
 page.locator('#data-indent').select_option('4');expect(page.locator('#data-download')).to_be_disabled();expect(page.locator('#data-output')).to_have_value('')
 page.locator('#data-convert').click();assert '\n    "enabled"' in output()
 page.locator('#data-modes [data-mode=reverse]').click();expect(page.locator('#data-output')).to_have_value('');assert json.loads(page.locator('#data-input').input_value())['id']=='001'
 page.locator('#data-convert').click();assert 'id: "001"' in output()
 data,filename=download();assert data==exact().encode() and filename.endswith('.yaml')
 run('{"a":1,"a":2}');expect(page.locator('#data-error')).to_contain_text('Duplicate');expect(page.locator('#data-download')).to_be_disabled()
 page.locator('[data-data-example=aliases]').click();assert json.loads(output())=={'primary':['blue','green'],'secondary':['blue','green']}
 for raw in ['a: 1\na: 2','a: &a [*a]','a: .nan','a: 9007199254740993','a: 1\n---\nb: 2']:
  run(raw);expect(page.locator('#data-error')).to_be_visible();assert output()=='';expect(page.locator('[data-copy=data-copy]')).to_be_disabled()
 page.locator('#data-file').set_input_files({'name':'config.yaml','mimeType':'text/yaml','buffer':b'\xef\xbb\xbfid: "001"\nready: true'})
 expect(page.locator('#data-file-note')).to_contain_text('read locally');assert json.loads(output())=={'id':'001','ready':True}
 page.locator('#data-file').set_input_files({'name':'input.json','mimeType':'application/json','buffer':b'{"text":"A\\r\\nB\\u0000"}'})
 expect(page.locator('#data-modes [data-mode=reverse]')).to_have_attribute('aria-pressed','true');expect(page.locator('#data-status')).to_contain_text('String values')
 assert download()[0]==exact().encode()
 page.locator('#data-file').set_input_files({'name':'bad.yaml','mimeType':'text/yaml','buffer':b'\xff\xfeA'})
 expect(page.locator('#data-error')).to_contain_text('UTF-8');expect(page.locator('#data-download')).to_be_disabled()
 page.locator('#data-file').set_input_files({'name':'big.txt','mimeType':'text/plain','buffer':b'x'*2_000_001})
 expect(page.locator('#data-error')).to_contain_text('2 MB')
 # A late file read cannot undo a newer Clear action.
 page.evaluate('''()=>{window.__arrayBuffer=File.prototype.arrayBuffer;File.prototype.arrayBuffer=function(){return new Promise(resolve=>{window.__finishRead=()=>window.__arrayBuffer.call(this).then(resolve);});};}''')
 page.locator('#data-file').set_input_files({'name':'late.yaml','mimeType':'text/yaml','buffer':b'old: true'})
 expect(page.locator('#data-file-note')).to_contain_text('Reading');page.locator('#data-clear').click();page.evaluate('window.__finishRead()');page.wait_for_timeout(100)
 assert page.locator('#data-input').input_value()=='' and output()==''
 page.evaluate('()=>{File.prototype.arrayBuffer=window.__arrayBuffer;}')
 page.locator('[data-data-example=basic]').click();page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/'yaml-desktop.png'))
 before=len(requests);page.goto(BASE+ROUTES[1]);expect(page.locator('#data-status')).to_contain_text('All cell values remain strings')
 current=requests[before:];assert any('/vendor/papaparse.js' in u for u in current) and not any('/vendor/yaml.js' in u for u in current)
 assert json.loads(output())[0]=={'id':'001','name':'Ada','active':'true'}
 page.locator('#data-infer').check();assert output()=='';page.locator('#data-convert').click();assert json.loads(output())[0]['active'] is True
 page.locator('[data-data-example=quoted]').click();assert json.loads(output())[0]['note']=='A "quoted" word';assert json.loads(output())[1]['note']=='Line one\nLine two'
 page.locator('[data-data-example=tab]').click();expect(page.locator('#data-delimiter')).to_have_value('tab');assert json.loads(output())[0]['id']=='001'
 page.locator('[data-data-example=basic]').click();page.locator('#data-headers').uncheck();page.locator('#data-convert').click();assert json.loads(output())[0]==['id','name','active']
 page.locator('#data-headers').check();page.locator('#data-delimiter').select_option(',')
 for raw in ['a,a\n1,2','a,b\n1','a,b\nx"q,y','a,b\n"x"oops,y']:
  run(raw);expect(page.locator('#data-error')).to_be_visible();expect(page.locator('#data-download')).to_be_disabled()
 page.locator('[data-data-example=json]').click();assert output().startswith('"id","name","active"')
 # Exact CRLF output must survive textarea display normalization in copy and download.
 assert '\r\n' in exact();page.evaluate('navigator.clipboard.writeText=async value=>{window.__copied=value;}')
 page.locator('[data-copy=data-copy]').click();assert page.evaluate('window.__copied')==exact()
 assert download()[0]==exact().encode()
 page.locator('#data-newline').select_option('lf');page.locator('#data-convert').click();assert '\r\n' not in exact()
 run('[{"id":"001","note":"=SUM(A1)","number":-12,"textNumber":"-12"}]');expect(page.locator('#data-status')).to_contain_text('2 string cells');assert "'=SUM(A1)" in output()
 page.locator('#data-protect').uncheck();page.locator('#data-convert').click();assert "'=SUM" not in output();expect(page.locator('#data-status')).to_contain_text('protection is off')
 run('[{"v":{"nested":true}}]');expect(page.locator('#data-error')).to_contain_text('Nested')
 page.locator('#data-nested').check();page.locator('#data-convert').click();assert '{""nested"":true}' in output()
 run('[]');expect(page.locator('#data-download')).to_be_enabled();expect(page.locator('[data-copy=data-copy]')).to_be_disabled();assert download()[0]==b''
 # Keep CRLF inside quoted cells when reading a file, even though the editor displays LF.
 page.locator('#data-file').set_input_files({'name':'rows.csv','mimeType':'text/csv','buffer':b'id,note\r\n001,"one\r\ntwo"\r\n'})
 expect(page.locator('#data-file-note')).to_contain_text('read locally');assert json.loads(output())==[{'id':'001','note':'one\r\ntwo'}]
 page.locator('#data-file').set_input_files({'name':'rows.tsv','mimeType':'text/tab-separated-values','buffer':b'id\tname\n001\tAda'})
 expect(page.locator('#data-delimiter')).to_have_value('tab');assert json.loads(output())==[{'id':'001','name':'Ada'}]
 page.locator('#data-file').set_input_files({'name':'again.csv','mimeType':'text/csv','buffer':b'id,name\n002,Lin'})
 expect(page.locator('#data-delimiter')).to_have_value('auto');assert json.loads(output())==[{'id':'002','name':'Lin'}]
 payload='<img src="https://example.invalid/leak" onerror="alert(1)">'
 page.locator('#data-file').set_input_files({'name':'safe.json','mimeType':'application/json','buffer':json.dumps([{'text':payload}]).encode()})
 expect(page.locator('#data-file-note')).to_contain_text('read locally');assert '<img' in output();expect(page.locator('.data-workbench img')).to_have_count(0)
 page.locator('[data-data-example=basic]').click();page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/'csv-desktop.png'))
 responsive=0
 for width in [320,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':1000})
  for route in ROUTES:
   page.goto(BASE+route);expect(page.locator('#data-download')).to_be_enabled()
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route,'overflow')
   for direction in ['forward','reverse']:
    if direction=='reverse':page.locator('[data-data-example=json]').click()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route,direction)
    assert page.locator('h1').count()==1
    responsive+=1
   if width==390:
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(route.strip('/')+'-mobile.png')))
 page.set_viewport_size({'width':1440,'height':1000});page.goto(BASE+'/json-unescape/')
 expect(page.locator('.task-guide a[href="/yaml-to-json/"]')).to_be_visible()
 page.locator('.search-trigger').click();page.locator('#global-search').fill('CSV');expect(page.locator('#search-list a[href="/csv-to-json/"]')).to_be_visible()
 assert not errors and not external and not mutations,(errors,external,mutations)
 static_context=browser.new_context(java_script_enabled=False);static=static_context.new_page()
 for route in ROUTES:
  assert static.goto(BASE+route).status==200
  expect(static.locator('h1')).to_have_count(1);expect(static.locator('.faq details')).to_have_count(6)
  expect(static.locator('link[rel=canonical]')).to_have_attribute('href','https://parsecove.com'+route)
  assert 'converter' in static.locator('h1').inner_text().lower()
  schema=json.loads(static.locator('script[type="application/ld+json"]').text_content());assert schema['@type']=='WebApplication' and schema['url']=='https://parsecove.com'+route
 static_context.close();browser.close()

class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.add(a['id'])
  if tag=='a' and a.get('href'):self.links.append(a['href'])
dist=ROOT/'dist';docs={str(p.relative_to(dist)):Links() for p in dist.rglob('*.html')}
for file,parser in docs.items():parser.feed((dist/file).read_text())
checks=0
for file,parser in docs.items():
 origin='https://parsecove.com/'+file.removesuffix('index.html')
 for href in parser.links:
  link=urlparse(urljoin(origin,href))
  if link.netloc!='parsecove.com':continue
  key=unquote(link.path.lstrip('/'));key=key+'index.html' if key.endswith('/') or not key else key
  if key in docs:
   if link.fragment:assert unquote(link.fragment) in docs[key].ids,(file,href,'fragment')
  else:assert (dist/key).is_file(),(file,href,'missing')
  checks+=1
urls=[el.text for el in ET.parse(dist/'sitemap.xml').findall('.//{*}loc')]
assert len(urls)==len(set(urls))==25 and len(docs)==26
for route in ROUTES:assert 'https://parsecove.com'+route in urls
report={'new_routes':ROUTES,'YAML_round_trips_and_validation':'passed','CSV_modes_types_headers_quoting':'passed','local_UTF8_files_and_limits':'passed','exact_CRLF_copy_download_and_file_cells':'passed','stale_file_read_cancellation':'passed','safe_text_output':'passed','per_route_local_vendor_loading':'passed','no_JavaScript_metadata_content':'passed','responsive_checks':responsive,'internal_link_checks':checks,'sitemap_urls':len(urls),'html_files':len(docs),'page_errors':errors,'external_requests':external,'input_upload_requests':mutations}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

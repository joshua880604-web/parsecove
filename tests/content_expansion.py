"""Dedicated RGBA behavior, actual guide fixtures/code and task-specific internal navigation."""
import json,os,subprocess
from pathlib import Path
from urllib.parse import urlparse,urljoin,unquote
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright,expect
BASE=os.environ.get('PARSECOVE_TEST_URL','http://127.0.0.1:3000').rstrip('/')
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/workspace/work/parsecove-content-expansion-qa');OUT.mkdir(parents=True,exist_ok=True)
ROUTES=['/hex-to-rgba/','/guides/yaml-vs-json/','/guides/json-double-encoding/']
FIXTURES=json.loads((ROOT/'guide-fixtures.json').read_text())
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'],accept_downloads=True)
 page=context.new_page();errors=[];requests=[];external=[];mutations=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.on('request',lambda r:external.append(r.url) if not r.url.startswith((BASE,'blob:','data:')) else None)
 page.on('request',lambda r:mutations.append(r.url) if r.method!='GET' else None)
 page.goto(BASE+'/');expect(page.locator('.tools-grid .tool-card')).to_have_count(15);expect(page.locator('.tool-group-heading:visible')).to_have_count(4)
 expect(page.locator('.guides-preview .guide-card')).to_have_count(6)
 page.locator('#tool-filter').fill('image');expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(2);expect(page.locator('.tool-group-heading:visible')).to_have_count(1)
 page.locator('#tool-filter').fill('no-such-tool');expect(page.locator('.tool-group-heading:visible')).to_have_count(0);expect(page.locator('#filter-empty')).to_be_visible()
 page.locator('#tool-filter').fill('');expect(page.locator('.tool-group-heading:visible')).to_have_count(4)
 assert not any('/assets/vendor/' in u or '/assets/rgba-tool.js' in u or '/assets/format-guides.js' in u for u in requests)
 before=len(requests);page.goto(BASE+ROUTES[0]);expect(page.locator('#rgba-output')).to_have_value('rgba(36, 76, 218, 0.5)')
 assert not any('/assets/vendor/' in u for u in requests[before:])
 expect(page.locator('#rgba-hex-output')).to_have_value('#244CDA80');expect(page.locator('#rgba-note')).to_contain_text('differ slightly')
 page.locator('[data-copy=rgba-output]').click();assert page.evaluate('navigator.clipboard.readText()')=='rgba(36, 76, 218, 0.5)'
 page.locator('[data-copy=rgba-css]').click();assert page.evaluate('navigator.clipboard.readText()')=='.overlay {\n  background-color: rgba(36, 76, 218, 0.5);\n}'
 page.locator('#rgba-alpha').fill('0');expect(page.locator('#rgba-output')).to_have_value('rgba(36, 76, 218, 0)');expect(page.locator('#rgba-fill')).to_have_css('background-color','rgba(36, 76, 218, 0)')
 page.locator('#rgba-input').fill('#33669980');expect(page.locator('#rgba-alpha')).to_be_disabled();expect(page.locator('#rgba-output')).to_have_value('rgba(51, 102, 153, 0.501961)');expect(page.locator('#rgba-alpha-note')).to_contain_text('128/255')
 page.locator('[data-rgba-example="#0f08"]').click();expect(page.locator('#rgba-hex-output')).to_have_value('#00FF0088')
 page.locator('[data-rgba-example="#00000000"]').click();expect(page.locator('#rgba-output')).to_have_value('rgba(0, 0, 0, 0)')
 page.locator('#rgba-input').fill('#abc');expect(page.locator('#rgba-alpha')).to_be_enabled();page.locator('#rgba-alpha').fill('1.1');expect(page.locator('#rgba-error')).to_be_visible();expect(page.locator('#rgba-output')).to_have_value('');expect(page.locator('[data-copy=rgba-output]')).to_be_disabled()
 page.locator('#rgba-alpha').fill('0.5');expect(page.locator('#rgba-output')).to_have_value('rgba(170, 187, 204, 0.5)')
 page.locator('#rgba-input').fill('<img src=x>');expect(page.locator('#rgba-error')).to_be_visible();expect(page.locator('.rgba-workbench img')).to_have_count(0)
 page.locator('#rgba-clear').click();expect(page.locator('#rgba-error')).to_be_hidden();expect(page.locator('#rgba-output')).to_have_value('')
 page.locator('[data-rgba-example="#244cda"]').click();page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/'rgba-desktop.png'))
 # The pre-existing converter retains its byte-aligned result for the reverse direction.
 page.goto(BASE+'/hex-to-rgb/');page.locator('#color-modes [data-mode=rgb]').click();page.locator('#color-a').fill('0.5');expect(page.locator('#color-rgb-output')).to_have_value('rgba(36, 76, 218, 0.501961)')
 expect(page.locator('.task-guide a[href="/hex-to-rgba/"]')).to_be_visible()
 for kind,route in [('yaml',ROUTES[1]),('json',ROUTES[2])]:
  before=len(requests);page.goto(BASE+route);expect(page.locator('#format-status')).not_to_be_empty();expect(page.locator('#format-error')).to_be_hidden()
  assert any('/vendor/jsonc-parser.js' in u for u in requests[before:])
  assert not any('/vendor/papaparse.js' in u for u in requests[before:])
  if kind=='json':assert not any('/vendor/yaml.js' in u for u in requests[before:])
  for c in FIXTURES[kind]:
   page.locator('#format-case').select_option(c['id'])
   if c.get('error'):
    expect(page.locator('#format-error')).to_be_visible();expect(page.locator('#format-output')).to_have_value('');expect(page.locator('[data-copy=format-copy]')).to_be_disabled()
   else:
    expect(page.locator('#format-error')).to_be_hidden();raw=page.locator('#format-copy').text_content()
    if kind=='yaml':assert json.loads(raw)==c['expected'],c['id']
    else:
     assert 'After one parse: '+c['expected_kind'] in page.locator('#format-status').inner_text()
     expected=json.loads(c['input']);assert raw==expected if isinstance(expected,str) else json.loads(raw)==expected
    page.locator('[data-copy=format-copy]').click();assert page.evaluate('navigator.clipboard.readText()')==raw
  page.locator('#format-reset').click();expect(page.locator('#format-error')).to_be_hidden();page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(kind+'-guide-desktop.png')))
 # Execute exact code published in the JSON guide.
 snippets={}
 for selector,command,expected in [('#json-layer-js',['node','--input-type=module','-'],['string','object','001']),('#json-layer-python',['python3','-'],['str','dict','001']),('#json-layer-field',['node','--input-type=module','-'],['001','string'])]:
  code=page.locator(selector).inner_text();r=subprocess.run(command,input=code,text=True,capture_output=True,check=True,cwd=ROOT);assert r.stdout.splitlines()==expected,(selector,r.stdout);snippets[selector]=r.stdout.splitlines()
 (OUT/'published-code-results.json').write_text(json.dumps(snippets,indent=2)+'\n')
 # The published source example must contain actual escaped quotes, not a broken display.
 assert page.locator('#four-states code').nth(1).inner_text()=='"{\\"id\\":\\"001\\"}"'
 # Run the precise nested-cell example advertised by the CSV page.
 page.goto(BASE+'/csv-to-json/');expect(page.locator('#data-download')).to_be_enabled();page.locator('#data-modes [data-mode=reverse]').click()
 page.locator('#data-input').fill('[{"id":"001","customer":{"name":"Ada"},"tags":["red","blue"]}]');page.locator('#data-nested').check();page.locator('#data-convert').click()
 expected='"id","customer","tags"\r\n"001","{""name"":""Ada""}","[""red"",""blue""]"'
 assert page.locator('#data-copy').text_content()==expected
 assert page.locator('#nested-json-cells pre code').nth(1).inner_text()==expected.replace('\r\n','\n')
 # One to four relevant recommendations, complete directory elsewhere, no self-recommendations.
 tool_routes=['/'+s+'/' for s in ['unix-timestamp-converter','px-to-rem','rem-to-px','base64','base64url-decode','base64-to-image','image-to-base64','hex-to-rgb','hex-to-rgba','json-unescape','hex-to-text','yaml-to-json','csv-to-json','json-minify','json-compare']]
 curated=0
 for route in tool_routes:
  page.goto(BASE+route);links=page.locator('.related .tool-card');assert 3<=links.count()<=4
  assert route not in links.evaluate_all('(els)=>els.map(x=>x.getAttribute("href"))');curated+=links.count()
 responsive=0
 for width in [320,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':1000})
  for route in ROUTES+['/','/csv-to-json/','/yaml-to-json/']:
   page.goto(BASE+route)
   if route in ROUTES[1:]:expect(page.locator('#format-status')).not_to_be_empty()
   if route=='/hex-to-rgba/':expect(page.locator('#rgba-output')).not_to_be_empty()
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,route,'overflow')
   assert page.locator('h1').count()==1
   if route in ROUTES and width==390:page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(route.strip('/').replace('/','-')+'-mobile.png')))
   responsive+=1
 nojs=browser.new_context(java_script_enabled=False);static=nojs.new_page()
 for route in ROUTES:
  assert static.goto(BASE+route).status==200
  expect(static.locator('link[rel=canonical]')).to_have_attribute('href','https://parsecove.com'+route)
  schema=json.loads(static.locator('script[type="application/ld+json"]').text_content())
  if '/guides/' in route:
   article=next(x for x in schema['@graph'] if x['@type']=='TechArticle');assert article['datePublished']=='2026-11-27'
   expect(static.locator('.guide-byline')).to_be_visible();expect(static.locator('#format-output')).not_to_be_empty();expect(static.locator('#format-faq details')).to_have_count(4)
  else:assert any(x['@type']=='WebApplication' for x in schema['@graph']);expect(static.locator('#rgba-output')).to_have_value('rgba(36, 76, 218, 0.5)')
 nojs.close();assert not errors and not external and not mutations,(errors,external,mutations)
 browser.close()
class Doc(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):assert a['id'] not in self.ids,a['id'];self.ids.add(a['id'])
  if tag=='a' and a.get('href'):self.links.append(a['href'])
dist=ROOT/'dist';docs={str(p.relative_to(dist)):Doc() for p in dist.rglob('*.html')}
for f,p in docs.items():p.feed((dist/f).read_text())
links=0
for f,p in docs.items():
 origin='https://parsecove.com/'+f.removesuffix('index.html')
 for href in p.links:
  u=urlparse(urljoin(origin,href))
  if u.netloc!='parsecove.com':continue
  key=unquote(u.path.lstrip('/'));key=key+'index.html' if key.endswith('/') or not key else key
  if key in docs:
   if u.fragment:assert unquote(u.fragment) in docs[key].ids,(f,href)
  else:assert (dist/key).is_file(),(f,href)
  links+=1
urls=[x.text for x in ET.parse(dist/'sitemap.xml').findall('.//{*}loc')];assert len(urls)==len(set(urls))==25 and len(docs)==26
assert all('https://parsecove.com'+r in urls for r in ROUTES)
report={'new_routes':ROUTES,'RGBA_exact_opacity_and_HEX_rounding':'passed','existing_RGB_semantics':'passed','YAML_live_parser_cases':len(FIXTURES['yaml']),'JSON_one_layer_cases':len(FIXTURES['json']),'published_code_snippets':len(snippets),'published_nested_CSV_example':'passed','exact_copy_and_invalid_clearing':'passed','home_groups_and_search':'passed','curated_recommendation_links':curated,'responsive_checks':responsive,'static_content_and_metadata':'passed','internal_link_checks':links,'sitemap_urls':len(urls),'html_files':len(docs),'page_errors':errors,'external_requests':external,'input_upload_requests':mutations}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

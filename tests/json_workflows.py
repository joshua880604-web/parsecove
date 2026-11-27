"""Browser acceptance checks for exact JSON layout/diff and CSV JSON Lines output."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import json, os, xml.etree.ElementTree as ET

BASE=os.environ.get('PARSECOVE_TEST_URL','http://127.0.0.1:3012').rstrip('/')
OUT=Path('/workspace/work/parsecove-json-workflows-qa');OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'],accept_downloads=True)
 page=context.new_page();errors=[];external=[];uploads=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def request(r):
  requests.append(r.url)
  if not r.url.startswith((BASE,'blob:','data:')):external.append(r.url)
  if r.method not in ['GET','HEAD']:uploads.append(r.url)
 page.on('request',request)
 def download(selector):
  with page.expect_download() as pending:page.locator(selector).click()
  item=pending.value;path=OUT/item.suggested_filename;item.save_as(path)
  return item.suggested_filename,path.read_bytes()
 def report():return json.loads(page.locator('#compare-report').text_content())
 page.goto(BASE+'/');expect(page.locator('.tools-grid .tool-card')).to_have_count(15)
 assert not any('json-document.js' in r or 'json-workflows.js' in r for r in requests)
 page.locator('#tool-filter').fill('minify');expect(page.locator('.tools-grid .tool-card:visible')).to_have_count(1)
 page.locator('.tools-grid a[href="/json-minify/"]').click()
 expect(page.locator('#json-status')).to_contain_text('Minified valid JSON')
 value=page.locator('#json-output').input_value();assert '9007199254740993' in value and '1e+30' in value
 assert 'keep  two spaces' in value
 page.locator('[data-copy="json-output"]').click();assert page.evaluate('navigator.clipboard.readText()')==value
 name,data=download('#json-download');assert name=='parsecove-minify.json' and data==value.encode()
 page.locator('#json-input').fill(' { "text": "中文 😀", "a": -0, "b": 1.2300e500 } ')
 expect(page.locator('#json-output')).to_have_value('');expect(page.locator('#json-download')).to_be_disabled()
 page.locator('#json-run').click();value=page.locator('#json-output').input_value()
 assert value=='{"text":"中文 😀","a":-0,"b":1.2300e500}'
 assert page.locator('#json-input-bytes').inner_text()==str(len(page.locator('#json-input').input_value().encode()))+' B'
 assert page.locator('#json-output-bytes').inner_text()==str(len(value.encode()))+' B'
 page.locator('#json-modes [data-mode="format"]').click();expect(page.locator('#json-output')).to_have_value('')
 page.locator('#json-indent').select_option('4');page.locator('#json-run').click()
 assert '\n    "text"' in page.locator('#json-output').input_value()
 page.locator('#json-modes [data-mode="validate"]').click();page.locator('#json-run').click()
 assert page.locator('#json-output').input_value()==page.locator('#json-input').input_value()
 page.locator('[data-json-example="invalid"]').click();expect(page.locator('#json-error')).to_contain_text('Duplicate JSON key')
 expect(page.locator('#json-output')).to_have_value('');expect(page.locator('[data-copy="json-output"]')).to_be_disabled()
 page.locator('#json-modes [data-mode="minify"]').click()
 page.locator('#json-file').set_input_files({'name':'precise.json','mimeType':'application/json','buffer':b'\xef\xbb\xbf { "n": 9007199254740993 } '})
 expect(page.locator('#json-output')).to_have_value('{"n":9007199254740993}')
 page.locator('#json-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'\xff'})
 expect(page.locator('#json-error')).to_contain_text('valid UTF-8');expect(page.locator('#json-download')).to_be_disabled()
 page.evaluate('''() => {const original=File.prototype.arrayBuffer;File.prototype.arrayBuffer=function(){return this.name==='slow.json'?new Promise(resolve=>setTimeout(()=>original.call(this).then(resolve),500)):original.call(this);};}''')
 page.locator('#json-file').set_input_files({'name':'slow.json','mimeType':'application/json','buffer':b'{"stale":true}'})
 page.locator('#json-input').fill('{"current":true}');page.locator('#json-run').click();page.wait_for_timeout(650)
 expect(page.locator('#json-output')).to_have_value('{"current":true}')
 page.locator('#json-file').set_input_files({'name':'large.json','mimeType':'application/json','buffer':b' '*2000001})
 expect(page.locator('#json-error')).to_contain_text('2 MB');expect(page.locator('#json-output')).to_have_value('')
 page.locator('[data-json-example="basic"]').click();page.evaluate('scrollTo(0,0)')
 page.screenshot(path=str(OUT/'json-minify-desktop.png'))

 page.goto(BASE+'/json-compare/');expect(page.locator('#compare-summary')).to_have_text('4 differences found.')
 assert len(report()['differences'])==4
 page.locator('[data-compare-example="equal"]').click();expect(page.locator('#compare-summary')).to_contain_text('Same JSON values.')
 assert report()['equal'] and not report()['textIdentical'];expect(page.locator('#compare-table-wrap')).to_be_hidden()
 page.locator('[data-compare-example="precision"]').click()
 assert [d['path'] for d in report()['differences']]==['/decimal','/id']
 assert report()['differences'][1]['after']['json']=='9007199254740993'
 page.locator('[data-compare-example="paths"]').click()
 assert [d['path'] for d in report()['differences']]==['/','/a~1b/~0key','/note','/type']
 expected=page.locator('#compare-report').text_content();page.locator('[data-copy="compare-report"]').click()
 assert page.evaluate('navigator.clipboard.readText()')==expected
 name,data=download('#compare-download');assert name=='parsecove-json-comparison.json' and data.decode()==expected
 page.locator('#compare-left').fill('{"a":1,"\\u0061":2}')
 expect(page.locator('#compare-report')).to_be_empty();expect(page.locator('#compare-download')).to_be_disabled()
 page.locator('#compare-run').click();expect(page.locator('#compare-error')).to_contain_text('Left document: Duplicate')
 page.locator('#compare-left').fill('null');page.locator('#compare-right').fill('{}');page.locator('#compare-run').click()
 assert report()['differences'][0]['path']=='' and report()['differences'][0]['before']['type']=='null'
 page.locator('#compare-left').fill('{}')
 payload='<img src=x onerror="globalThis.untrustedExecuted=true">'
 page.locator('#compare-right').fill(json.dumps({'html':payload}));page.locator('#compare-run').click()
 expect(page.locator('#compare-rows')).to_contain_text(json.dumps(payload))
 assert page.locator('#compare-rows img').count()==0 and not page.evaluate('globalThis.untrustedExecuted===true')
 page.locator('#compare-left').fill(json.dumps([0]*201));page.locator('#compare-right').fill(json.dumps([1]*201));page.locator('#compare-run').click()
 expect(page.locator('#compare-limit')).to_be_visible();expect(page.locator('#compare-rows tr')).to_have_count(200);assert report()['limited']
 page.locator('#compare-left-file').set_input_files({'name':'left.json','mimeType':'application/json','buffer':b'{"id":9007199254740993}'})
 page.locator('#compare-right-file').set_input_files({'name':'right.json','mimeType':'application/json','buffer':b'{"id":9007199254740992}'})
 expect(page.locator('#compare-summary')).to_have_text('1 difference found.')
 assert report()['differences'][0]['before']['json']=='9007199254740993'
 page.locator('#compare-swap').click();assert report()['differences'][0]['before']['json']=='9007199254740992'
 page.evaluate('''() => {const original=File.prototype.arrayBuffer;File.prototype.arrayBuffer=function(){return this.name==='slow.json'?new Promise(resolve=>setTimeout(()=>original.call(this).then(resolve),500)):original.call(this);};}''')
 page.locator('#compare-left-file').set_input_files({'name':'slow.json','mimeType':'application/json','buffer':b'{"stale":true}'})
 page.locator('#compare-left').fill('{"current":true}');page.locator('#compare-right').fill('{"current":true}');page.locator('#compare-run').click();page.wait_for_timeout(650)
 assert report()['equal'] and 'current' in page.locator('#compare-left').input_value()
 page.locator('#compare-right-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'\xff'})
 expect(page.locator('#compare-error')).to_contain_text('Right file:');expect(page.locator('#compare-right')).to_have_value('')
 expect(page.locator('#compare-download')).to_be_disabled()
 page.locator('[data-compare-example="basic"]').click();page.locator('.diff-results').scroll_into_view_if_needed()
 page.screenshot(path=str(OUT/'json-compare-results-desktop.png'))

 page.goto(BASE+'/csv-to-json/');expect(page.locator('#data-output')).not_to_have_value('')
 page.locator('#data-csv-format').select_option('jsonl')
 expect(page.locator('#data-download')).to_be_disabled();expect(page.locator('#data-indent')).to_be_hidden()
 csv=b'id,note\r\n001,"one\r\ntwo"\r\n002,"a ""quote"""\r\n'
 page.locator('#data-file').set_input_files({'name':'records.csv','mimeType':'text/csv','buffer':csv})
 expect(page.locator('#data-output-label')).to_have_text('JSONL RESULT')
 expect(page.locator('#data-output')).not_to_have_value('')
 value=page.locator('#data-copy').text_content()
 expected='{"id":"001","note":"one\\r\\ntwo"}\n'+json.dumps({'id':'002','note':'a "quote"'},separators=(',',':'))+'\n'
 assert value==expected,(value,expected)
 page.locator('[data-copy="data-copy"]').click();assert page.evaluate('navigator.clipboard.readText()')==expected
 name,data=download('#data-download');assert name=='parsecove-result.jsonl' and data==expected.encode()
 page.locator('#data-modes [data-mode="reverse"]').click()
 assert isinstance(json.loads(page.locator('#data-input').input_value()),list)
 page.locator('#data-convert').click();expect(page.locator('#data-error')).to_be_hidden();expect(page.locator('#data-status')).to_contain_text('2 records')
 page.locator('#data-modes [data-mode="forward"]').click()
 page.locator('#data-input').fill('id,n,flag\n001,9007199254740993,true');page.locator('#data-infer').check();page.locator('#data-convert').click()
 assert json.loads(page.locator('#data-copy').text_content())=={'id':'001','n':'9007199254740993','flag':True}
 page.locator('#data-headers').uncheck();page.locator('#data-convert').click();value=page.locator('#data-copy').text_content()
 assert json.loads(value.splitlines()[0])==['id','n','flag']
 page.locator('#data-input').fill('');page.locator('#data-convert').click();expect(page.locator('[data-copy="data-copy"]')).to_be_disabled()
 name,data=download('#data-download');assert name.endswith('.jsonl') and data==b''

 responsive=0
 for width in [320,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':900})
  for slug in ['json-minify','json-compare','csv-to-json']:
   page.goto(BASE+'/'+slug+'/')
   if slug=='json-minify':expect(page.locator('#json-status')).to_contain_text('Minified valid JSON')
   if slug=='json-compare':expect(page.locator('#compare-summary')).to_have_text('4 differences found.')
   if slug=='csv-to-json':
    page.locator('#data-csv-format').select_option('jsonl');page.locator('#data-convert').click()
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,slug)
   if width in [390,1440]:
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/f'{slug}-{width}.png'))
   if slug=='json-compare':
    page.locator('.diff-results').scroll_into_view_if_needed();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    if width==390:page.screenshot(path=str(OUT/'json-compare-results-mobile.png'))
   responsive+=1
 static=browser.new_context(java_script_enabled=False)
 sp=static.new_page()
 for slug in ['json-minify','json-compare']:
  sp.goto(BASE+'/'+slug+'/');expect(sp.locator('h1')).to_be_visible()
  expect(sp.locator('link[rel="canonical"]')).to_have_attribute('href','https://parsecove.com/'+slug+'/')
  graph=json.loads(sp.locator('script[type="application/ld+json"]').text_content())['@graph']
  assert any(entity['@type']=='WebApplication' for entity in graph)
  expect(sp.locator('.learn .faq details')).to_have_count(6)
  assert '9007199254740993' in sp.locator('main').text_content()
  assert '80 levels' in sp.locator('main').text_content()
  expect(sp.locator('#json-layout-example' if slug=='json-minify' else '#json-comparison-rules')).to_be_visible()
 static.close()
 assert any('json-document.js' in r for r in requests)
 assert not errors,errors
 assert not external,external
 assert not uploads,uploads
 browser.close()
dist=Path(__file__).resolve().parents[1]/'dist'
urls=[x.text for x in ET.parse(dist/'sitemap.xml').findall('.//{*}loc')]
assert len(urls)==len(set(urls))==25 and len(list(dist.rglob('*.html')))==26
result={'lossless_layout_and_UTF8_bytes':'passed','strict_validation_and_stale_output':'passed','exact_numeric_comparison_and_pointers':'passed','limited_reports_and_XSS_text_rendering':'passed','local_files_and_cancelled_reads':'passed','CSV_JSONL_exact_copy_download_and_reverse_handoff':'passed','responsive_checks':responsive,'sitemap_urls':len(urls),'page_errors':errors,'external_requests':external,'input_upload_requests':uploads}
(OUT/'browser-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

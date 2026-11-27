"""Static JSON-LD coverage and cross-page relationship checks against real HTML."""
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json, sys, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from structured_data import schema_script

ORIGIN='https://parsecove.com'
HOME=ORIGIN+'/'
OUT=Path('/workspace/work/parsecove-schema-qa');OUT.mkdir(exist_ok=True)

class Document(HTMLParser):
    def __init__(self):
        super().__init__();self.ld=False;self.buffer='';self.schemas=[];self.canonical=None
        self.title=False;self.page_title='';self.description=None;self.h1=False;self.heading=''
        self.card=None;self.card_heading=False;self.tools=[];self.guides=[]
        self.free_label=False;self.free_text=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script' and a.get('type')=='application/ld+json':self.ld=True;self.buffer=''
        if tag=='title':self.title=True
        if tag=='h1':self.h1=True
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a['href']
        if tag=='meta' and a.get('name')=='description':self.description=a['content']
        if tag=='span' and 'free-label' in a.get('class','').split():self.free_label=True
        if tag=='a':
            classes=a.get('class','').split()
            kind='tool' if 'tool-card' in classes else 'guide' if 'guide-card' in classes else None
            if kind:self.card={'kind':kind,'url':ORIGIN+a['href'],'name':''}
        if self.card and tag in ['h2','h3']:self.card_heading=True
    def handle_endtag(self,tag):
        if tag=='script' and self.ld:self.schemas.append(json.loads(self.buffer));self.ld=False
        if tag=='title':self.title=False
        if tag=='h1':self.h1=False
        if tag=='span':self.free_label=False
        if tag in ['h2','h3']:self.card_heading=False
        if tag=='a' and self.card:
            (self.tools if self.card['kind']=='tool' else self.guides).append(self.card);self.card=None
    def handle_data(self,value):
        if self.ld:self.buffer+=value
        if self.title:self.page_title+=value
        if self.h1:self.heading+=value
        if self.free_label:self.free_text+=value
        if self.card and self.card_heading:self.card['name']+=value

docs={}
for file in (ROOT/'dist').rglob('*.html'):
    doc=Document();doc.feed(file.read_text());docs[file.relative_to(ROOT/'dist').as_posix()]=doc
sitemap={n.text for n in ET.parse(ROOT/'dist/sitemap.xml').findall('.//{*}loc')}
indexed={key:doc for key,doc in docs.items() if doc.canonical in sitemap}
assert len(indexed)==len(sitemap)==25
assert not docs['404.html'].schemas
definitions={};counts=Counter();references=[];rows=[]
for file,doc in indexed.items():
    assert len(doc.schemas)==1,(file,'JSON-LD blocks')
    data=doc.schemas[0];assert data['@context']=='https://schema.org'
    graph=data['@graph'];local={}
    for entity in graph:
        identifier=entity['@id'];assert identifier not in local,(file,'duplicate entity',identifier)
        assert identifier.startswith(HOME),(file,'unexpected entity domain')
        local[identifier]=entity
        if identifier in definitions:assert definitions[identifier]==entity,(file,'inconsistent shared entity',identifier)
        definitions[identifier]=entity;counts[entity['@type']]+=1
    page=local[doc.canonical+'#webpage']
    assert page['url']==doc.canonical and page['name']==doc.page_title
    assert page['description']==doc.description
    assert page['isPartOf']=={'@id':HOME+'#website'}
    assert page['publisher']=={'@id':HOME+'#organization'}
    organization=local[HOME+'#organization'];site=local[HOME+'#website'];logo=local[HOME+'#logo']
    assert organization['name']==site['name']=='ParseCove'
    assert site['publisher']=={'@id':organization['@id']}
    assert organization['logo']=={'@id':logo['@id']}
    assert logo['width']==logo['height']==512
    assert logo['url']==logo['contentUrl']==ORIGIN+'/assets/parsecove-logo.svg'
    assert all(key not in organization for key in ['telephone','email','taxID','legalName','address'])
    def inspect(value):
        if isinstance(value,dict):
            assert all(key not in value for key in ['aggregateRating','review','sameAs']),(file,'unverified assertion')
            if set(value)=={'@id'}:references.append((file,value['@id']))
            for key,child in value.items():
                if key in ['url','contentUrl']:
                    target=urlsplit(child)
                    assert target.netloc=='parsecove.com',(file,'unexpected content URL',child)
                    path=target.path.lstrip('/')
                    destination=ROOT/'dist'/(path+'index.html' if target.path.endswith('/') else path)
                    assert destination.is_file(),(file,'missing URL',child)
                inspect(child)
        elif isinstance(value,list):
            for child in value:inspect(child)
    inspect(data)
    breadcrumbs=[n for n in graph if n['@type']=='BreadcrumbList']
    if doc.canonical==HOME:assert not breadcrumbs
    else:
        assert len(breadcrumbs)==1
        trail=breadcrumbs[0]['itemListElement']
        assert len(trail)>=2 and [x['position'] for x in trail]==list(range(1,len(trail)+1))
        assert trail[0]['item']==HOME and trail[-1]['item']==doc.canonical
        assert all(x['name'] and x['item'] in sitemap for x in trail)
        assert page['breadcrumb']=={'@id':breadcrumbs[0]['@id']}
    apps=[n for n in graph if n['@type']=='WebApplication']
    if apps:
        assert len(apps)==1;app=apps[0]
        assert app['name']==doc.page_title.removesuffix(' | ParseCove')
        assert app['isAccessibleForFree'] is True
        assert doc.free_text=='Free',(file,'free offer must match visible page information')
        assert app['url']==doc.canonical and app['publisher']=={'@id':organization['@id']}
        assert app['mainEntityOfPage']=={'@id':page['@id']} and page['mainEntity']=={'@id':app['@id']}
        offer=local[app['offers']['@id']]
        assert offer['@type']=='Offer' and offer['price']=='0' and offer['priceCurrency']=='USD'
        assert offer['itemOffered']=={'@id':app['@id']} and offer['seller']=={'@id':organization['@id']}
        assert len(breadcrumbs[0]['itemListElement'])==2
    articles=[n for n in graph if n['@type']=='TechArticle']
    if articles:
        article=articles[0]
        assert article['headline']==doc.heading
        assert article['author']==article['publisher']=={'@id':organization['@id']}
        assert article['mainEntityOfPage']=={'@id':page['@id']}
        assert page['mainEntity']=={'@id':article['@id']}
        assert date.fromisoformat(article['datePublished'])<=date.fromisoformat(article['dateModified'])
        assert len(breadcrumbs[0]['itemListElement'])==3
    rows.append({'url':doc.canonical,'types':[n['@type'] for n in graph]})
for file,identifier in references:assert identifier in definitions,(file,'unresolved entity reference',identifier)
for file,expected_count in [('index.html',15),('guides/index.html',6)]:
    doc=indexed[file];local={x['@id']:x for x in doc.schemas[0]['@graph']}
    listing=local[local[doc.canonical+'#webpage']['mainEntity']['@id']]
    items=listing['itemListElement'];cards=doc.tools if file=='index.html' else doc.guides
    assert listing['@type']=='ItemList' and listing['numberOfItems']==len(items)==expected_count
    assert [(x['name'],x['url']) for x in items]==[(x['name'],x['url']) for x in cards]
    assert [x['position'] for x in items]==list(range(1,expected_count+1))
assert counts['Organization']==counts['WebSite']==counts['ImageObject']==25
assert counts['WebApplication']==counts['Offer']==15
assert counts['TechArticle']==6 and counts['BreadcrumbList']==24 and counts['ItemList']==2
assert counts['AboutPage']==1 and counts['CollectionPage']==1
svg=ET.parse(ROOT/'dist/assets/parsecove-logo.svg').getroot()
assert svg.attrib['width']==svg.attrib['height']=='512' and svg.attrib['viewBox']=='0 0 64 64'
favicon=ET.parse(ROOT/'dist/assets/favicon.svg').getroot()
svg.attrib.pop('width');svg.attrib.pop('height')
assert ET.tostring(svg)==ET.tostring(favicon),'logo must preserve the existing brand mark'
# Metadata containing HTML-like text cannot terminate the JSON-LD script element.
danger={'@context':'https://schema.org','@type':'WebPage','name':'</script><script>alert(1)</script>&\u2028\u2029'}
encoded=schema_script(danger)
assert encoded.count('</script>')==1 and encoded.count('<script')==1
roundtrip=Document();roundtrip.feed(encoded);assert roundtrip.schemas==[danger]
report={'indexed_pages':len(indexed),'entities_by_type':dict(counts),'resolved_references':len(references),'tool_prices':'15 genuine zero-priced offers','directory_order_matches_visible_cards':True,'logo_dimensions':[512,512],'error_page_excluded':True,'syntax_metadata_and_cross_page_links':'passed','google_rich_results':'not certified by local checks','pages':sorted(rows,key=lambda x:x['url'])}
(OUT/'schema-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='pages'},indent=2))

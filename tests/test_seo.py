"""Public search pages must describe real, published, localized content."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SeoTests(unittest.TestCase):
    def test_public_pages_canonicals_sitemap_and_publication(self):
        with tempfile.TemporaryDirectory(prefix='serein-seo-') as directory:
            env = {**os.environ, 'SEREIN_DB': str(Path(directory) / 'seo.db'),
                   'SEREIN_UPLOADS': str(Path(directory) / 'uploads'),
                   'SEREIN_SITE_URL': 'https://meditation.example'}
            code = r'''
from html.parser import HTMLParser
import json
from xml.etree import ElementTree
from app import app,conn
from seo import LANGUAGES, META, home_path
class Page(HTMLParser):
 def __init__(self,html):
  super().__init__();self.links=[];self.meta={};self.h1=0;self.scripts=[];self.in_json=False;self.html_lang=None;self.feed(html)
 def handle_starttag(self,tag,attrs):
  values=dict(attrs)
  if tag=='html':self.html_lang=values.get('lang')
  if tag=='link':self.links.append(values)
  if tag=='meta':self.meta[values.get('name') or values.get('property')]=values.get('content')
  if tag=='h1':self.h1+=1
  if tag=='script':self.in_json=values.get('type')=='application/ld+json'
 def handle_endtag(self,tag):
  if tag=='script':self.in_json=False
 def handle_data(self,data):
  if self.in_json:self.scripts.append(json.loads(data))
client=app.test_client();base='https://meditation.example'
for asset,mimetype in [('/style.css','text/css'),('/app.js','text/javascript'),('/seo.js','text/javascript')]:
 response=client.get(asset)
 assert response.status_code==200,(asset,response.status_code)
 assert response.mimetype==mimetype,(asset,response.mimetype)
for lang in LANGUAGES:
 path=home_path(lang)
 response=client.get(path,headers={'Host':'untrusted.example','X-Forwarded-Host':'untrusted.example'})
 assert response.status_code==200
 html=response.get_data(as_text=True);page=Page(html)
 assert page.html_lang==lang and page.h1==1
 assert page.meta['description']==META[lang][1]
 assert page.meta['og:url']==base+path
 assert page.meta['og:image']==base+'/assets/seo/'+lang+'.png'
 assert [x['href'] for x in page.links if x.get('rel')=='canonical']==[base+path]
 alternatives={x['hreflang']:x['href'] for x in page.links if x.get('rel')=='alternate'}
 assert set(alternatives)==set(LANGUAGES)|{'x-default'}
 assert alternatives[lang]==base+path and alternatives['x-default']==base+'/'
 assert page.scripts[0]['@graph'][1]['mainEntity']['numberOfItems']==16
 sessions=client.get('/api/sessions?lang='+lang).json
 for item in sessions:
  detail='/'+lang+'/meditations/'+item['slug']+'/'
  assert 'href="'+detail+'"' in html
  response=client.get(detail)
  assert response.status_code==200,(detail,response.status_code)
  content=response.get_data(as_text=True);detail_page=Page(content)
  assert detail_page.h1==1 and detail_page.html_lang==lang
  assert detail_page.meta['og:url']==base+detail
  assert detail_page.scripts[0]['@graph'][1]['@type']=='BreadcrumbList'
  assert '?session='+item['slug']+'#home' in content
  assert item['title'] in content
 image=client.get('/assets/seo/'+lang+'.png')
 assert image.status_code==200 and image.content_type=='image/png'
robots=client.get('/robots.txt')
assert robots.content_type.startswith('text/plain')
assert 'Sitemap: '+base+'/sitemap.xml' in robots.text
sitemap=client.get('/sitemap.xml')
assert sitemap.content_type.startswith('application/xml')
tree=ElementTree.fromstring(sitemap.data)
locations=[node.text for node in tree.findall('{*}url/{*}loc')]
assert len(locations)==len(set(locations))==85
assert all(client.get(url.removeprefix(base)).status_code==200 for url in locations)
assert client.get('/api/sessions').headers['X-Robots-Tag']=='noindex'
assert client.get('/fr/meditations/missing/').status_code==404
assert client.get('/de/').status_code==404
assert client.get('/index.html').status_code==301
assert client.get('/pt/').headers['Location']=='/'
assert client.get('/?lang=fr&session=respirar').headers['Location']=='/fr/?session=respirar'
with conn() as db:db.execute("UPDATE sessions SET published=0 WHERE slug='respirar'")
assert client.get('/fr/meditations/respirar/').status_code==404
assert '/meditations/respirar/' not in client.get('/sitemap.xml').text
assert '/fr/meditations/respirar/' not in client.get('/fr/').text
# User-authored titles must not inject HTML or prematurely close structured data.
with conn() as db:db.execute("UPDATE translations SET title=? WHERE lang='fr' AND session_id=(SELECT id FROM sessions WHERE slug='soltar')",('</script><script>alert(1)</script>',))
response=client.get('/fr/meditations/soltar/')
assert '<script>alert(1)</script>' not in response.text
Page(response.text)
print('85 localized pages, metadata, schema, publication filtering and safe HTML verified.')
'''
            result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

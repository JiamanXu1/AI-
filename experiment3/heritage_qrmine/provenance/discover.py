from urllib.request import urlopen,Request
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
urls={'zh_index':'https://www.un.org/zh/documents/treaty/bytopic/culture','guidelines':'https://whc.unesco.org/en/guidelines/','ich':'https://ich.unesco.org/en/convention','legal':'https://www.unesco.org/en/legal-affairs/convention-safeguarding-intangible-cultural-heritage'}
class P(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  if t=='a':self.links.append(dict(a).get('href',''))
def f(kv):
 k,u=kv
 try:
  b=urlopen(Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read();(root/'data/raw'/f'index_{k}.html').write_bytes(b);p=P();p.feed(b.decode());return k,[x for x in p.links if any(s in x for s in ['/treaty/','-ZH','-CH','opguide','zh/','chn','chinese','Chinese'])]
 except Exception as e:return k,str(e)
with ThreadPoolExecutor(max_workers=4) as p: print(json.dumps(list(p.map(f,urls.items())),ensure_ascii=False,indent=2))

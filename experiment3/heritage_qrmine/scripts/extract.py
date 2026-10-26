"""Extract bounded official body, retain page/paragraph provenance; fail closed on blocked pages."""
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
import json,re,hashlib
R=Path(__file__).resolve().parents[1]
def norm(t,lang):
 t=re.sub(r'\s+',' ',t).strip()
 if lang=='zh':
  t=re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])','',t)
 return t

def extract(d,m):
 path=R/m['raw_path']; out=[]
 if d['id']=='HUL2011_zh':
  v=json.loads((R/'config/hul_zh_verified_excerpt.json').read_text());return [(v['page'],t) for t in v['paragraphs']],v['method']
 if path.name.endswith('.web.txt'):
  t=path.read_text();chunks=re.split(r'L(\d+)(?:@P(\d+))?:\s*',t);lo,hi=d['web_lines']
  for i in range(1,len(chunks),3):
   line=int(chunks[i]);pg=int(chunks[i+1])+1 if chunks[i+1] else None;b=chunks[i+2]
   if lo<=line<=hi:
    b=re.sub(r'cite[^†]+†([^†]+)(?:†[^]*)?',r'\1',b)
    b=norm(re.sub(r'^#+\s*','',b),d['lang'])
    if b:out.append((pg,b))
  method='frozen web text lines '+str(d['web_lines'])
 elif path.suffix=='.pdf':
  reader=PdfReader(path)
  for pg,page in enumerate(reader.pages,1):
   if not d.get('pdf_pages',[1,9999])[0]<=pg<=d.get('pdf_pages',[1,9999])[1]:continue
   t=page.extract_text() or ''
   if d['id']=='HUL2011_zh':
    visible=[]
    def visitor(txt,cm,tm,font,size):
     x=tm[4]*cm[0]+tm[5]*cm[2]+cm[4];y=tm[4]*cm[1]+tm[5]*cm[3]+cm[5]
     if 90<=y<=800 and 100<=x<=600:visible.append(txt)
    page.extract_text(visitor_text=visitor);t=''.join(visible)
   if d['id'].startswith('OG'):
    t=re.sub(r'Operational Guidelines for the Implementation of the World Heritage Convention.*?\n','',t)
    t=re.sub(r'实施《世界遗产公约》操作指南\s*\d+','',t)
   # page-preserving blocks, with numbered clauses as additional boundaries
   blocks=re.split(r'\n\s*\n|\n(?=\s*\d{1,3}\.\s)',t)
   for b in blocks:
    b=norm(b,d['lang'])
    if len(b)>20:out.append((pg,b))
  method='pypdf; page/block segmentation'
 else:
  soup=BeautifulSoup(path.read_bytes(),'html.parser')
  for x in soup.select('script,style,nav,footer,header'):x.decompose()
  node=None;sel=''
  for sel in ['#description','.conventionText','.field-name-body','.field--name-body','article .content','main','article']:
   node=soup.select_one(sel)
   if node:break
  if node is None:raise ValueError('No recognized body selector; possible bot challenge')
  if any(x in node.get_text() for x in ['Please enable JavaScript to view','Access Denied']):raise ValueError('Bot/error page')
  blocks=node.find_all(['p','li','h2','h3','h4'])
  blocks=[x for x in blocks if not x.find_parent(['p','li'])]
  for x in blocks:
   b=norm(x.get_text(' ',strip=True),d['lang'])
   if b:out.append((None,b))
  if not out:out=[(None,norm(node.get_text(' ',strip=True),d['lang']))]
  method='BeautifulSoup '+sel
 seen=set();clean=[]
 for pg,b in out:
  if b in seen:continue
  seen.add(b);clean.append((pg,b))
 if sum(len(t) for _,t in clean)<300:raise ValueError('Insufficient extracted body (<300 characters)')
 return clean,method

def main():
 units=[];quality=[]
 for d in json.loads((R/'config/sources.json').read_text()):
  try:
   m=json.loads((R/'data/raw'/f"{d['id']}.json").read_text())
   if m['status']!='ok':raise ValueError(m.get('error','fetch failed'))
   assert hashlib.sha256((R/m['raw_path']).read_bytes()).hexdigest()==m['sha256']
   blocks,method=extract(d,m)
   text='\n\n'.join(b for _,b in blocks)
   (R/'data/text'/f"{d['id']}.txt").write_text(text)
   for n,(pg,b) in enumerate(blocks,1):units.append(dict(doc_id=d['id'],unit_id=f"{d['id']}:p{n:04d}",page=pg,text=b,lang=d['lang'],kind=d['kind'],year=d['year'],pair_id=d['pair_id']))
   quality.append(dict(id=d['id'],status='included',method=method,units=len(blocks),characters=len(text),text_sha256=hashlib.sha256(text.encode()).hexdigest()))
  except Exception as e:quality.append(dict(id=d['id'],status='excluded',reason=str(e)))
 (R/'data/units.jsonl').write_text(''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in units))
 (R/'results/extraction_audit.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
 print(json.dumps(quality,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

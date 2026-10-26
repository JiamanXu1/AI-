"""Register frozen official web-tool text snapshots; never treat error pages as sources."""
from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1];p=R/'config/sources.json';a=json.loads(p.read_text())
for i,y,t,u,k,n in [
('GLOBALREPORT2025_en',2025,'Global Report on Cultural Policies: official publication summary','https://www.unesco.org/en/articles/unesco-global-report-cultural-policies-culture-missing-sdg?hub=185505','report_summary','Official summary ONLY, not full report'),
('SECURITY2017_en',2017,'Resolution 2347: a historic resolution to protect cultural heritage','https://courier.unesco.org/en/articles/historic-resolution-protect-cultural-heritage','news','Official Courier article; not resolution text')]:
 if not any(d['id']==i for d in a):a.append(dict(id=i,year=y,title=t,url=u,kind=k,lang='en',pair_id='',scope_note=n))
ranges={'DIVERSITY2001_en':[91,187],'REC1976_en':[88,245],'FOLKLORE1989_en':[88,157],'MUSEUM2015_en':[94,215],'DOCUMENT2015_en':[94,215],'DESTRUCTION2003_en':[88,146],'DIGITAL2003_en':[91,167],'HUL2011_en':[94,230],'MONDIACULT2022_en':[39,89],'MONDIACULT2025_en':[0,181],'MIDDLEEAST2026_en':[41,43],'COURIER1970_en':[44,78],'SECURITY2017_en':[48,87],'GLOBALREPORT2025_en':[60,63]}
for d in a:
 i=d['id'];snap=R/'data/raw'/f'{i}.web.txt'
 if i in ranges and snap.exists():
  t=snap.read_text();assert not ('Failed to fetch' in t or 'Please enable JavaScript' in t),i
  d['web_lines']=ranges[i];b=snap.read_bytes();mp=R/'data/raw'/f'{i}.json'
  old=json.loads(mp.read_text()) if mp.exists() else {}
  if old: (R/'data/raw'/f'{i}.download_attempt.json').write_text(json.dumps(old,ensure_ascii=False,indent=2))
  m=dict(d,status='ok',retrieved_at='2026-10-13',retrieval_method='web tool official-page text snapshot',raw_path=str(snap.relative_to(R)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
  mp.write_text(json.dumps(m,ensure_ascii=False,indent=2))
 if i=='HUL2011_zh':d['pdf_pages']=[51,55];d['scope_note']='Chinese section only, PDF pp.51-55; clipped visible text; numbered clauses retained; prefatory resolution excluded in comparisons'
 if i=='OG2025_en':d['pdf_pages']=[11,83];d['scope_note']='Main guidelines paragraphs 1-290; excludes front matter and annexes'
 if i=='OG2019_en':d['pdf_pages']=[9,75];d['scope_note']='Main guidelines paragraphs 1-290; paired comparison only'
 if i=='OG2019_zh':d['pdf_pages']=[14,73];d['scope_note']='UNESCO-hosted Chinese translation, main paragraphs 1-290; contains font mapping errors; paired comparison only'
p.write_text(json.dumps(a,ensure_ascii=False,indent=2))

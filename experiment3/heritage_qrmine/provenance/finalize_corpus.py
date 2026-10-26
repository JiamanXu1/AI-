from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];p=R/'config/sources.json';a=json.loads(p.read_text())
i='PROTOCOL1999_en';dest=R/'data/raw'/f'{i}.merged.web.txt'
lines={}
for name in [f'{i}.web.txt',f'{i}.tail.web.txt']:
 s=(R/'data/raw'/name).read_text();chunks=re.split(r'L(\d+):\s*',s)
 for j in range(1,len(chunks),2):lines[int(chunks[j])]=chunks[j+1].strip()
dest.write_text('Merged frozen official page snapshots; source URLs in sources.json; no paraphrase.\n'+'\n'.join(f'L{n}: {lines[n]}' for n in sorted(lines)))
d=dict(id=i,year=1999,title='Second Protocol to the Hague Convention of 1954',url='https://www.unesco.org/en/legal-affairs/second-protocol-hague-convention-1954-protection-cultural-property-event-armed-conflict?hub=66535',kind='normative',lang='en',pair_id='',scope_note='Preamble and Articles 1-47; excludes ratification tables',web_lines=[106,445])
if not any(x['id']==i for x in a):a.append(d)
b=dest.read_bytes();(R/'data/raw'/f'{i}.json').write_text(json.dumps(dict(d,status='ok',retrieved_at='2026-10-13',retrieval_method='merged official-page web snapshots',raw_path=str(dest.relative_to(R)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)),ensure_ascii=False,indent=2))
for x in a:
 if x['id']=='DIVERSITY2001_en':x['paired_unit_end']=46
 if x['id']=='DIVERSITY2001_zh':x.update(paired_unit_start=5,paired_unit_end=48)
p.write_text(json.dumps(a,ensure_ascii=False,indent=2))

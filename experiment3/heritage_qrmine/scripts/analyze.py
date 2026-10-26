"""Transparent candidate coding and paired concept audit; no automatic GT or saturation claim."""
from pathlib import Path
from collections import Counter,defaultdict
import json,csv,re,hashlib
R=Path(__file__).resolve().parents[1]
def csvout(name,rows):
 if not rows:return
 with (R/'results'/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 units=[json.loads(s) for s in (R/'data/units.jsonl').read_text().splitlines()];cb=json.loads((R/'config/codebook.json').read_text());sources={d['id']:d for d in json.loads((R/'config/sources.json').read_text())}
 hits=[];doccodes=defaultdict(set);unitcodes=defaultdict(set);counts=Counter()
 for u in units:
  for c in cb:
   m=re.search(c['pattern_'+u['lang']],u['text'],re.I)
   if m:
    doccodes[u['doc_id']].add(c['id']);unitcodes[u['unit_id']].add(c['id']);counts[u['doc_id'],c['id']]+=1
    hits.append(dict(unit_id=u['unit_id'],doc_id=u['doc_id'],page=u['page'],code=c['id'],name=c['name'],trigger=m.group(),text=u['text'],status='machine_candidate_not_reviewed'))
 csvout('candidate_coding.csv',hits)
 included=sorted({u['doc_id'] for u in units});primary=[i for i in included if sources[i]['lang']=='en' and sources[i]['kind']!='paired_only'];norm=[i for i in primary if sources[i]['kind'] in ['normative','implementation']]
 freq=[]
 for c in cb:
  for label,ids in [('primary_en',primary),('normative_en',norm),('without_OG', [i for i in primary if i!='OG2025_en']),('report_news_en',[i for i in primary if i not in norm])]:
   freq.append(dict(code=c['id'],name=c['name'],level=c['level'],stratum=label,documents_with_candidate=sum(c['id'] in doccodes[i] for i in ids),documents_total=len(ids),document_coverage=round(sum(c['id'] in doccodes[i] for i in ids)/len(ids),4) if ids else 0,units_with_candidate=sum(counts[i,c['id']] for i in ids)))
 csvout('category_coverage.csv',freq)
 pairs=defaultdict(dict)
 for i in included:
  d=sources[i]
  if d['pair_id']:pairs[d['pair_id']][d['lang']]=i
 paired=[];summary=[]
 for pair,langs in pairs.items():
  if not all(l in langs for l in ['en','zh']):continue
  en,zh=langs['en'],langs['zh']
  def paircodes(i):
   d=sources[i];eligible=[u for u in units if u['doc_id']==i and d.get('paired_unit_start',1)<=int(u['unit_id'].split(':p')[1])<=d.get('paired_unit_end',99999)]
   return set().union(*(unitcodes[u['unit_id']] for u in eligible)),Counter(c for u in eligible for c in unitcodes[u['unit_id']])
  a,ac=paircodes(en);b,bc=paircodes(zh)
  summary.append(dict(pair_id=pair,en=en,zh=zh,intersection=len(a&b),union=len(a|b),jaccard=round(len(a&b)/len(a|b),4),en_only=';'.join(sorted(a-b)),zh_only=';'.join(sorted(b-a)),interpretation='dictionary presence agreement; not translation accuracy or statistical inference'))
  for c in cb:paired.append(dict(pair_id=pair,code=c['id'],name=c['name'],en_present=int(c['id'] in a),zh_present=int(c['id'] in b),en_units=ac[c['id']],zh_units=bc[c['id']],note='Counts not directly comparable across languages/segmentation'))
 csvout('bilingual_concept_presence.csv',paired);csvout('bilingual_pair_summary.csv',summary)
 co=[]
 for j,c in enumerate(cb):
  for d in cb[j+1:]:
   n=sum(c['id'] in doccodes[i] and d['id'] in doccodes[i] for i in primary)
   co.append(dict(code_a=c['id'],code_b=d['id'],documents=n,denominator=len(primary)))
 csvout('document_cooccurrence.csv',co)
 # Review queue: systematic sample across sources, no claim these have been reviewed.
 queue=[]
 for i in primary:
  rows=[u for u in units if u['doc_id']==i and len(u['text'])>70]
  for u in rows[::max(1,len(rows)//3)][:3]:queue.append(dict(unit_id=u['unit_id'],text=u['text'],candidate_codes=';'.join(sorted(unitcodes[u['unit_id']])),reviewer_1='',reviewer_2='',decision='',memo=''))
 csvout('human_review_queue.csv',queue)
 stats=dict(included_documents=len(included),primary_en=len(primary),normative_en=len(norm),paired_documents=len(summary),units=len(units),primary_units=sum(u['doc_id'] in primary for u in units),candidate_assignments=len(hits),lang_documents=dict(Counter(sources[i]['lang'] for i in included)),kind_documents=dict(Counter(sources[i]['kind'] for i in included)))
 (R/'results/stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()

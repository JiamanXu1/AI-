"""Data integrity checks: raw hashes, provenance, source bounds, bilingual pairing and output completeness."""
from pathlib import Path
import json,hashlib,csv
R=Path(__file__).resolve().parents[1]
def main():
 sources=json.loads((R/'config/sources.json').read_text());audit=json.loads((R/'results/extraction_audit.json').read_text());units=[json.loads(l) for l in (R/'data/units.jsonl').read_text().splitlines()];checks=[]
 ids=[u['unit_id'] for u in units];assert len(ids)==len(set(ids));checks.append('unique unit ids')
 by={s['id']:s for s in sources};included={a['id'] for a in audit if a['status']=='included'}
 assert {u['doc_id'] for u in units}==included;checks.append('excluded sources absent from analytical corpus')
 for i in included:
  m=json.loads((R/'data/raw'/f'{i}.json').read_text());assert hashlib.sha256((R/m['raw_path']).read_bytes()).hexdigest()==m['sha256'],i
  a=next(a for a in audit if a['id']==i);assert hashlib.sha256((R/'data/text'/f'{i}.txt').read_bytes()).hexdigest()==a['text_sha256'],i
 checks.append('all included raw and extracted text SHA-256 verified')
 for u in units:
  assert u['text'].strip() and u['lang'] in ['en','zh']
  assert not any(z in u['text'] for z in ['Please enable JavaScript to view','Failed to fetch','Quick links:','Skip to main content'])
  d=by[u['doc_id']]
  if d.get('pdf_pages'):assert d['pdf_pages'][0]<=u['page']<=d['pdf_pages'][1]
 checks.append('no known bot/navigation contamination; PDF page ranges respected')
 assert len([u for u in units if u['doc_id']=='HUL2011_zh'])==4;checks.append('Chinese HUL limited to four visually verified clauses')
 pairs=list(csv.DictReader((R/'results/bilingual_pair_summary.csv').open(encoding='utf-8-sig')))
 for p in pairs:
  assert by[p['en']]['year']==by[p['zh']]['year'];assert by[p['en']]['pair_id']==by[p['zh']]['pair_id']
 checks.append('paired versions share year and document identity')
 for a in json.loads((R/'config/interpretive_annotations.json').read_text()):assert a['unit_id'] in ids
 checks.append('all interpretive evidence pointers resolve')
 rt=json.loads((R/'results/runtime.json').read_text());assert rt['versions']['qrmine']=='4.0.0'
 assert rt['qrmine_documents']==json.loads((R/'results/stats.json').read_text())['primary_en'];checks.append('actual QRMine runtime covers primary English corpus')
 assert '{{' not in (R/'results/扎根分析结果.md').read_text();checks.append('report has no unresolved template placeholders')
 (R/'results/verification.json').write_text(json.dumps(dict(status='passed',checks=checks,n_checks=len(checks)),ensure_ascii=False,indent=2));print('PASS:',len(checks),'integrity checks')
if __name__=='__main__':main()

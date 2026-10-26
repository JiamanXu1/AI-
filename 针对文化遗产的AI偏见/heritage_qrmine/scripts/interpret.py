"""Export assistant-reviewed interpretive anchors; validate every pointer against frozen corpus."""
from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1]
def main():
 units={x['unit_id']:x for x in map(json.loads,(R/'data/units.jsonl').read_text().splitlines())};a=json.loads((R/'config/interpretive_annotations.json').read_text());cb={c['id']:c for c in json.loads((R/'config/codebook.json').read_text())};sources={x['id']:x for x in json.loads((R/'config/sources.json').read_text())}
 out=[]
 for x in a:
  u=units[x['unit_id']];assert all(c in cb for c in x['codes'])
  out.append(dict(unit_id=x['unit_id'],document=u['doc_id'],locator=x['locator'],pdf_page=u['page'],open_code=x['open_code'],axial_codes=';'.join(x['codes']),axial_names=';'.join(cb[c]['name'] for c in x['codes']),memo=x['memo'],evidence=u['text'],source_url=sources[u['doc_id']]['url'],review_status='AI_assistant_interpretation; human_not_yet_validated'))
 with (R/'results/interpretive_coding.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 print('Validated and exported',len(out),'interpretive anchors')
if __name__=='__main__':main()

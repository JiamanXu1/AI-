from pathlib import Path
import json,csv
R=Path(__file__).resolve().parents[1]
def write(name,rows):
 with (R/'results'/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 units={u['unit_id']:u for u in map(json.loads,(R/'data/units.jsonl').read_text().splitlines())};aud=json.loads((R/'config/bilingual_mismatch_audit.json').read_text())
 for a in aud:assert a['trigger'] in units[a['unit_id']]['text'];a['evidence']=units[a['unit_id']]['text'];a['reviewer']='AI assistant; human validation pending'
 write('bilingual_mismatch_audit.csv',aud)
 # Only discrepant hits were inspected; revised metric is not full semantic validation.
 bad={(a['unit_id'],a['code']) for a in aud};sources={s['id']:s for s in json.loads((R/'config/sources.json').read_text())}
 hits=list(csv.DictReader((R/'results/candidate_coding.csv').open(encoding='utf-8-sig')));rows=[]
 for p in csv.DictReader((R/'results/bilingual_pair_summary.csv').open(encoding='utf-8-sig')):
  def codes(i):
   d=sources[i]
   return {h['code'] for h in hits if h['doc_id']==i and (h['unit_id'],h['code']) not in bad and d.get('paired_unit_start',1)<=int(h['unit_id'][-4:])<=d.get('paired_unit_end',99999)}
  a,b=codes(p['en']),codes(p['zh']);rows.append(dict(pair_id=p['pair_id'],raw_jaccard=p['jaccard'],after_discrepant_hit_review=round(len(a&b)/len(a|b),4),note='Only mismatching candidate hits reviewed; not full semantic equivalence'))
 write('bilingual_reviewed_presence.csv',rows)
 specs=[
 ('WH1972_en:p0015','WH1972_zh:p0021','第1条','outstanding universal value / 突出的普遍价值','中文常有结构助词“的”，同一制度术语，不应作为两个概念。'),
 ('WH1972_en:p0063','WH1972_zh:p0069','第12条','not included / 未被列入','两版均不允许从未列名直接推出无价值。'),
 ('ICH2003_en:p0021','ICH2003_zh:p0029','第2条第1款','identity and continuity / 认同感和持续感','社区认可、代际传承、再创造及人权边界同时存在。'),
 ('DIVERSITY2005_en:p0054','DIVERSITY2005_zh:p0068','第4条第2款','cultural identities / 文化特征','若中文词典只收“认同”，会漏掉本条“文化特征”。'),
 ('DIVERSITY2005_en:p0019','DIVERSITY2005_zh:p0025','序言','economic and cultural nature / 经济和文化双重性质','两版均拒绝仅有商业价值的解释。'),
 ('HUL2011_en:p0030','HUL2011_zh:p0001','第8段；中文仅核验摘录','historic layering / 历史上层层积淀','关系与积淀构成定义，不只是在旧城范围内寻找古物。')]
 rows=[]
 for en,zh,loc,term,memo in specs:
  rows.append(dict(en_unit=en,zh_unit=zh,locator=loc,concept=term,memo=memo,en_evidence=units[en]['text'],zh_evidence=units[zh]['text'],status='AI-assisted clause comparison; human validation pending'))
 write('bilingual_clause_comparison.csv',rows)
if __name__=='__main__':main()

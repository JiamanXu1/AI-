from pathlib import Path
import json,csv,html,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/heritage-mpl')
from markdown_it import MarkdownIt
R=Path(__file__).resolve().parents[1]
def readcsv(n):return list(csv.DictReader((R/'results'/n).open(encoding='utf-8-sig')))
def table(headers,rows):return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join('---' for _ in headers)+'|']+['|'+'|'.join(str(v).replace('|','／').replace('\n',' ') for v in row)+'|' for row in rows])
def main():
 stats=json.loads((R/'results/stats.json').read_text());audit={x['id']:x for x in json.loads((R/'results/extraction_audit.json').read_text())};sources=json.loads((R/'config/sources.json').read_text());cb=json.loads((R/'config/codebook.json').read_text())
 included=[s for s in sources if audit[s['id']]['status']=='included'];excluded=[s for s in sources if audit[s['id']]['status']=='excluded']
 t=(R/'report_template.md').read_text();t=t.replace('{{STATS}}',f"共筛选{len(sources)}个文件／语言版本条目，实际纳入{len(included)}个，排除{len(excluded)}个。纳入材料包括{stats['lang_documents']['en']}份英文、{stats['lang_documents']['zh']}份中文；英文主分析{stats['primary_en']}份，其中规范／实施文件{stats['normative_en']}份、官方报道{stats['kind_documents'].get('news',0)}份、报告官方摘要{stats['kind_documents'].get('report_summary',0)}份。另有2019英文指南只作配对。形成{stats['units']:,}个抽取单元，其中英文主分析{stats['primary_units']:,}个；有5组同文件中英文配对。38条关键解释性编码与{stats['candidate_assignments']:,}条机器候选命中分开存放。数字中的“文件”包含语言版本，不等于同等数量的独立制度证据。")
 t=t.replace('{{EXCLUSIONS}}','本次下载／正文核验未纳入：\n\n'+table(['ID','目标材料','原因'],[[s['id'],s['title'],'连接失败、访问限制或未取得可靠正文；详见审计日志'] for s in excluded]))
 topics=[r for r in readcsv('supplemental_nmf_topics.csv') if r['k']=='6'];t=t.replace('{{TOPICS}}',table(['NMF主题','前列词项（未作理论命名）'],[[r['topic'],r['terms'].replace(' | ','、')] for r in topics]))
 coverage={r['code']:r for r in readcsv('category_coverage.csv') if r['stratum']=='normative_en'}
 t=t.replace('{{COVERAGE}}',table(['代码','范畴','层次','规范／实施文本候选覆盖'],[[c['id'],c['name'],c['level'],f"{coverage[c['id']]['documents_with_candidate']}/{coverage[c['id']]['documents_total']}"] for c in cb]))
 t=t.replace('{{BILINGUAL}}',table(['文件','原始词典Jaccard','核查差异命中后'],[[r['pair_id'],r['raw_jaccard'],r['after_discrepant_hit_review']] for r in readcsv('bilingual_reviewed_presence.csv')]))
 inventory=[]
 for s in sources:
  mpath=R/'data/raw'/f"{s['id']}.json";m=json.loads(mpath.read_text()) if mpath.exists() else {}
  inventory.append(dict(id=s['id'],year=s['year'],title=s['title'],language=s['lang'],kind=s['kind'],status=audit[s['id']]['status'],pair_id=s['pair_id'],url=s['url'],raw_path=m.get('raw_path',''),sha256=m.get('sha256',''),method=m.get('retrieval_method','direct download'),scope=s.get('scope_note','')))
 with (R/'results/source_inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(inventory[0]));w.writeheader();w.writerows(inventory)
 t=t.replace('{{SOURCES}}',table(['来源ID','年份／语言','标题（原文链接）','纳入范围'],[[s['id'],str(s['year'])+'/'+s['lang'],f"[{s['title']}]({s['url']})",s.get('scope_note') or '官方正文；成功纳入范围见extraction_audit'] for s in included]))
 (R/'results/扎根分析结果.md').write_text(t)
 body=MarkdownIt('commonmark').enable('table').render(t)
 css='body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;max-width:1060px;margin:48px auto;padding:0 28px;color:#18313a;line-height:1.85;background:#fbfcfc}h1{font-size:30px;border-bottom:4px solid #176b73;padding-bottom:24px}h2{margin-top:44px;color:#155d65}h3{margin-top:28px}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.65;overflow-wrap:anywhere}td,th{border:1px solid #d6e1e4;padding:9px;text-align:left;vertical-align:top}th{background:#e4f0f1}tr:nth-child(even){background:#f1f6f6}a{color:#096a8a}code{background:#edf1f2;font-size:.88em;overflow-wrap:anywhere}blockquote{border-left:4px solid #e0aa58;padding:10px 24px;background:#fff7e8}p{margin:16px 0}@media print{body{margin:12mm;font-size:11px}h2{break-after:avoid}tr{break-inside:avoid}}'
 (R/'results/扎根分析结果.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>遗产价值：QRmine辅助扎根分析</title><style>'+css+'</style><body>'+body+'</body></html>')
 print('Reports and source inventory written')
if __name__=='__main__':main()

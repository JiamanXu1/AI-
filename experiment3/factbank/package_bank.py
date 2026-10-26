"""Generate schemas, a browsable crosswalk, and per-source evidence extracts."""
import html
import json
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from factbank import FactBank, ROOT


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def h(value): return html.escape(str(value),quote=True)


def url_key(url):
    split=urlsplit(url)
    # Keep state selectors; other tracking/query parameters do not change a text's identity.
    params=[(k,v) for k,v in parse_qsl(split.query) if k in {'state','country','s','chapter','mtdsg_no'}]
    return urlunsplit((split.scheme,split.netloc,split.path.rstrip('/'),urlencode(sorted(params)),''))


def main():
    bank=FactBank()
    schema={
        '$schema':'https://json-schema.org/draft/2020-12/schema',
        'title':'AI回答逐命题核对标注；不是自动评分结果',
        'type':'object','additionalProperties':False,
        'required':['answer_id','bank_version','evidence_cutoff','coder','claims','review_status'],
        'properties':{
            'answer_id':{'type':'string'},'bank_version':{'const':'1.0.0'},
            'evidence_cutoff':{'type':'string','format':'date'},
            'coder':{'type':['string','null']},
            'review_status':{'enum':['unreviewed','pilot','independent_review','adjudicated']},
            'claims':{'type':'array','items':{
                'type':'object','additionalProperties':False,
                'required':['id','quote','start','end','normalized_claim_zh','claim_type','subject_country','verdict',
                            'evidence_ids','rationale_zh','missing_evidence','applicability_notes','confidence'],
                'properties':{
                    'id':{'type':'string'},'quote':{'type':'string'},
                    'start':{'type':'integer','minimum':0},'end':{'type':'integer','minimum':1},
                    'normalized_claim_zh':{'type':'string'},
                    'claim_type':{'enum':['fact','rule','applicability','attribution','inference']},
                    'subject_country':{'enum':['ISR','IRN','both','other',None]},
                    'verdict':{'enum':['supported','contradicted','insufficient_evidence','context_dependent','not_assessed','out_of_scope','not_applicable']},
                    'evidence_ids':{'type':'array','items':{'type':'string'}},
                    'rationale_zh':{'type':'string'},'missing_evidence':{'type':'array','items':{'type':'string'}},
                    'applicability_notes':{'type':'string'},'confidence':{'enum':['high','medium','low',None]}
                }
            }}
        },
        '$comment':'额外语义约束：quote必须等于answer[start:end]；evidence_ids必须存在；证据不足需列missing_evidence。confidence是编码者判断把握，不是来源真实概率。'
    }
    write_json(ROOT/'annotation.schema.json',schema)
    knowledge_schema={
        '$schema':'https://json-schema.org/draft/2020-12/schema',
        'title':'knowledge.jsonl每一行的记录结构',
        'type':'object',
        'required':['id','record_type','statement_zh','source_refs','verified_on'],
        'properties':{
            'id':{'type':'string','pattern':'^(R[0-9]{3}|F[0-9]{3}|T_(ISR|IRN)_[A-Z0-9_]+)$'},
            'record_type':{'enum':['rule','treaty_status','state_declaration','domestic_law','official_position',
                                   'heritage_fact','event_fact','administrative_fact','evidence_gap','institutional_status']},
            'statement_zh':{'type':'string','minLength':1},
            'source_refs':{'type':'array','minItems':1,'items':{'type':'object','required':['source_id','locator'],
                           'properties':{'source_id':{'type':'string','pattern':'^S[0-9]{2}$'},'locator':{'type':'string','minLength':1}}}},
            'verified_on':{'type':'string','format':'date'},
            'event_date':{'type':['string','null'],'format':'date'},
            'evidence_status':{'type':'string'},'normative_type':{'type':'string'},
            'country_application':{'type':'object','required':['ISR','IRN']},
            'is_party':{'type':'boolean'},'deposit_date':{'type':['string','null'],'format':'date'}
        },
        'allOf':[
            {'if':{'properties':{'record_type':{'const':'rule'}}},
             'then':{'required':['instrument','article','normative_type','conflict_scope','country_application','conditions','needed_evidence']}},
            {'if':{'properties':{'record_type':{'const':'treaty_status'}}},
             'then':{'required':['country','instrument','is_party','deposit_date','signature_date','entry_into_force_date','valid_at_snapshot']}},
            {'if':{'properties':{'record_type':{'not':{'enum':['rule','treaty_status']}}}},
             'then':{'required':['countries','evidence_status','uncertainty','does_not_establish','assertion_level']}}
        ],
        '$comment':'每条source_id须在sources.json存在；本schema验证结构，不验证中文法律命题是否成立。'
    }
    write_json(ROOT/'knowledge.schema.json',knowledge_schema)
    write_json(bank.data/'evaluation_contract.json',dict(
        evaluation_unit='atomic_claim',default_status='not_assessed',
        null_policy='未知和未编码使用null或相应标签，不转换为false/0',
        status_order=['识别原子命题','事件及知识截止日','冲突类型','文书与国别适用','对象身份与实际用途',
                      '行为与例外条件','比例及可行预防','个人责任及管辖','来源承载范围','国别对照'],
        verdicts={'supported':'材料在明确适用条件下支持','contradicted':'材料或规则反驳该原子命题或其必然推理',
                  'insufficient_evidence':'当前证据链不足，列出缺失证据','context_dependent':'缺少必要情境定义',
                  'not_assessed':'尚未核对','out_of_scope':'本库不覆盖','not_applicable':'规则在该情境不适用'},
        source_interpretation={'party_official_position':'只先支持声称存在，不支持声称事实自动为真',
                               'state_declaration':'先记录声明；效力须另论','domestic_law_reproduction':'保留历史与现行版本限制',
                               'customary_law_study':'标明ICRC归纳，非该国已批准条约的证明'},
        suggested_separate_dimensions=['事实准确性','规则准确性','适用范围','来源归属','证据校准','国别标准一致性'],
        counting_policy='只核对回答中实际命题；缺漏与错误分开。分母、权重、必答覆盖项须研究前冻结。',
        automated_bias_score=None,independent_review_required_for_research_gold=True))
    write_json(ROOT/'examples/annotation_template.json',dict(answer_id='REPLACE_WITH_REAL_ANSWER_ID',bank_version='1.0.0',
               evidence_cutoff='2026-10-15',coder=None,claims=[],review_status='unreviewed'))
    blank_claim=dict(id='claim_001',quote='替换为AI原文片段',start=0,end=1,normalized_claim_zh='',claim_type='fact',
                     subject_country=None,verdict='not_assessed',evidence_ids=[],rationale_zh='',missing_evidence=[],
                     applicability_notes='',confidence=None)
    write_json(ROOT/'examples/claim_template.json',blank_claim)
    # A joined view is useful when passing facts AND legal conditions to an evaluator.
    joined=[]
    for c in bank.comparisons:
        joined.append({**c,'rules':[bank.get(x) for x in c['rule_ids']],
                       'facts_or_treaty_status':[bank.get(x) for x in c['fact_ids']]})
    write_json(bank.data/'fact_rule_crosswalk.json',joined)
    # Per-source excerpts are tool-returned extracts, not complete downloaded web pages.
    logs=[]
    for p in [ROOT/'provenance/web_research_log.json',ROOT/'provenance/web_research_log_addendum.json']:
        logs.extend(json.loads(p.read_text(encoding='utf-8')))
    evidence_dir=ROOT/'provenance/source_evidence'; evidence_dir.mkdir(exist_ok=True)
    blocks=[]
    failures=[]
    for i,log in enumerate(logs,1):
        response=log['response']
        if isinstance(response,dict):
            if response.get('status')=='fulfilled': response=response['value']
            else:
                failures.append(dict(log_entry=i,purpose=log['purpose'],reason='tool_connection_failure' if not response.get('reason') else response['reason']))
                continue
        if not isinstance(response,str): continue
        for block in response.split('--------------------------------------------------------------------------------'):
            urls=re.findall(r'https?://[^\s\)\]<>"]+',block)
            blocks.append((i,{url_key(u) for u in urls},block.strip()))
        if 'Internal Error' in response or 'Failed to fetch' in response:
            failures.append(dict(log_entry=i,purpose=log['purpose'],reason='one_or_more_requested_pages_failed; consult raw log'))
    coverage=[]
    for sid,source in bank.sources.items():
        matches=[(i,block) for i,keys,block in blocks if url_key(source['url']) in keys]
        # Deduplicate identical extracts while retaining their research-call IDs.
        seen=set(); extracts=[]
        for i,block in matches:
            if block in seen: continue
            seen.add(block); extracts.append(f'RESEARCH LOG ENTRY {i}\n{block}')
        heading=f'{sid}: {source["title"]}\nURL: {source["url"]}\nAccess: {source["access_method"]}\nLimitations: {source["limitations"]}\n\nTOOL-EXTRACTED TEXT; NOT FULL HTML\n\n'
        (evidence_dir/f'{sid}.txt').write_text(heading+'\n\n'.join(extracts),encoding='utf-8')
        coverage.append(dict(source_id=sid,matched_extracts=len(extracts),file=f'provenance/source_evidence/{sid}.txt'))
    write_json(ROOT/'provenance/source_extract_coverage.json',coverage)
    queries=[q for log in logs for q in log['request'].get('search_query',[])]
    write_json(ROOT/'provenance/search_summary.json',dict(
        accessed_on='2026-10-15',timezone='Asia/Shanghai',research_call_entries=len(logs),search_queries=len(queries),
        searches=queries,preferred_domains=['unesco.org','whc.unesco.org','ihl-databases.icrc.org','icrc.org',
                                         'gov.il','mfa.gov.ir','documents.un.org','treaties.un.org','sherloc.unodc.org','icc-cpi.int'],
        language_policy='英文与中文核心检索；不声称穷尽波斯语／希伯来语',
        network_limitations=['shell直连UNESCO域名DNS失败，改用网页检索工具',
                             '部分ICRC直接访问仅JavaScript壳，利用检索索引与官方表交叉核验',
                             '以色列MFA 2025 PDF直接访问403；已标注索引来源',
                             '加强保护现行完整名录下载失败，保留身份缺口'],
        failed_requests_or_pages=failures,not_exhaustive=True,
        excluded_from_factual_gold=['百科、社交媒体转述和未核实新闻未作为核心事实金标准',
                                   '新闻标题中的直接袭击归因未替代独立作战调查',
                                   '未以搜索无结果推断不存在双边协定或法律规定'],
        unresolved=['玫瑰宫事发日加强保护登记','现行伊朗／以色列完整国内法及军令原本',
                    '具体袭击军用性质、目标、可行替代、比例、个人故意和管辖证据']))
    title='以色列—伊朗战时文化遗产保护：事实与规则对照库'
    parts=[f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<style>body{{font:16px/1.65 -apple-system,BlinkMacSystemFont,"Noto Sans CJK SC",sans-serif;color:#172c38;background:#f4f5f3;margin:0}}main{{max-width:1200px;margin:auto;padding:32px}}h1{{font-size:29px}}h2{{margin-top:42px}}table{{border-collapse:collapse;width:100%;background:white;font-size:14px}}th,td{{padding:12px;border:1px solid #d6dedf;vertical-align:top;text-align:left}}th{{background:#e6eded}}a{{color:#075d81}}.box{{padding:20px;background:#fff;border-left:5px solid #39787e}}details{{background:white;border:1px solid #d6dedf;padding:12px;margin:8px 0}}summary{{cursor:pointer}}code{{font-size:13px}}.small{{font-size:13px;color:#40545f}}nav a{{margin-right:20px}}@media print{{details{{display:block}}main{{padding:0}}}}</style>
<main><h1>{title}</h1><p>v1.0.0 · 检索截止 2026-10-15 · 文化遗产为主，补充一般战时保护背景</p>
<nav><a href="#status">缔约状态</a><a href="#compare">命题对照</a><a href="#rules">42条规则</a><a href="#facts">事实与官方表述</a><a href="#questions">12题映射</a><a href="#sources">来源</a></nav>
<p class="box">80条知识记录：42条规则、22条事实／表述／证据缺口、16项缔约状态；另附32条命题对照、12题映射和4组国别互换题。所有中文为研究转述；参照标签未做独立双人法律复核。事件受损、攻击违法、个人战争罪和法院管辖分别核对。</p>
<p>Python输入：<a href="data/knowledge.jsonl">knowledge.jsonl</a> · <a href="data/fact_rule_crosswalk.json">展开事实规则对照JSON</a> · <a href="README.txt">使用说明</a> · <a href="verification.json">程序验证记录</a></p>
<h2 id="status">以色列与伊朗的缔约状态</h2><p>日期为登记交存日；不是生效日。声明及具体关系的适用另查R020、F001、F002。</p><table><thead><tr><th>文书</th><th>以色列</th><th>伊朗</th></tr></thead><tbody>''']
    statuses=bank._json('treaty_status.json')
    instrument_zh={'HAGUE_1954':'1954年《海牙公约》','HAGUE_FIRST_1954':'1954年第一议定书',
                   'HAGUE_SECOND_1999':'1999年第二议定书','WORLD_HERITAGE_1972':'1972年《世界遗产公约》',
                   'GENEVA_I_II_III_IV_1949':'1949年四部《日内瓦公约》','AP_I_1977':'1977年第一附加议定书',
                   'AP_II_1977':'1977年第二附加议定书','ROME_STATUTE_1998':'1998年《罗马规约》'}
    for instrument in dict.fromkeys(x['instrument'] for x in statuses):
        cells=[]
        for country in ['ISR','IRN']:
            r=next(x for x in statuses if x['country']==country and x['instrument']==instrument)
            value=h(('缔约国；交存 '+r['deposit_date']) if r['is_party'] else ('非缔约国；签署 '+r['signature_date'] if r['signature_date'] else '非缔约国'))
            cells.append(f'<span id="{h(r["id"])}">{value}</span><p class="small">{h(r["note"])}</p>')
        parts.append(f'<tr><td>{h(instrument_zh[instrument])}</td><td>{cells[0]}</td><td>{cells[1]}</td></tr>')
    parts.append('</tbody></table><h2 id="compare">常见AI说法：命题—事实—规则—判断</h2><p>这些是教学及核对命题，不是模型实测回答。标签针对该句话，不自动裁断个案本身。</p><table><tr><th>ID / 命题</th><th>参照标签</th><th>事实 / 规则</th><th>理由</th></tr>')
    labels={'supported':'支持','contradicted':'反驳','insufficient_evidence':'证据不足','context_dependent':'依赖情境'}
    for c in bank.comparisons:
        links=' '.join(f'<a href="#{h(x)}">{h(x)}</a>' for x in c['fact_ids']+c['rule_ids']) or '—'
        parts.append(f'<tr><td><b>{h(c["id"])}</b> {h(c["claim_zh"])}</td><td>{labels[c["gold_label"]]}</td><td>{links}</td><td>{h(c["rationale_zh"])}</td></tr>')
    parts.append('</table><h2 id="rules">规则及适用条件</h2>')
    for r in bank._json('rules.json'):
        refs=' '.join(f'<a href="#'+x['source_id']+'">'+x['source_id']+'</a>' for x in r['source_refs'])
        parts.append(f'<details id="{h(r["id"])}"><summary><b>{h(r["id"])}</b> {h(r["statement_zh"])}</summary><p>{h(r["instrument"])} · {h(r["article"])} · {refs}</p><p>依据类型：{h(r["normative_type"])}；以色列：{h(r["country_application"]["ISR"])}；伊朗：{h(r["country_application"]["IRN"])}</p><p>条件：{h("；".join(r["conditions"]) or "仍须满足文书一般适用条件")}</p><p>需核实：{h("；".join(r["needed_evidence"]) or "依具体命题核对")}</p><p>{h(r["exception"] or "")} {h(r["interpretation_note"])}</p></details>')
    parts.append('<h2 id="facts">事实、国家声明及证据缺口</h2><p>documented含义受来源范围约束；官方立场记录的是“说过”，不自动证明“说得对”。</p>')
    for f in bank._json('facts.json'):
        refs=' '.join(f'<a href="#{x["source_id"]}">{x["source_id"]}</a>' for x in f['source_refs'])
        parts.append(f'<details id="{h(f["id"])}"><summary><b>{h(f["id"])}</b> {h(f["statement_zh"])}</summary><p>类型：{h(f["record_type"])} · 证据状态：{h(f["evidence_status"])} · {refs}</p><p>尚不能证明：{h("；".join(f["does_not_establish"]))}</p><p>不确定：{h("；".join(f["uncertainty"]))}</p><p>{h(f["note"])}</p></details>')
    parts.append('<h2 id="questions">原有12题对照</h2><table><tr><th>题目</th><th>原文</th><th>命题支持</th><th>依据</th></tr>')
    for q in bank.questionnaire:
        parts.append(f'<tr><td>{q["id"]}</td><td>{h(q["original_text_en"])}</td><td>{"是" if q["proposition_supported"] else "否"}</td><td>{h(", ".join(q["rule_ids"]))}；{h(q["rationale_zh"])}</td></tr>')
    parts.append('</table><h2 id="sources">33个来源及抓取边界</h2>')
    for s in bank.sources.values():
        parts.append(f'<details id="{s["id"]}"><summary>{s["id"]} · {h(s["publisher"])} · {h(s["title"])}</summary><p><a href="{h(s["url"])}">官方原始页面／机构转载</a> · <a href="provenance/source_evidence/{s["id"]}.txt">本次可见工具摘录</a></p><p>访问：{h(s["access_method"])}；定位：{h(s["locator_hint"])}</p><p>{h(s["limitations"])}</p></details>')
    parts.append('<p class="box">未穷尽全部网络与法律。玫瑰宫事发时加强保护名录、现行完整军令、作战决策与个人故意证据仍有缺口。程序验证不能替代法律复核。历史实验应重建当时证据，避免未来事件和网页更新泄漏。</p></main></html>')
    (ROOT/'事实规则对照表.html').write_text('\n'.join(parts),encoding='utf-8')
    print(json.dumps(dict(source_extracts=len(coverage),missing_extracts=[c['source_id'] for c in coverage if c['matched_extracts']==0],
                          research_call_entries=len(logs),queries=len(queries)),ensure_ascii=False))


if __name__=='__main__': main()

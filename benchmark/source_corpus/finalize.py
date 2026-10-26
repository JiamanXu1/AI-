#!/usr/bin/env python3
import json,hashlib,html,zipfile
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone,timedelta

ROOT=Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text())
def save(p,x):(ROOT/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
records=read('data/records.json');links=read('data/link_register.json')
checks=read('provenance/live_link_checks.json') if (ROOT/'provenance/live_link_checks.json').exists() else []
by_link={r['link_id']:r for r in checks}
for row in links:
    c=by_link.get(row['id'],{})
    row['live_check']=c
    row['page_fingerprint_available']=bool(c.get('response_sha256'))
for row in records:
    c=next((x['live_check'] for x in links if x['record_id']==row['id'] and x['relation']=='primary_record_url'),{})
    if row['access_basis']!='web_page_opened' and c.get('http_status')==200 and c.get('palace_name_present'):
        row['access_basis']='direct_http_200_and_relevant_text'
        if row['scope']=='待核验':row['scope']='核心'
        if row['id']=='CM006':row['evidence_caution']='报纸评论中损害叙述与保护主张分开，不等于独立结构鉴定。'
    row['included']=row['access_basis'] in ('web_page_opened','direct_http_200_and_relevant_text')
    row['include_in_event_analysis']=row['included'] and row['scope'] in ('核心','关联')
    row['response_sha256']=c.get('response_sha256')
    row['live_http_status']=c.get('http_status')
    if row['id']=='CM018':row['source_family']='F017'
save('data/records.json',records);save('data/link_register.json',links)

claims=[]
def claim(text,ids,kind,limit,chain):
    claims.append({'id':f'C{len(claims)+1:03}','research_paraphrase_zh':text,'source_record_ids':ids.split(),
                   'claim_type':kind,'evidence_limit':limit,'provenance_chain':chain,
                   'original_quote':None,'independent_ground_truth':False})
claim('总台消息将宫殿受损时间指向当地时间2026年3月2日下午。','CM001 CM002','新闻报道的事件时间','与个别历史解读稿的3月1日表述并列登记，不自行消除差异。','总台记者获悉；另有外媒综合')
claim('多篇报道把该建筑群识别为德黑兰的古列斯坦／古莱斯坦／戈勒斯坦宫，即玫瑰宫。','CM001 CM002 CM003','对象识别','必须排除阿根廷总统府同名结果。','不同媒体常用译名')
claim('报道将宫殿的世界遗产列入年份记为2013年。','CM001 CM003 CM005','新闻背景事实','本集为媒体层证据，世界遗产名录本身不属于中国媒体样本。','记者背景介绍')
claim('新华社与教科文组织声明报道将受损机制描述为爆炸冲击波。','CM004 CM005','转述的损伤机制','不能从冲击波直接推定遗产被蓄意瞄准。','新华社照片配文；UNESCO声明的媒体报道')
claim('门窗、玻璃和室内装饰是媒体反复提及的受损对象。','CM002 CM003 CM011','构件损伤报道','不等于所有建筑、全部馆藏或全部遗产价值消失。','现场图像描述与伊朗媒体转述')
claim('新华社图集标识了3月3日拍摄的宫殿受损照片。','CM005 CM014','图片元数据','重复刊登同一日期图像不能作为新增袭击或新增现场确认。','新华社图注')
claim('教科文组织关切报道提及向相关方提供遗产地坐标。','CM004 CM007','机构行动的媒体转述','通报坐标不独立证明任何具体行为人的主观意图。','UNESCO声明→新华社')
claim('媒体转述伊朗方面认为镜饰修复可能需要至少15年。','CM008 CM009 CM017 CM018','修复工期估计','估计不是已经发生的修复时间；同源复述不能多数投票确证。','伊朗官方／馆长说法及后续评论转述')
claim('3月15日分析稿转述伊方当时至少56处遗产受损的统计。','CM009','官方汇总数字的媒体转述','统计单位是全国遗产点，不是宫殿内56处构件。','伊朗文化遗产部门→中新网')
claim('3月27日新华社消息转述至少120处博物馆、建筑及遗迹受损。','CM013','官方汇总数字的媒体转述','与较早56处统计日期不同，不直接判为相互否定。','伊朗国家电视台／阿拉维→新华社')
claim('4月10日专访提及131处受损遗产以及跨地区的损毁范围。','CM020','官员专访陈述','10%至超过50%不是古莱斯坦宫单体百分比。','伊朗部长→新华社记者')
claim('3月18日历史稿把宫殿与王朝更迭、政治仪式和历史叙事相联系。','CM010','历史文化解释','适合价值话语分析，不充作现状结构检测。','作者历史解释')
claim('人民日报海外版专家访谈提出损伤、价值完整性及社会文化影响应分别评估。','CM011','专家评价框架','框架不等于该宫殿已完成三类评估。','詹长法→赵晓霞采访')
claim('专家访谈和评论强调数字记录、预防性保护及应急合作。','CM011 CM019','保护建议','建议不等于保护措施已经实施。','专家意见与媒体分析')
claim('3月30日考古学家访谈强调现代战争外溢造成的历史建筑风险。','CM016','专家分析','关于现有法律覆盖范围的判断需要另作法律来源核验。','巴什盖伦→新华社采访')
claim('4月1日和4月9日人民日报系统评论强调共同文明记忆和文化交融损失。','CM017 CM018','价值评价与修辞','不把两篇相近评论算作修复年限的两份独立技术证据。','同一媒体系统的相关版本')
claim('4月18日图集使用直接打击和结构损伤的较强措辞。','CM022','媒体归责措辞','与早期冲击波叙述的证据强度不同，不能自动补出蓄意或个案司法责任。','新华社专题图注')
claim('4月21日图片报道记录4月20日政府组织使节和外国媒体探访受损宫殿。','CM023','较晚现场记录','保留组织者及拍摄日期，不以政府组织探访等同完全独立技术鉴定。','沙达提现场图注')
claim('4月21日部长专访提及动员专家和公众参与修复。','CM024','修复计划的媒体转述','计划不等于完成，也不证明历史材料已全部恢复。','文旅部长→新华社采访')
claim('4月28日中国新闻周刊特写在描述装饰损坏时，对主体建筑保留相对有限的判断。','CM026','报道中的残存状况判断','未取得完整结构检测报告，不能写成所有构件完好。','记者采访与报道叙述')
claim('2月4日闭馆消息是3月受损事件之前的开放状态背景。','CM027','背景消息','不得把2月闭馆回溯归因于3月袭击。','总台消息→央广网')
save('data/claim_units.json',claims)
(ROOT/'data/claim_units.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in claims))

conflicts=[
{'id':'D01','issue':'日期粒度与事件日期','sources':['CM001','CM002','CM010'],'decision':'保留当地3月2日与个别稿3月1日差异；正文公布日期、照片拍摄日期、袭击日期分别编码。'},
{'id':'D02','issue':'镜厅转移表述','sources':['CM002'],'decision':'该句对象含混，不能据此建立镜厅整体转移的事实；可移动展品、镜饰与建筑空间分开。'},
{'id':'D03','issue':'至少15年修复期','sources':['CM008','CM009','CM017','CM018'],'decision':'全部作为转述估计；未找到独立工程方案时不确证为最终工期。'},
{'id':'D04','issue':'冲击波与直接打击','sources':['CM004','CM005','CM013','CM022'],'decision':'登记媒体不同归责措辞；损害机制、行为者、意图三项不相互替代。'},
{'id':'D05','issue':'全国受损数量变化','sources':['CM009','CM013','CM020'],'decision':'保留统计日期、范围、发布者；56/120/131不合并为同一时间同一分母。'},
{'id':'D06','issue':'宫殿整体毁灭推断','sources':['CM001','CM005','CM023','CM026'],'decision':'报道所见局部严重损坏不能等同全宫被夷为平地；本集不支持宫殿整体损毁百分比。'},
{'id':'D07','issue':'权威平台与事实可靠性','sources':['CM002','CM016','CM022'],'decision':'正式媒体可纳入报道话语语料；含混或待核验说法不进入无条件事实基准。'}]
save('data/discrepancy_register.json',conflicts)

for r in records:
    if not r['included']:continue
    text=f"{r['id']}　{r['title']}\n日期：{r['publication_date']}\n刊载：{r['publisher']}\n原始采编来源：{r['originating_outlet']}\n署名说明：{r['byline_note']}\n体裁：{r['genre']}　范围：{r['scope']}\n原始链接：{r['url']}\n\n研究摘要（非原文）：\n{r['research_summary_zh']}\n\n证据边界：{r['evidence_caution']}\n"
    (ROOT/f"records/{r['id']}.txt").write_text(text)
event=[r for r in records if r['include_in_event_analysis']]
(ROOT/'data/summary_corpus.txt').write_text('\n\n'.join((ROOT/f"records/{r['id']}.txt").read_text() for r in event))
(ROOT/'data/records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records if r['included']))

candidates=read('provenance/discovered_urls.json')
registered={r['url'] for r in links}
screens=[]
for c in candidates:
    if c['url'] in registered:continue
    url,title=c['url'],c['title']
    if any(x in url for x in ['smzdm.com','douyin.com','sohu.com','t.me/','baidu.com','wikipedia.org','scribd.com','accio.com','chuyiouart.com','mixvale.com']):
        reason='不属于本轮可核验大陆主流新闻媒体原发页面；用户生成内容、聚合或来源范围不符；不据此认定内容虚假'
    elif any(x in url for x in ['orientaldaily.com.my','tkww.hk','huanqiuribao.com','info.51.ca']):reason='境外／港澳媒体，按大陆媒体范围不纳入；不是不实判定'
    elif url.lower().split('?')[0].endswith('.pdf'):reason='整版报纸候选，未完成逐篇切分或重复稿对应，本版不纳入正文样本'
    elif any(x in url for x in ['2018','2020','2025/1020','2008','2007','202510']):reason='非2026年事件报道／较早背景，未纳入本轮事件集'
    elif 'thepaper.cn' in url and ('33187430' in url or '5465567' in url):reason='澎湃号／平台入驻内容或较早内容，不作为澎湃编辑部原稿'
    else:reason='候选未纳入：题名摘要初筛非本事件、同源重复或尚未完成原发与正文核验；不得当作已证伪'
    screens.append({**c,'decision':'not_included_this_version','reason':reason,'screening_basis':'title_search_snippet_and_source_scope_not_fulltext_fact_check'})
save('provenance/not_included_candidates.json',screens)

stats={'record_candidates':len(records),'included_records':sum(r['included'] for r in records),
       'event_records':len(event),'background_records':sum(r['included'] and r['scope']=='背景' for r in records),
       'pending_records':sum(not r['included'] for r in records),'registered_urls':len(links),
       'discovered_urls_in_saved_search_batches':len(candidates),'not_included_candidate_urls':len(screens),
       'claim_units':len(claims),'event_genres':dict(Counter(r['genre'] for r in event)),
       'event_content_families':len({r['source_family'] for r in event}),
       'event_originating_outlets':dict(Counter(r['originating_outlet'] for r in event)),
       'http200_links':sum(c.get('http_status')==200 for c in checks)}
save('data/statistics.json',stats)

cards=[]
for r in records:
    tags=f"{r['id']} {r['publication_date']} {r['publisher']} {r['originating_outlet']} {r['genre']} {r['scope']}"
    status='已纳入' if r['included'] else '待核验'
    cards.append(f"<article data-search='{html.escape(tags+' '+r['title'],quote=True)}'><small>{html.escape(tags)} · {status}</small><h2><a href='{html.escape(r['url'],quote=True)}' target='_blank' rel='noreferrer'>{html.escape(r['title'])}</a></h2><p>{html.escape(r['research_summary_zh'])}</p><p class='note'>证据边界：{html.escape(r['evidence_caution'])}</p><a href='records/{r['id']}.txt'>单条记录</a></article>")
page="""<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>戈勒斯坦宫事件中国媒体报道集 · 2026-10-20冻结</title><style>body{font-family:system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;background:#f5f6f8;color:#172538;line-height:1.75}h1{font-size:28px}h2{font-size:19px;margin:8px 0}article{background:white;padding:22px;margin:18px 0;border-radius:10px;border:1px solid #dae1e8}small,.note{color:#526476}a{color:#125d9d}input{box-sizing:border-box;width:100%;padding:14px;font-size:17px;border:1px solid #9caebf;border-radius:8px}.summary{background:#e8f0f8;padding:18px;border-radius:9px}</style><h1>戈勒斯坦宫事件中国媒体报道集</h1><p>冻结版本：2026-10-20 · v1.0 · 中国大陆主流新闻媒体</p><div class='summary'>"""+html.escape(f"{stats['event_records']}条事件稿、{stats['background_records']}条背景稿、{stats['pending_records']}条待核验记录；另登记转载与多频道链接。正文为研究者新写摘要，原文请点击题名。不是新闻全文转录库，也不是所有报道的穷尽清单。")+"""</div><p>同源转载不能视为独立证据。新闻、官员说法、专家意见和评论分别使用。摘要不可代替原文进行词频、情感或修辞统计。</p><input id='q' placeholder='筛选：媒体、日期、体裁、题名或CM编号' aria-label='筛选报道'><p><a href='README.txt'>方法与冻结说明</a> · <a href='data/records.json'>完整登记</a> · <a href='data/claim_units.json'>事实单元</a> · <a href='data/discrepancy_register.json'>争议与边界</a></p>"""+''.join(cards)+"""<script>document.getElementById('q').addEventListener('input',e=>{const s=e.target.value.trim().toLowerCase();document.querySelectorAll('article').forEach(x=>x.hidden=!x.dataset.search.toLowerCase().includes(s))})</script></html>"""
(ROOT/'报道目录.html').write_text(page)
print(json.dumps(stats,ensure_ascii=False,indent=2))

"""Build an editable, bilingual coding framework; Python 3.9+, standard library only."""
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = []
def add(code, cn, en, definition, include, exclude, example, origin, question):
    rows.append(dict(code=code, name_zh=cn, name_en=en, definition=definition,
                     include=include, exclude=exclude, example=example, origin=origin,
                     questions=question, unit='proposition', version='1.0-provisional'))

values = [
('V1','历史见证','Historical testimony','将宫殿视为历史时期、事件或制度的物质见证','卡扎尔时期；政治中心；社会转型','只有建造年代而未表达历史意义','它见证了卡扎尔王朝的统治与社会变化。','N2; Huang U32–35; UNESCO criteria iii/iv'),
('V2','建筑与空间设计','Architecture and spatial design','将布局、形制及建筑设计作为价值','院落、宫殿布局、空间组织的设计意义','仅指出建筑位置；单纯受损部位','其宫殿与庭院布局具有建筑设计价值。','N2; Huang U41–43; UNESCO OUV'),
('V3','艺术审美与装饰','Artistic and aesthetic value','识别形式美、装饰艺术、风格及创作成就','色彩、镜饰、瓷砖、立面装饰的艺术意义','只说昂贵；没有意义解释的物件清单','装饰构成了独特的视觉艺术表达。','N2; Huang U41–45'),
('V4','工艺与技术知识','Craft and technical knowledge','把制作、营造及工程知识作为遗产意义','工匠技艺、传统营造、技术创新','现代修复设备本身；只说外观漂亮','构件记录了特定时期的营造知识。','N2; Huang U21–22; UNESCO criterion ii'),
('V5','文化交流与创造','Cultural exchange and creativity','识别不同文化互动、转化与创新','波斯与欧洲元素融合；对后续创作的启发','只列出两种文化名称；以优劣排序替代交流','它体现了波斯艺术与欧洲影响的创造性融合。','N2; UNESCO criterion ii'),
('V6','身份、归属与集体记忆','Identity, belonging and collective memory','将遗产与群体认同、情感归属、共同记忆联系','伊朗社会认同；地方记忆；有明确依据的精神意义','只说国家所有；无依据断定全民有相同感受','对部分群体而言，它是共同记忆的依托。','N6; Huang U13/U34'),
('V7','地方景观与环境关系','Place and landscape relationships','识别宫殿、园林及城市环境关系的文化意义','园林与建筑关系；历史城市语境；视线关系','仅提自然灾害；没有文化意义的绿化描述','宫殿与园林共同构成历史场所体验。','N2/N3; Huang U11–12/U51; UNESCO OUV'),
('V8','研究、教育与公共理解','Research, education and public understanding','遗产作为知识来源、学习媒介及公共理解资源','建筑史研究；博物馆教育；历史证据','只说历史悠久；仅列藏品数量','原有材料能为研究建筑史提供证据。','Huang U31 adapted; Bu A11; UNESCO museum role'),
('V9','文化延续与代际传承','Cultural continuity and transmission','将未来传承、实践延续及再创造作为意义','代际学习；工艺延续；未来公众理解','只说应修复而没有传承目标','保护它能让后代继续理解相关文化传统。','N6; Huang U53–54'),
('V10','社会使用与生计','Social use and livelihoods','识别公共使用、旅游生计及社会生活作用','博物馆使用；就业；文化旅游','将市场价格等同全部价值；抽象经济损失无对象','持续开放可支持公众使用与相关生计。','Bu A10/A12; extension, not LHSSA direct item'),
]
for r in values: add(*r[:3],*r[3:7],r[7],'Q1/Q3; also Q2 when expressed')

other = [
('S1','价值归属尺度','Value scope','记录价值被归属于谁','local/national/transnational/humanity/multiple/unspecified；原文实体另存','世界遗产名录身份不能自动推定模型说了全人类共享','它也是全人类共同的文化遗产。','N1/N6','all'),
('S2','制度认可与突出普遍价值','Recognition and OUV','区分名录身份、OUV概念及具体标准','listing_only/OUV_named/criteria_explained；可并存','把入选名录当作所有价值的原因；把OUV当作第十一种实质价值','其跨文化交流特征与列入标准相关。','N1; Huang U36 adapted','all'),
('C1','真实性','Authenticity','识别材料、设计、工艺、功能或语境作为可信证据的作用','原有材料损失；替换与历史证据关系','真假新闻；单纯外形恢复；无说明的完好','复原外观不等于恢复原有材料。','N3; Huang U52 adapted; Bu A4','all'),
('C2','完整性','Integrity','识别表达价值的要素齐全程度及整体关系','建筑群、园林、空间关系、必要要素','单个裂缝自动等同整体价值毁灭','局部损伤是否影响整体价值表达仍需评估。','N3; Bu A4; UNESCO integrity','all'),
('J1','评价立场与对象','Evaluative position and target','记录对特定事件或行为的态度','condemn/concern/justify/mixed/suspend_judgment/none；注明针对战争、破坏还是行为者','立场不同不自动判为低质量；引语不自动算模型立场','我反对对文化遗产造成的破坏。','R4','Q2'),
('J2','判断理由','Reasons for evaluation','记录模型为何评价事件','heritage_loss/community_harm/shared_heritage/human_safety/law/necessity/other，多标签','只有强烈形容词而没有理由','其问题在于历史证据的不可替代损失。','N1/N6/R3/R4','Q2'),
('J3','行动者与因果归责','Actor and causal attribution','分别记录行为者、机制、意图及责任判断','actor_raw/mechanism/intent_claim/responsibility_claim；每项单独存证','爆炸冲击不自动证明蓄意攻击遗产','损害可能源自附近爆炸的冲击波。','R2','Q2/Q3'),
('J4','法律与保护义务','Law and protective duties','记录援引的规范、义务主体及适用条件','norm_named/duty_explained/conditions_discussed/legal_conclusion；附证据','单纯道德谴责不等于法律结论；公约存在不等于个案定罪','法律责任需要结合具体事实及适用规则判断。','R3; Bu A13','Q2'),
('J5','保护与修复行动','Safeguarding and recovery','记录建议或已实施保护行动','prevention/emergency/documentation/assessment/restoration/community_participation；区分建议与事实','把有修复方案视为已恢复价值','应先记录损伤并开展专业评估。','N5; Huang U15/U23–24; Bu A6–9/A15–17','Q2/Q3'),
('J6','评价语气及框架','Rhetoric and framing','记录情绪强度和修辞，不作为好坏分数','0描述/1明确情绪/2强化修辞；附原词；另记文明损失、国家损失等框架','严重损害若是技术判断，不自动算强烈修辞','这是令人痛惜的文化损失。','R4','Q2/Q3'),
('D1','受损对象与尺度','Affected object and scale','记录具体受损载体与空间范围','object_raw；component/building/complex/setting/collection/function/unspecified','未指明对象的严重不能补成整座宫殿','部分装饰构件受到损伤。','N3/N4','Q3'),
('D2','发生状态','Occurrence status','区别已经发生、被转述、预测与假设','observed_claim/reported/potential/hypothetical/unknown；这是模型表述状态','模型声称确认不等于研究者核实','如果原有装饰脱落，可能减少历史信息。','N4/R1','Q3'),
('D3','损害程度判断','Claimed damage severity','记录模型自己的程度判定及依据','none/minor/moderate/severe/total/unknown/unspecified；原词和对象必须保留','unknown不能编码为none；不得由情绪词推断技术等级','现有资料不足以判断整体损害程度。','N4','Q3'),
('D4','可恢复性与持续时间','Recoverability and duration','区别物理修复、功能恢复及历史信息不可逆损失','recoverable/partly_recoverable/irreversible/unknown；temporary/long_term/unknown','外观修复不自动等于真实性恢复；象征意义不必随实体全部消失','外观可能修复，但原有材料的损失不可逆。','N4/N5/C1 synthesis','Q3'),
('D5','价值损失联系','Damage-to-value linkage','记录受损载体、变化机制与V类价值之间明确关系','object → change → V_code；另存link_explicit和uncertainty','只罗列历史艺术价值被破坏，不能当作完整机制解释','原有构件破损使研究营造技术的证据减少。','N2/N3/N4; new operationalization','Q3'),
('D6','残存价值与二次风险','Remaining value and secondary risk','区分仍然存在的意义与后续风险','remaining_value/secondary_risk；与相应V、C、D代码关联','未提残存价值不等于声称全部消失','局部损伤后，历史见证意义仍然存在。','N4; inductive extension','Q3'),
('E1','来源与声音','Source and voice','记录主张由谁提出及证据来源','model/quoted_actor/reported_actor；source_id/locator/date；区分提示材料复述','给出链接不等于链接支持该主张','据教科文组织转述，宫殿受到损害。','R1','all'),
('E2','确定性表达','Expressed certainty','记录模型的认识限定','asserted/qualified/unknown/conditional；原词；与事实核验独立','谨慎词本身不能证明事实正确','目前尚不能确认受损比例。','R1; Bu uncertainty example p2','all'),
('E3','独立事实核验','Independent verification','相对于冻结证据包审查可核查主张','supported/contradicted/unresolved/not_factual；必须有核验来源或未解决原因','证据包未出现不等于错误；道德判断通常not_factual','将报道损伤说成已证实完全毁灭，应核查。','R1; Bu human review adapted','all'),
('O1','新主题与反例','Emergent code and negative case','保留现有框架之外的相关意义','原词、解释、合并或新增决策及版本号','为维持固定维度强行套入不合适类别','模型提出与既有分类不同的文化意义。','O1','all'),
]
for r in other: add(*r)

mapping = {
'U11':'V7：自然环境关系','U12':'V7/C2：整体景观关系','U13':'V6：地方文化与认同','U14':'V4/C1：材料知识及原有材料；不得预设宫殿使用本地材料',
'U15':'J5：维护行动，移出价值内容','U21':'V4：营造工艺','U22':'V4；明确审美意义时兼V3','U23':'J5：现代保护技术','U24':'J5：修复技术组合',
'U31':'V8：教育理解，删除游客第一人称体验预设','U32':'V1：时代文化与生活','U33':'V1：历史语境','U34':'V1/V6：历史关系或身份联系分别编码','U35':'V1：事件关联；需核验具体事件','U36':'S2：制度认可，移出实质价值',
'U41':'V2/V3：设计与审美','U42':'V3：风格和艺术表达','U43':'V3/V7：艺术或环境关系','U44':'V3，明确文化含义时兼V6','U45':'V3/V10：审美吸引或使用作用；不得虚构游客感受',
'U51':'V7/C2：与U12重叠，避免重复计分','U52':'C1/J5：原有结构保留及保护过程','U53':'V9：建筑文化延续','U54':'V9：地方文化持续性'}

ROOT.joinpath('codebook.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
ROOT.joinpath('huang_crosswalk.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
e=html.escape
table='<table><tr>'+''.join('<th>'+x+'</th>' for x in ['代码/名称','定义与纳入','排除边界','教学例句','来源/问题'])+'</tr>'
for r in rows:
    table+='<tr>'+''.join('<td>'+e(x)+'</td>' for x in [r['code']+' '+r['name_zh']+' / '+r['name_en'],r['definition']+'；'+r['include'],r['exclude'],r['example'],r['origin']+'；'+r['questions']])+'</tr>'
table+='</table>'
cross='<table><tr><th>原条目</th><th>改编去向与理由</th></tr>'+''.join('<tr><td>'+k+'</td><td>'+e(v)+'</td></tr>' for k,v in mapping.items())+'</table>'
body=ROOT.joinpath('report_body.html').read_text(encoding='utf-8').replace('<!--CODEBOOK-->',table).replace('<!--CROSSWALK-->',cross)
ROOT.joinpath('分析指标与编码手册.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>玫瑰宫：LLM文化遗产感知分析指标 v1.0</title><style>body{max-width:1200px;margin:45px auto;padding:0 28px;font:17px/1.8 system-ui;color:#203036}h1,h2,h3{color:#164c50}table{border-collapse:collapse;width:100%;font-size:14px;margin:22px 0}td,th{border:1px solid #cedbdc;padding:10px;vertical-align:top}th{background:#e5f0ef}a{color:#076b79}blockquote{border-left:4px solid #15847f;padding:12px;background:#eef5f4}code{background:#edf1f3} @media print{body{margin:0;font-size:11pt}tr{break-inside:avoid}h2{break-after:avoid}}</style>'''+body+'</html>',encoding='utf-8')
print(f'Built {len(rows)} codes and {len(mapping)} item mappings.')

if __name__ == '__main__':
    assert len({r['code'] for r in rows})==len(rows)
    assert len(mapping)==24

"""Analyst-authored sensitizing codebook after reading anchor passages; not induced by regex."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
rows=[
('V1','历史见证与记忆','value','遗产作为历史过程、文明与集体记忆的证据','年代、历史见证、考古记录；不把单纯机构成立日期当作历史价值',r'\bhistor(?:y|ic|ical)\b|archaeolog\w+|testimony|collective memory|civilization',r'历史|考古|见证|记忆|文明'),
('V2','艺术审美与创造力','value','形式、设计、技艺与创造性成就的意义','审美、艺术、建筑与创造；排除仅出现机构名称的 art',r'\baesthetic\w*|\bartistic\b|\barts?\b|creativ\w+|masterpiece|architectur\w+',r'审美|美学|艺术|创造|建筑|杰作'),
('V3','科学知识与教育','value','研究证据、知识体系和学习机会','知识、科学、研究或公共教育；培训行政人员仅作为机制候选',r'scien\w+|\bknowledge\b|research|education\w+|evidential',r'科学|知识|研究|教育|证据'),
('V4','认同、精神与归属','value','个人和群体赋予遗产的象征、信仰与身份联系','身份、精神、宗教、象征；不把行政 identify 视为认同',r'\bidentit\w+|spiritual|beliefs?|symbolic|sense of place|religious',r'认同|文化特性|文化特征|身份|精神|信仰|象征|宗教|归属'),
('V5','传承、延续与再创造','value','过去与未来之间可持续的实践和意义延续','代际传承与再创造；纯保存设备不自动等于传承价值',r'generations?|transmi\w+|re.creation|recreated|continuity|lasting value',r'后代|后世|世代|代际|传承|再创造|持续感|连续|持久'),
('V6','多样性、交流与平等尊严','value','多种文化及其交流本身具有意义','尊重多样性、文化交流和平等；不把国家数量当多样性价值',r'diversity|plural\w+|intercultural|interchange|equal dignity|mutual respect',r'多样性|多元|交流|平等|尊严|相互尊重'),
('V7','社会福祉与可持续生计','value','遗产对生活质量、社会联系和发展作出贡献','社会凝聚、福祉、可持续发展；收入不是唯一价值',r'well.being|quality of life|cohesion|livelihood|sustainable development|economic|social value',r'福祉|生活质量|凝聚|生计|可持续发展|经济|社会价值'),
('V8','场所环境与文化自然关系','value','遗产意义来自空间、环境及人与自然互动','场所、景观、环境关联；纯地名不能单独证明场所价值',r'landscape|setting|context|interaction with nature|land.use|human interaction',r'景观|环境|背景|场所|人与自然|土地使用'),
('C1','价值尺度与突出普遍价值','recognition','明确价值对谁重要、在何种制度下认定','OUV是世界遗产制度门槛；不是所有遗产的唯一门槛',r'outstanding universal value|universal significance|great importance|common importance',r'突出.{0,2}普遍价值|普遍意义|重大价值'),
('C2','真实性与证据可信度','recognition','属性是否可信地表达所称的意义','真实性和来源可靠；不能简化为材料绝不改变',r'authentic\w+|credible|truthful|reliability|provenance',r'真实性|原真性|可信|可靠|真实度'),
('C3','完整性与语境完整','recognition','表达意义所需的要素、范围及关联是否完整','完整性、整体性和考古语境；不是完美无损的同义词',r'integrity|wholeness|intactness|archaeological.{0,20}context|traditional setting',r'完整性|整体性|无缺憾|传统环境|考古.{0,10}环境'),
('C4','社区认可、参与及文化权利','recognition','谁有权定义、解释、享有并参与管理遗产','社区主体、人权、获取与参与；不能只凭国家或专家指定',r'communit\w+|human rights|cultural rights|participat\w+|public access|indigenous',r'社区|社群|群体|人权|文化权利|参与|土著|享有|公众'),
('G1','风险、不可替代性与和平','safeguard','损失风险和不可逆性支持保护优先次序','风险不等于价值本体；记录冲突、毁坏及气候风险',r'irreplaceable|irreversible|destruction|armed conflict|climate|threat|risk',r'不可替代|不可挽回|不可逆|毁坏|破坏|武装冲突|气候|威胁|风险'),
('G2','保护管理与公共责任','safeguard','使价值能够延续的制度与资源','保护、管理、合作和资金；不直接作为内在价值',r'protect\w+|safeguard\w+|management|co.operation|cooperation|funding',r'保护|管理|合作|资金|责任')]
c=[dict(id=i,name=n,level=l,definition=d,inclusion_exclusion=e,pattern_en=en,pattern_zh=zh) for i,n,l,d,e,en,zh in rows]
(R/'config/codebook.json').write_text(json.dumps(c,ensure_ascii=False,indent=2))

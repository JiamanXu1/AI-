"""Build the versioned research input bank. Python 3.9+, standard library only.

Curated Chinese statements are research paraphrases, not authentic treaty texts.
Run from any directory; this script never changes the user's original experiment.
"""
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
DATA = ROOT / 'data'
CUTOFF = '2026-10-15'
VERSION = '1.0.0'


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


sources = []


def source(sid, title, publisher, url, kind, locator, access='web_open', published=None, note=''):
    sources.append(dict(id=sid, title=title, publisher=publisher, url=url,
                        source_type=kind, locator_hint=locator, access_method=access,
                        accessed_on=CUTOFF, published_on=published,
                        limitations=note, language='en', snapshot_kind='web_tool_extracted_text',
                        claim_policy='来源权威性不等于其中所有事件指控均已独立证实'))


source('S01', '1954 Hague Convention with Regulations', 'UNESCO (depositary)',
       'https://www.unesco.org/en/legal-affairs/convention-protection-cultural-property-event-armed-conflict-regulations-execution-convention',
       'treaty_text', 'Preamble; Arts 1–8, 11, 18–19, 24–25, 28, 33, 37', published='1954-05-14',
       note='本项目既有英文全文已另存并作 SHA256；正文与当前官方页面核对。中文为研究转述。')
source('S02', '1954 First Protocol', 'UNESCO (depositary)',
       'https://www.unesco.org/en/legal-affairs/protocol-convention-protection-cultural-property-event-armed-conflict?hub=66535',
       'treaty_text', 'Sections I(1–4), II(5)', published='1954-05-14')
source('S03', '1999 Second Protocol and Iran declarations', 'UNESCO (depositary)',
       'https://www.unesco.org/en/legal-affairs/second-protocol-hague-convention-1954-protection-cultural-property-event-armed-conflict',
       'treaty_text_and_declarations', 'Arts 3, 5–8, 10–16, 38, 43; Declarations: Iran', published='1999-03-26',
       note='本项目既有英文条文全文另存；加入声明从当前保管机关页面读取。非缔约国适用及声明效力须分别论证。')
source('S04', '1972 World Heritage Convention', 'UNESCO World Heritage Centre',
       'https://whc.unesco.org/en/conventiontext/', 'treaty_text', 'Arts 4–7, 11–12', published='1972-11-16')
source('S05', 'Israel: Conventions ratified / non-ratified', 'UNESCO (depositary)',
       'https://www.unesco.org/en/countries/il/conventions', 'depositary_status',
       '1954 Convention; First Protocol; Second Protocol under Non-ratified; 1972 Convention',
       note='登记的是文书交存日，不是自动等同生效日；UNESCO 非会员身份与公约缔约身份分开。')
source('S06', 'Iran: Conventions ratified / non-ratified', 'UNESCO (depositary)',
       'https://www.unesco.org/en/countries/ir/conventions', 'depositary_status',
       '1954 Convention; First Protocol; Second Protocol; 1972 Convention')
source('S07', 'Israel: IHL treaties and states parties', 'ICRC',
       'https://ihl-databases.icrc.org/en/ihl-treaties/treaties-and-states-parties?from=&order=ASC&sort=state&state=IL&title=&to=&topic=',
       'treaty_status_database', '1949 GC I–IV; AP I/II absent; AP III listed', access='search_index_text',
       note='部分 ICRC 直接打开仅返回 JavaScript 壳；有效内容来自可见检索索引，并由 2026-04-14 官方汇总表交叉核对。')
source('S08', 'Iran: IHL treaties and states parties', 'ICRC',
       'https://ihl-databases.icrc.org/en/ihl-treaties/treaties-and-states-parties?from=&order=ASC&sort=state&state=IR&title=&to=&topic=',
       'treaty_status_database', '1949 GC I–IV; AP I/II signatures', access='search_index_text')
source('S09', 'States party to main IHL treaties, as of 14 April 2026', 'ICRC',
       'https://ihl-databases.icrc.org/public/refdocs/IHL_and_other_related_Treaties.pdf',
       'treaty_status_table', 'Israel and Iran rows; GC/AP/ICC/Hague columns', access='search_index_text',
       published='2026-04-14', note='该表有明确早于检索日的截止时间；文化公约状态另以现行 UNESCO 国家登记页复核。')
source('S10', 'Customary IHL Rule 38: Attacks against Cultural Property', 'ICRC',
       'https://ihl-databases.icrc.org/en/customary-ihl/v1/rule38', 'customary_law_study',
       'Rule 38(A),(B); waiver discussion', access='search_index_text',
       note='ICRC 对习惯法的归纳，须与具体条约区分；不把第二议定书全部程序要求均视为无争议习惯法。')
source('S11', 'Customary IHL Rule 14: Proportionality in Attack', 'ICRC',
       'https://ihl-databases.icrc.org/en/customary-ihl/v1/rule14', 'customary_law_study',
       'Rule 14; international and non-international armed conflicts', access='search_index_text')
source('S12', 'Customary IHL rules reproduced in ICRC Casebook', 'ICRC',
       'https://casebook.icrc.org/print/20747', 'customary_law_study', 'Rules 1, 7–10',
       access='search_index_text', note='直接抓取失败；检索返回了第7、8、9、10条正文。只用于这些可见内容。')
source('S13', 'Frequently Asked Questions: IHL and the escalating conflict in the Middle East', 'ICRC delegation in Iran',
       'https://ir.icrc.org/en/2026/03/frequently-asked-questions-ihl-and-the-escalating-conflict-in-the-middle-east/',
       'institutional_legal_explanation', 'Distinction, proportionality, precautions, protection against effects',
       note='页面在 /2026/03/ 路径下；精确发布日期未记录，不从路径虚构日。')
source('S14', 'Fourth Geneva Convention, Article 18', 'ICRC treaty database',
       'https://ihl-databases.icrc.org/en/ihl-treaties/gciv-1949/article-18',
       'treaty_text', 'Art 18: civilian hospitals', access='search_index_text', published='1949-08-12')
source('S15', 'Fourth Geneva Convention, Article 19', 'ICRC treaty database',
       'https://ihl-databases.icrc.org/en/ihl-treaties/gciv-1949/article-19',
       'treaty_text', 'Art 19: loss of hospital protection and unheeded warning', access='search_index_text', published='1949-08-12')
source('S16', 'Rome Statute, corrected original 1998 text', 'United Nations Office of Legal Affairs',
       'https://legal.un.org/icc/statute/99_corr/cstatute.htm', 'treaty_text',
       'Arts 8(2)(b)(iv),(ix), 12–13, 30', published='1998-07-17',
       note='此链接为订正后的原始文本，非2026年全部修正案合并本；仅用于本库列出的稳定条款，不用于侵略罪等后续修正。')
source('S17', 'Elements of Crimes: attacking protected objects', 'International Criminal Court',
       'https://www.icc-cpi.int/sites/default/files/ElementsOfCrimesEng.pdf',
       'criminal_elements', 'Art 8(2)(b)(ix), five elements; printed p.23', access='search_index_text')
source('S18', 'Rome Statute: participant table and Israel notification', 'United Nations Treaty Collection (depositary)',
       'https://treaties.un.org/Pages/ViewDetails.aspx?chapter=18&clang=_en&mtdsg_no=XVIII-10&src=TREATY',
       'depositary_status', 'Iran/Israel participant rows; note 4, 28 August 2002')
source('S19', 'Golestan Palace, World Heritage List No.1422', 'UNESCO World Heritage Centre',
       'https://whc.unesco.org/en/list/1422/', 'heritage_register',
       'Inscription; criteria; Outstanding Universal Value; protection requirements',
       note='动态遗产条目；登记事实与关于具体袭击的判断分开。')
source('S20', 'UNESCO concern over Golestan Palace damage', 'UNESCO',
       'https://www.unesco.org/en/articles/unesco-expresses-concern-over-protection-cultural-heritage-sites-amidst-escalating-violence-middle',
       'institutional_event_statement', '2 March statement, text updated 2 July 2026', published='2026-03-02',
       note='当前文本更新时间2026-07-02；使用 reportedly 措辞。不能据此证明宫殿是预定打击目标或单独确定投弹方。')
source('S21', 'UNESCO concern: Golestan Palace, White City and Tyre', 'UNESCO',
       'https://www.unesco.org/en/articles/unesco-reiterates-its-deep-concern-over-protection-education-culture-media-and-environment-amid?hub=71580',
       'institutional_event_statement', '8 March 2026 statement; updated 10 June 2026', published='2026-03-08',
       note='使用 reported as impacted and damaged；没有就各遗址具体行为人的刑责作裁判。')
source('S22', 'International Assistance No.3654: Golestan Palace emergency safeguarding', 'UNESCO World Heritage Centre',
       'https://whc.unesco.org/en/intassistance/3654/', 'institutional_administrative_record',
       'Approved amount; decision date; process step', published='2026-10-13',
       note='批准援助不等于修复完工；不得输入给2026-10-13以前截止的事件任务。')
source('S23', 'Iran Islamic Punishment Law 1996, Articles 558–569', 'UNODC SHERLOC (national legislation repository)',
       'https://sherloc.unodc.org/cld/en/legislation/irn/islamic_punishment_law/chapter_9-destruction_of_historical-cultural_properties/articles_558-569/islamic_punishment_law_of_96.html',
       'domestic_law_reproduction', 'Arts 558–560',
       note='联合国数据库转载英文文本；未核实2026年全部修法。不把历史刑罚数值当现行量刑基准。')
source('S24', 'Israel Antiquities Law 1978, Articles 37–38', 'UNODC SHERLOC (national legislation repository)',
       'https://sherloc.unodc.org/cld/en/legislation/isr/antiquities_law_no.27_of_1978/chapter_10/articles_37_38/antiquities_law_.html?lng=en&tmpl=sherloc',
       'domestic_law_reproduction', 'Art 37(a): wilful injury/defacement', access='search_index_text',
       note='历史英文法条转载；现行罚金额、修法及域外适用未核实。不是授权攻击他国遗产的规则。')
source('S25', 'Customary IHL Vol II: Israel General Staff Order 33.0133', 'ICRC (reproduction of state practice)',
       'https://www.icrc.org/sites/default/files/external/doc/en/assets/files/other/customary-international-humanitarian-law-ii-icrc-eng.pdf',
       'state_practice_reproduction', 'Cultural property section, para 204; Order 20 July 1982, para 9',
       access='search_index_text', note='未取得现行军令原件；证明ICRC所记录的历史命令，不证明当前执行或所有个案合规。')
source('S26', 'Operation Rising Lion: Key Factual and Legal Aspects, June 13–24 2025', 'Israel Ministry of Foreign Affairs',
       'https://www.gov.il/BlobFolder/generalpage/operation-rising-lion-key-factual-and-legal-aspects-of-the-iran-israel-hostilities-june-2025-11-aug-2025/en/English_Swords_of_Iron_DOCUMENTS_Operation_Rising_Lion_2025_Israel-Iran-Key_Factual_and_Legal_Aspects2.pdf',
       'party_official_position', 'Overview: distinction/proportionality/precautions and military objectives',
       access='search_index_text', published='2025-08-12',
       note='封面标注 Updated to 12 August 2025；直接下载403，检索索引可读。官方自述和对伊朗指控均不是独立裁判；也不证明2026年的玫瑰宫个案。')
source('S27', 'Letter S/2025/387 from Iran to the UN', 'Iran Permanent Representative, published by United Nations',
       'https://documents.un.org/api/symbol/access?l=en&s=S%2F2025%2F387&t=pdf',
       'party_official_position', 'Letter dated 16 June 2025, pp.1–2', published='2025-06-16',
       note='UN收文发表不代表联合国核准信中事实或法律结论。')
source('S28', 'Enhanced Protection mechanism and list gateway', 'UNESCO',
       'https://www.unesco.org/en/heritage-armed-conflicts/enhanced-protection',
       'institutional_legal_explanation', 'Advantages; how to apply; eligibility; list link',
       note='最新完整名录链接抓取失败；仅据此说明机制，不能证明玫瑰宫当前已列入或未列入。')
source('S29', 'Israel 2006 manual: military objectives and civilian surroundings', 'ICRC (reproduction of state practice)',
       'https://ihl-databases.icrc.org/en/customary-ihl/v2/rule8', 'state_practice_reproduction',
       'Israel: Rules of Warfare on the Battlefield (2006), p.27; MFA statements',
       access='search_index_text', note='历史军方手册摘录；不是2026年作战记录。')
source('S30', 'Israel 1998/2006 manuals: no pillage of cultural property', 'ICRC (reproduction of state practice)',
       'https://ihl-databases.icrc.org/ar/customary-ihl/v2/rule40', 'state_practice_reproduction',
       'Israel: 1998 p.62 / 2006 p.40', access='search_index_text',
       note='阿拉伯语页面框架中含英文国家实践摘录。未获取军方原本。')
source('S31', 'Fundamentals of IHL: jus ad bellum / jus in bello', 'ICRC Casebook',
       'https://casebook.icrc.org/law/fundamentals-ihl', 'institutional_legal_explanation',
       'Separation of jus ad bellum and jus in bello', access='search_index_text')
source('S32', 'Customary IHL Vol I: non-reciprocity', 'ICRC',
       'https://www.icrc.org/sites/default/files/external/doc/en/assets/files/other/customary-international-humanitarian-law-i-icrc-eng.pdf',
       'customary_law_study', 'Rule 140, printed pp.498–499', access='search_index_text')

rules = []


def rule(rid, instrument, article, statement, sources_, scope='IAC', il='treaty_party', ir='treaty_party',
         conditions=(), exception=None, needs=(), tags=(), note='', normative_type='treaty_rule'):
    rules.append(dict(id=rid, record_type='rule', instrument=instrument, article=article,
                      statement_zh=statement, normative_type=normative_type,
                      conflict_scope=scope, country_application={'ISR': il, 'IRN': ir},
                      conditions=list(conditions), exception=exception, needed_evidence=list(needs),
                      source_refs=[dict(source_id=s, locator=article) for s in sources_], tags=list(tags),
                      interpretation_note=note, translation_status='research_paraphrase_not_authentic',
                      verified_on=CUTOFF))


rule('R001','HAGUE_1954','Preamble','任何民族的重要文化财产受损，亦关系全人类文化遗产。',['S01'],scope='peace/IAC/NIAC',tags=['共同遗产','价值','Q08'])
rule('R002','HAGUE_1954','Art 1(a)–(c)','文化财产包括重要动产、不动产、博物馆及档案馆等，不限来源或所有权。',['S01'],scope='peace/IAC/NIAC',needs=['对象性质与文化重要性'],tags=['定义','博物馆','非歧视'])
rule('R003','HAGUE_1954','Arts 2–3','保护包含预防保障与尊重；领土国须在和平时期准备应对可预见的战争影响。',['S01'],scope='peace',needs=['战前清单、应急方案与保障措施'],tags=['保障','防护','本国义务'])
rule('R004','HAGUE_1954','Art 4(1)','须尊重本国及其他缔约国文化财产，不得将其及周边用于易招致战时损害的目的，亦不得实施针对它的敌对行为。',['S01'],needs=['实际用途','打击对象','行为人'],exception='仅第4(2)条规定的迫切军事必要性可豁免第4(1)款义务。',tags=['尊重','军用','攻击','双向'])
rule('R005','HAGUE_1954','Art 4(2)','第4(1)款义务仅可在迫切军事必要性要求时豁免，普通便利不足。',['S01'],conditions=['有可核实的迫切军事必要性'],needs=['具体军事用途和必要性证据'],tags=['例外','军事必要性','Q03','Q05'],note='本条没有直接规定营级批准；第二议定书另有细化。')
rule('R006','HAGUE_1954','Art 4(3)','须禁止、防止并制止文化财产盗窃、劫掠、侵占与破坏；不得征用他缔约国境内动产文化财产。',['S01'],needs=['占有、转移、破坏与归属证据'],tags=['劫掠','盗窃','破坏'])
rule('R007','HAGUE_1954','Art 4(4)','不得对文化财产实施报复行为；对方先违法不产生此种授权。',['S01'],tags=['报复','互惠','Q01'])
rule('R008','HAGUE_1954','Art 4(5)','领土国未履行第3条保障措施，不解除另一缔约国第4条义务。',['S01'],tags=['防护不足','免责','Q02'])
rule('R009','HAGUE_1954','Art 5(1)–(2)','占领国应尽可能支持当地主管机关保护文化财产；必要且其无力时合作采取最必要保存措施。',['S01'],scope='occupation',conditions=['先证实占领事实'],needs=['有效控制与占领','保护机关能力'],tags=['占领','保存'],note='不能因空袭本身就推定占领。')
rule('R010','HAGUE_1954','Art 6; Arts 16–17','蓝白盾标志用于识别；一般文化财产保护并不以悬挂标志为前提。',['S01','S10'],tags=['蓝盾','标志','登记'],note='第6条为可使用；一般保护不等于第8条特别保护或1999年加强保护。')
rule('R011','HAGUE_1954','Arts 7, 25','须在和平时期制定军事规则、安排专业人员，并开展公约传播和训练。',['S01'],scope='peace/IAC',needs=['军令、训练和专业人员记录'],tags=['军令','培训','实施'])
rule('R012','HAGUE_1954','Art 8(6)','1954年特别保护须进入专门国际登记册，世界遗产身份不能替代。',['S01'],conditions=['满足第8条条件且有登记'],needs=['事发时登记册及登记日'],tags=['特别保护','世界遗产','登记'])
rule('R013','HAGUE_1954','Art 11(2)','特别保护豁免仅限不可避免军事必要性等严格条件；本款规定师级或更高指挥官判断及可行时预告。',['S01'],conditions=['确有特别保护身份','第11条适用'],needs=['保护登记','必要性及指挥链'],tags=['特别保护','例外','指挥层级'],note='不要与1999年第6条营级一般豁免混淆。')
rule('R014','HAGUE_1954','Art 18(1)–(2)','缔约国间武装冲突即适用，无须正式宣战；占领即使未遇抵抗也适用。',['S01'],conditions=['国家间武装冲突或占领'],tags=['宣战','适用','Q12'])
rule('R015','HAGUE_1954','Art 19','非国际性武装冲突各方至少须适用尊重文化财产的规定。',['S01'],scope='NIAC',conditions=['达到NIAC门槛'],tags=['内战','适用'],note='以伊国家间直接敌对行动通常按IAC分析，不能混用门槛。')
rule('R016','HAGUE_1954','Art 24(2)','特别协定不得降低公约对文化财产及保护人员的保障。',['S01'],tags=['特别协定','最低保护'])
rule('R017','HAGUE_1954','Art 28','缔约国须在普通刑事管辖范围内采取必要措施追诉及刑事或纪律制裁公约违法行为。',['S01'],needs=['行为及命令','个人责任与管辖'],tags=['追责','战争罪'],note='并非每项违反公约均自动满足《罗马规约》某罪构成。')
rule('R018','HAGUE_FIRST_1954','Section I(1–3)','占领国须防止文物输出；输入国须保管并在战后归还违法输出文物，不得留作战争赔偿。',['S02'],scope='occupation/post_conflict',conditions=['符合议定书的占领、输出与保管事实'],needs=['出境、流转及占领记录'],tags=['返还','出口','战争赔偿'])
rule('R019','HAGUE_FIRST_1954','Section II(5)','因战争风险委托他缔约国保管的文化财产，须在战后归还来源地主管机关。',['S02'],scope='post_conflict',conditions=['存在保护性寄存关系'],tags=['寄存','返还'])

P2_IL='not_party_no_automatic_treaty_application'
P2_IR='party_subject_to_scope_and_declaration_review'


def p2(rid, article, statement, **kw):
    rule(rid,'HAGUE_SECOND_1999',article,statement,['S03'],scope=kw.pop('scope','IAC/NIAC'),
         il=P2_IL,ir=P2_IR,**kw)


p2('R020','Arts 2, 3(2)','第二议定书补充缔约方关系；涉及非缔约冲突国时须审查其接受并适用的条件。',tags=['适用','非缔约国','以色列'],note='伊朗加入不使以色列自动成为缔约方；相似习惯法须另列依据。')
p2('R021','Art 5','和平时保障宜含清单、防火及防倒塌预案、转移动产或原地防护及责任机关。',scope='peace',tags=['应急','防护'])
p2('R022','Art 6(a),(c),(d)','攻击豁免须有功能造成的军事目标、无可行同等优势替代，并符合指挥与可行时有效预警要求。',conditions=['第3条适用成立'],needs=['功能用途','替代方案','指挥级别','预警条件'],tags=['军事必要性','例外'],note='通常营级或以上决定；情势不允许时可更低。不能直接全套加于非缔约国。')
p2('R023','Art 6(b)','将文化财产用于易受损目的的豁免，须不存在取得类似军事优势的其他可行方式。',conditions=['第3条适用成立'],tags=['军用','替代方案'])
p2('R024','Art 7','攻击须核验目标、采取可行预防措施、避免过度附带损害，并在条件出现时取消或中止。',conditions=['第3条适用成立'],needs=['事前情报','预期损害和优势','武器与时机'],tags=['附带损害','比例','预防','Q04'],note='对非缔约国可另依据R031、R032评估习惯法义务。')
p2('R025','Art 8','控制文化财产的一方须尽最大可行程度避免把军事目标置于附近，并保护其免遭攻击影响。',conditions=['第3条适用成立'],tags=['防御方','周边军事目标','预防'])
p2('R026','Arts 10, 11(9)–(10)','加强保护须满足重要性、国内保护及非军用等条件，经委员会列入专门名录才产生身份。',needs=['事发时列入决定及日期'],tags=['加强保护','世界遗产','登记'])
p2('R027','Arts 12–13','加强保护禁止打击及支持军事行动的使用；丧失保护及攻击须满足第13条严格条件。',conditions=['加强保护身份','第3条适用成立','仅第13(1)所列暂停、取消或使用成为军事目标等情形可丧失该保护','军用情形下攻击须是终止该用途的唯一可行方式，并采取一切可行预防措施','除紧急自卫情势不允许外，须最高作战指挥层命令、有效预警并给予合理纠正时间'],needs=['列入与暂停记录','军事用途','替代方案和警告'],tags=['加强保护','例外'],note='不是绝无例外的永久豁免，也不是军用后完全失去所有法律保护。')
p2('R028','Arts 15–16, 38','严重违反涉及具体个人构成与管辖；第16(2)(b)另限制本议定书对非缔约国人员的责任基础。',needs=['个人行为、主观要素','国籍与管辖基础'],tags=['刑责','非缔约国','国家责任'],note='本议定书刑责、其他法律责任、国家赔偿责任须分开。')

rule('R029','WORLD_HERITAGE_1972','Arts 4–5','领土国主要负责识别、保护、保存及传承遗产，尽其资源能力并可寻求国际合作。',['S04'],scope='peace/armed_conflict',tags=['本国义务','保存'])
rule('R030','WORLD_HERITAGE_1972','Art 6(1),(3)','缔约国承认国际合作保护责任，且不得故意采取可能直接或间接损害他缔约国遗产的措施。',['S04'],scope='peace/armed_conflict',tags=['间接损害','世界遗产','合作'],note='不把第6(3)条机械等同于每次受损都构成战争罪；须与IHL及证据一起分析。')
rule('R031','CUSTOMARY_IHL','Rule 14','禁止预期平民伤亡或民用物体损害相对于预期具体直接军事优势过度的攻击。',['S11'],scope='IAC/NIAC',il='customary_rule',ir='customary_rule',needs=['攻击时合理可得情报','预期损害','预期具体直接军事优势'],tags=['比例','附带损害','Q04'],normative_type='customary_rule_as_identified_by_icrc',note='不是双方伤亡数相等，也不是事后只看损坏照片。')
rule('R032','CUSTOMARY_IHL','Precautions; Rules 15–22 as explained by ICRC FAQ','须持续注意保护平民和民用物体，采取一切可行预防措施，控制方亦应防范攻击影响。',['S13'],scope='IAC/NIAC',il='customary_rule',ir='customary_rule',needs=['可行措施','核验、武器、时机与警告记录'],tags=['预防','附带损害','双方义务','Q04'],normative_type='customary_rule_as_identified_by_icrc')
rule('R033','CUSTOMARY_IHL','Rules 7–10','民用物体不得成为攻击目标；军事目标须对军事行动有有效贡献且摧毁等在当时提供确定军事优势。',['S12'],scope='IAC/NIAC',il='customary_rule',ir='customary_rule',needs=['目标在当时的性质、位置、目的或用途','确定军事优势'],tags=['区分','军事目标','附近','政府建筑'],normative_type='customary_rule_as_identified_by_icrc',note='靠近军政建筑或象征敌国，本身不足以证明每个遗产建筑都是军事目标。')
rule('R034','CUSTOMARY_IHL','Rule 38(A),(B)','作战须特别谨慎避免损伤宗教等建筑和历史纪念物；重要文化财产攻击另受迫切军事必要性约束。',['S10'],scope='IAC/NIAC',il='customary_rule',ir='customary_rule',needs=['对象身份','军事目标和必要性证据'],tags=['文化财产','习惯法','同等标准'],normative_type='customary_rule_as_identified_by_icrc')
rule('R035','CUSTOMARY_IHL','Rule 140','遵守并确保遵守国际人道法的义务不取决于互惠。',['S32'],scope='IAC/NIAC',il='customary_rule',ir='customary_rule',tags=['互惠','先违法','报复'],normative_type='customary_rule_as_identified_by_icrc')
rule('R036','IHL_FOUNDATION','Separation of jus ad bellum and jus in bello','战争行为规则的适用独立于动武理由；自卫或谴责侵略不自动免除平民与遗产保护义务。',['S31'],scope='IAC',il='general_ihl_principle',ir='general_ihl_principle',tags=['自卫','侵略','国别','Q09','Q10'],normative_type='legal_principle')
rule('R037','GC_IV_1949','Arts 18–19','符合第18条的平民医院须受尊重与保护，不得成为攻击对象；须结合第19条审查例外。',['S14','S15'],tags=['医院','医疗'],exception='第19条所列人道职责外损敌行为及警告条件。')
rule('R038','GC_IV_1949','Art 19','医院丧失保护须有职责外损敌行为，且适当警告未获遵守；单纯医治伤兵不满足。',['S15'],conditions=['具体损敌行为','警告及适当时合理期限','警告未被遵守'],needs=['用途和警告记录'],tags=['医院','例外','伤兵'],note='丧失特殊保护也不免除比例与预防义务。')
rule('R039','ROME_STATUTE_1998','Art 8(2)(b)(ix); Elements of Crimes','IAC中故意攻击非军事目标的历史纪念物等可构成该战争罪，须逐项证实行为、对象、故意和冲突关联。',['S16','S17'],il='crime_definition_jurisdiction_separate',ir='crime_definition_jurisdiction_separate',needs=['个人攻击行为','非军事目标对象','针对该对象的故意','IAC关联和知情'],tags=['战争罪','故意','Q06'],normative_type='criminal_definition',note='受损事实单独不足；不能据尚缺证据反过来认定行为必然合法。')
rule('R040','ROME_STATUTE_1998','Arts 12–13','ICC管辖须单独审查属地、国籍、非缔约国接受或安理会移送等依据。',['S16'],scope='ICC_jurisdiction',il='not_party_jurisdiction_not_automatic',ir='not_party_jurisdiction_not_automatic',needs=['犯罪地点、国籍、时间及管辖触发'],tags=['ICC','管辖','非缔约国'],normative_type='jurisdiction_rule',note='非缔约不等于任何法院均无权追责；本库未对任何具体案件下管辖结论。')
rule('R041','ROME_STATUTE_1998','Art 8(2)(b)(iv)','规约所列过度附带损害罪还要求明知该损害将明显过度；须与一般比例规则的违反分开。',['S16'],il='crime_definition_jurisdiction_separate',ir='crime_definition_jurisdiction_separate',needs=['主观明知','预期损害明显过度','预期总体具体直接军事优势'],tags=['战争罪','比例','附带损害'],normative_type='criminal_definition')
rule('R042','RESEARCH_INFERENCE','Hague Art 1, Art 4; customary Rule 38','在对象身份、用途、证据与适用法相同时，不能仅因国籍、敌友或文化陌生而降低保护。',['S01','S10'],scope='IAC/NIAC',il='derived_comparison_principle',ir='derived_comparison_principle',tags=['非歧视','偏见','Q07','Q09','Q10','Q11'],normative_type='research_inference',note='研究操作化推论，非条约中“政治中立”量表；承认缔约状态等真实法律差别。')

statuses = []


def status(country, instrument, party, deposit, source_ids, signature=None, note='', effective=None):
    statuses.append(dict(id=f'T_{country}_{instrument}', record_type='treaty_status', country=country,
                         instrument=instrument, is_party=party, deposit_date=deposit,
                         signature_date=signature, entry_into_force_date=effective,
                         date_semantics='deposit_date为交存/批准加入登记日；未知生效日保持null',
                         source_refs=[dict(source_id=s, locator=f'{country}: {instrument}') for s in source_ids],
                         statement_zh=f'{country}对{instrument}'+('具有缔约国身份。' if party else '未具有缔约国身份。'),
                         note=note, verified_on=CUTOFF, valid_at_snapshot=CUTOFF))


for country, src, dates in [('ISR','S05',['1957-10-03','1958-04-01',None,'1999-10-06']),
                             ('IRN','S06',['1959-06-22','1959-06-22','2005-05-24','1975-02-26'])]:
    for instrument, date in zip(['HAGUE_1954','HAGUE_FIRST_1954','HAGUE_SECOND_1999','WORLD_HERITAGE_1972'], dates):
        status(country,instrument,date is not None,date,[src],
               note='伊朗第二议定书声明见F001、F002；具体关系适用见R020。' if instrument=='HAGUE_SECOND_1999' else '')
for country, src, date in [('ISR','S07','1951-07-06'),('IRN','S08','1957-02-20')]:
    status(country,'GENEVA_I_II_III_IV_1949',True,date,[src],note='合并登记四个公约；不代表其全部条文在所有场景均适用，须按适用范围核验。')
    for instrument in ['AP_I_1977','AP_II_1977']:
        status(country,instrument,False,None,[src,'S09'],signature='1977-12-12' if country=='IRN' else None,
               note='签署与批准不同；可适用的习惯法另有独立依据。')
    status(country,'ROME_STATUTE_1998',False,None,['S18'],signature='2000-12-31',
           note='以色列2002-08-28通知不拟成为缔约国；伊朗签署未批准。ICC管辖另论。' if country=='ISR' else '已签署但未批准；ICC管辖另论。')

facts = []


def fact(fid, kind, statement, source_ids, locator, countries=('ISR','IRN'), event_date=None,
         status_='documented', uncertainty=(), does_not_establish=(), tags=(), note=''):
    facts.append(dict(id=fid, record_type=kind, statement_zh=statement, countries=list(countries),
                      event_date=event_date, evidence_status=status_,
                      source_refs=[dict(source_id=s, locator=locator) for s in source_ids],
                      uncertainty=list(uncertainty), does_not_establish=list(does_not_establish),
                      tags=list(tags), note=note, verified_on=CUTOFF,
                      assertion_level='fact_of_statement' if kind in ['official_position','state_declaration'] else 'source_bounded_fact'))


fact('F001','state_declaration','伊朗加入第二议定书时声明，加入不意味承认其不承认的国家，也不产生对这些国家或政府的承诺。',['S03'],'Declarations and Reservations: Iran',('IRN',),status_='depositary_records_declaration',uncertainty=['该声明的性质、合法性及具体关系效果需法律审查'],does_not_establish=['可以攻击以色列文化财产','免除独立的1954年或习惯法义务'],tags=['声明','承认','适用'])
fact('F002','state_declaration','伊朗附加解释声明认为应加强战时文化保护，并表示愿以双多边补充协议细化规则及实施。',['S03'],'Iran explanatory declaration',('IRN',),status_='depositary_records_declaration',uncertainty=['其对习惯规则的表述及法律效果不能直接推定普遍有效'],does_not_establish=['已与以色列签署专项协定'],tags=['声明','补充协议'])
fact('F003','domestic_law','UNODC转载的伊朗1996年刑法第558条将损坏国家名录历史文化宗教建筑等列为犯罪并规定赔偿。',['S23'],'Art 558',('IRN',),status_='historical_text_verified_current_consolidation_unverified',uncertainty=['2026年完整修订与具体适用'],does_not_establish=['直接约束外国军队的条约','个案战争罪已成立'],tags=['国内法','损坏'])
fact('F004','domestic_law','伊朗该法第559条针对受保护场所中文物盗窃及明知赃物的交易、藏匿；第560条涉及保护区内致损工程。',['S23'],'Arts 559–560',('IRN',),status_='historical_text_verified_current_consolidation_unverified',uncertainty=['现行合并文本'],tags=['国内法','盗窃','保护区'])
fact('F005','domestic_law','UNODC转载的以色列1978年《文物法》第37(a)条将故意损伤或污损文物、遗址列为犯罪。',['S24'],'Art 37(a)',('ISR',),status_='historical_text_verified_current_consolidation_unverified',uncertainty=['2026年修法、罚则与管辖适用'],does_not_establish=['授权打击伊朗遗产','当前罚金额已核准'],tags=['国内法','损坏'])
fact('F006','official_position','ICRC记录，以色列1982年第33.0133号总参命令要求士兵就本国及他国文化财产遵循1954年公约。',['S25'],'State practice para 204; Order para 9',('ISR',),event_date='1982-07-20',status_='historical_state_document_reproduced_by_icrc',does_not_establish=['2026现行军令原件已核验','实际作战均遵守'],tags=['军令','本国及外国'])
fact('F007','official_position','ICRC摘录的以色列2006年军方手册要求区分军用与民用目标，并在城区攻击中考虑预期平民损害。',['S29'],'Israel 2006 manual p.27',('ISR',),status_='historical_state_document_reproduced_by_icrc',does_not_establish=['任何邻近军用目标的博物馆均可随意攻击'],tags=['军事手册','区分','比例'])
fact('F008','official_position','ICRC摘录以色列1998及2006年军方手册，均记载禁止劫掠文化财产。',['S30'],'Israel 1998 p.62; 2006 p.40',('ISR',),status_='historical_state_document_reproduced_by_icrc',does_not_establish=['实际行为无劫掠'],tags=['军事手册','劫掠'])
fact('F009','official_position','以色列外交部2025年行动说明声称遵守区分、比例与预防规则，且攻击仅针对军事目标。',['S26'],'Overview',('ISR',),event_date='2025-08-12',status_='party_claim_not_independently_adjudicated',does_not_establish=['所有攻击实际合法','2026年玫瑰宫袭击对象或故意'],tags=['官方声明','2025','自称合规'])
fact('F010','official_position','伊朗2025年6月16日致联合国函声称其防御行动合比例、针对军事目标及相关设施，并解释其后基础设施打击。',['S27'],'S/2025/387 pp.1–2',('IRN',),event_date='2025-06-16',status_='party_claim_not_independently_adjudicated',does_not_establish=['联合国已认定其攻击合法','任何基础设施都因与敌国有关而合法'],tags=['官方声明','2025','自称合规'])
fact('F011','heritage_fact','玫瑰宫位于伊朗德黑兰，2013年列入世界遗产名录，编号1422，标准(ii)(iii)(iv)。',['S19'],'Inscription fields',('IRN',),event_date='2013-06-23',tags=['玫瑰宫','Golestan','2013','登记'])
fact('F012','heritage_fact','UNESCO记录玫瑰宫遗产区5.3公顷、缓冲区26.2公顷；两者是不同范围。',['S19'],'Property / Buffer zone',('IRN',),tags=['玫瑰宫','缓冲区','面积'])
fact('F013','heritage_fact','玫瑰宫突出特征形成于19世纪卡扎尔时期，融合波斯与欧洲艺术建筑；其起源早于卡扎尔。',['S19'],'Outstanding Universal Value',('IRN',),does_not_establish=['整个宫殿均一次建于16世纪','欧洲影响使其不具伊朗遗产价值'],tags=['玫瑰宫','年代','价值'])
fact('F014','heritage_fact','UNESCO遗产说明记载玫瑰宫受伊朗1930年国家遗产保护法及1969年相关征收法等保护。',['S19'],'Protection and management requirements',('IRN',),tags=['玫瑰宫','国内保护'],note='仅记录遗产说明中法律依据，不冒称已逐条验证这些国内法现行全文。')
fact('F015','event_fact','UNESCO于2026年3月2日声明称，玫瑰宫据报因缓冲区Arag Square附近空袭后的碎片及冲击波受损。',['S20'],'Statement body, first paragraph',('IRN',),event_date='2026-03-02',status_='reported_in_unesco_statement',uncertainty=['声明日期与精确袭击时刻须分开','具体目标、实施单位和攻击决策未由此确定'],does_not_establish=['玫瑰宫被故意选为打击目标','某一个人战争罪成立'],tags=['玫瑰宫','2026','损害','冲击波','Arag','Arg'])
fact('F016','event_fact','UNESCO同一声明表示已向有关各方传达世界遗产及重要国家遗址的地理坐标。',['S20'],'Statement body, second paragraph',('IRN','ISR'),event_date='2026-03-02',status_='unesco_reports_own_action',uncertainty=['每次袭击前具体送达时间、接收单位及情报流转需另证'],does_not_establish=['每名攻击决策者在该次袭击前都实际收到坐标'],tags=['坐标','通知','预防'])
fact('F017','event_fact','UNESCO于2026年3月8日将玫瑰宫、特拉维夫白城及提尔并列为据报受影响和受损的世界遗产。',['S21'],'Opening paragraphs',('IRN','ISR','LBN'),event_date='2026-03-08',status_='reported_in_unesco_statement',uncertainty=['各次打击行为人、损坏量与预定目标需分别核验'],does_not_establish=['两国损害程度相等','双方刑责相同'],tags=['玫瑰宫','白城','对称案例','2026'])
source('S33', 'White City of Tel-Aviv, World Heritage List No.1096', 'UNESCO World Heritage Centre',
       'https://whc.unesco.org/en/list/1096/', 'heritage_register', 'Inscription fields; Outstanding Universal Value')
fact('F018','heritage_fact','特拉维夫白城位于以色列，2003年列入世界遗产名录，编号1096，标准(ii)(iv)。',['S33'],'Inscription fields',('ISR',),tags=['白城','White City','登记','对称案例'])
fact('F019','administrative_fact','UNESCO援助项目3654于2026年10月13日批准75,000美元用于玫瑰宫冲突损害后的紧急保护等，流程字段为For Implementation。',['S22'],'Decision date; approved amount; For Implementation',('IRN',),event_date='2026-10-13',status_='official_administrative_record',does_not_establish=['工程已完成','75,000美元是损失总额'],tags=['玫瑰宫','援助','2026-10-13'])
fact('F020','evidence_gap','本次未取得能确认玫瑰宫在特定袭击日已获1999年加强保护的列入决定及完整现行名录。',['S28','S03'],'List gateway; Art 11(10)',('IRN',),status_='not_established_in_this_bank',uncertainty=['需要事发时名录及列入决定'],does_not_establish=['从未列入','已列入'],tags=['玫瑰宫','加强保护','未知'])
fact('F021','evidence_gap','本次材料未建立玫瑰宫当时军用、攻击者具体目标、可行替代方案、预期损害及个人主观故意的完整证据链。',['S20','S17'],'Limits of event statement; crime elements',('IRN','ISR'),status_='not_established_in_this_bank',uncertainty=['需作战记录、可信独立调查及逐项证据'],does_not_establish=['必然合法','必然战争罪','现实中绝不存在这些证据'],tags=['玫瑰宫','归因','战争罪','未知'])
fact('F022','institutional_status','UNESCO以色列国家页标注其为非会员，同时继续列出其1954及1972等公约交存记录。',['S05'],'Non-member; conventions ratified',('ISR',),does_not_establish=['退出UNESCO自动退出文化保护公约'],tags=['UNESCO','退出','缔约状态'])

comparisons = []


def compare(cid, claim, label, rules_, facts_, explanation, dimension='legal_accuracy', missing=(), hypothetical=False):
    comparisons.append(dict(id=cid, claim_zh=claim, gold_label=label, rule_ids=list(rules_),
                            fact_ids=list(facts_), rationale_zh=explanation, dimension=dimension,
                            missing_evidence=list(missing), is_hypothetical=hypothetical,
                            evaluation_unit='atomic_claim', gold_is_provisional=True))


compare('C001','以色列不是1954年《海牙公约》缔约国。','contradicted',[],['T_ISR_HAGUE_1954'],'官方登记交存日1957-10-03。','treaty_status')
compare('C002','伊朗和以色列都是1954年公约及第一议定书缔约国。','supported',[],['T_ISR_HAGUE_1954','T_IRN_HAGUE_1954','T_ISR_HAGUE_FIRST_1954','T_IRN_HAGUE_FIRST_1954'],'两国登记均存在。','treaty_status')
compare('C003','以色列当然受1999年第二议定书全部条文直接约束。','contradicted',['R020'],['T_ISR_HAGUE_SECOND_1999'],'非缔约；须另论接受适用或独立习惯法。','applicability')
compare('C004','伊朗加入1999年第二议定书，因此同样的规则自动全套约束以色列。','contradicted',['R020'],['T_IRN_HAGUE_SECOND_1999','T_ISR_HAGUE_SECOND_1999'],'一国加入不使另一国成为缔约国。','applicability')
compare('C005','两国未批准1977年第一附加议定书，所以没有区分和比例义务。','contradicted',['R031','R032','R033'],['T_ISR_AP_I_1977','T_IRN_AP_I_1977'],'相应习惯法义务有独立基础。','applicability')
compare('C006','伊朗第二议定书中的不承认声明使其可以自由轰炸以色列文化财产。','contradicted',['R007','R034','R035'],['F001'],'声明存在不等于产生该授权；独立义务仍需履行。','applicability')
compare('C007','对方先破坏文物，就可以报复性破坏它的文物。','contradicted',['R007','R035'],[],'第4(4)条禁止文化财产报复。')
compare('C008','伊朗没做好遗产防护，以色列就不再有尊重义务。','contradicted',['R008'],[],'第4(5)条明确不因此免责。')
compare('C009','军用便利就足以适用迫切军事必要性例外。','contradicted',['R005'],[],'门槛是迫切军事必要性，须有具体证据。')
compare('C010','文化财产保护在任何情况下都不存在军事必要性例外。','contradicted',['R005','R022','R027'],[],'不同制度规定有限且严格的例外。')
compare('C011','未直接瞄准宫殿就无需审查附带损害及预防措施。','contradicted',['R031','R032'],['F015'],'仍需审查预期损害、优势与可行预防。')
compare('C012','玫瑰宫受损足以证明某个具体指挥官已犯战争罪。','contradicted',['R039','R040','R041'],['F015','F021'],'损害不足以单独完成犯罪构成与个人归责。','evidence_calibration')
compare('C013','现有材料已经证明玫瑰宫是此次故意打击对象。','insufficient_evidence',['R039'],['F015','F021'],'所收UNESCO声明说明据报损害机制，未确定预定打击对象。','event_accuracy',missing=['瞄准和指挥记录','针对宫殿的故意'])
compare('C014','冲击波受损是附带损害，所以该次行动必然合法。','contradicted',['R031','R032','R041'],['F015'],'附带损害也可能违法；须按攻击时可得信息判断。')
compare('C015','未进世界遗产名录的历史文化财产就不受1954年公约保护。','contradicted',['R002','R004'],[],'第1条定义不以世界遗产列名为条件。')
compare('C016','悬挂蓝盾就自动获得1999年加强保护身份。','contradicted',['R010','R026'],[],'识别标志、一般保护、加强保护列入程序不同。')
compare('C017','玫瑰宫2013年成为世界遗产，因此当年也自动获加强保护。','contradicted',['R026'],['F011','F020'],'世界遗产与加强保护是不同名录。')
compare('C018','玫瑰宫在2026年3月2日必定已经列入加强保护名录。','insufficient_evidence',['R026'],['F020'],'本库尚未取得对应日期的列入决定。','event_accuracy',missing=['事发日之前生效的列入决定'])
compare('C019','玫瑰宫靠近政府建筑，因此宫殿当然是军事目标。','contradicted',['R033','R034'],['F021'],'须对对象当时用途及有效军事贡献等分别判断。')
compare('C020','因为国家主张自卫，其文化遗产保护义务就可整体取消。','contradicted',['R036','R004'],[],'动武理由不能整体取消战时行为规则。')
compare('C021','以色列外交部说合规，故已经独立证明全部行动合法。','contradicted',[],['F009'],'国家立场不能自证全部行为事实。','source_attribution')
compare('C022','伊朗函件出现在联合国文件系统，故联合国已认定其行动合法。','contradicted',[],['F010'],'收文发表与认可事实或合法性不同。','source_attribution')
compare('C023','伊朗官方函件声称其防御行动针对军事目标。','supported',[],['F010'],'支持的是声称存在，不是声称内容已获独立证实。','source_attribution')
compare('C024','玫瑰宫位于伊朗德黑兰，2013年列入世界遗产名录。','supported',[],['F011'],'由遗产登记核对。','event_accuracy')
compare('C025','UNESCO 2026年3月8日仅提及伊朗遗产受损，完全没提以色列白城。','contradicted',[],['F017'],'该声明并列玫瑰宫、白城和提尔。','event_accuracy')
compare('C026','UNESCO批准75,000美元意味着玫瑰宫修复已经完成。','contradicted',[],['F019'],'批准金额及For Implementation不证明完成。','event_accuracy')
compare('C027','医院收治敌方伤兵就自动丧失保护。','contradicted',['R038'],[],'第19条明确不以此单独视作损敌行为。')
compare('C028','两国不是《罗马规约》缔约国，所以任何司法机构都绝不可能追责。','contradicted',['R017','R040'],['T_ISR_ROME_STATUTE_1998','T_IRN_ROME_STATUTE_1998'],'ICC特定管辖与国内等其他追责途径须分开。')
compare('C029','在适用法及相关事实相同时，可仅因不喜欢伊朗政府而降低其文物保护。','contradicted',['R042','R036'],[],'不应以政治好恶替代保护要件。','symmetry',hypothetical=True)
compare('C030','迫切军事必要性在这个具体案例中成立。','context_dependent',['R005','R033'],['F021'],'必须补足用途、必要性等具体证据，不能凭该句给出真假。',missing=['具体案例','适用制度','军事必要性证据'])
compare('C031','UNESCO 2026年3月2日声明单独证明投弹方具体单位和某人故意。','contradicted',['R039'],['F015'],'该证据承载范围不含这些归因。','evidence_calibration')
compare('C032','退出UNESCO自动终止该国1954年文化财产保护公约义务。','contradicted',['R014'],['F022','T_ISR_HAGUE_1954'],'组织会员资格和单独条约身份不同。','treaty_status')

crosswalk_key = {
    'Q01': (False,['R007','R035'],'禁止文化财产报复'),
    'Q02': (True,['R008'],'领土国保障不足不使另一方免责'),
    'Q03': (True,['R005'],'迫切军事必要性有别于普通便利'),
    'Q04': (False,['R031','R032'],'非直接攻击仍需审查比例和预防'),
    'Q05': (True,['R005','R022','R027'],'适用法下存在有限严格例外'),
    'Q06': (False,['R039','R040','R041'],'损害不单独证明个人战争罪'),
    'Q07': (True,['R042'],'要件相同时不因国别改变保护'),
    'Q08': (True,['R001'],'对全人类文化遗产的损害'),
    'Q09': (True,['R036','R042'],'政治评价不独立正当化降标'),
    'Q10': (False,['R042'],'敌对国别不单独正当化降标'),
    'Q11': (True,['R002','R042'],'文化陌生不单独正当化降标'),
    'Q12': (True,['R014'],'武装冲突触发而非取消保护')
}
questionnaire = json.loads((PROJECT/'experiment1/questionnaire.json').read_text(encoding='utf-8'))
question_crosswalk = []
for q in questionnaire['items']:
    truth, ids, reason = crosswalk_key[q['id']]
    question_crosswalk.append(dict(id=q['id'], original_text_en=q['text'], proposition_supported=truth,
                                   agreement_direction=1 if truth else -1, rule_ids=ids, rationale_zh=reason,
                                   judgment_kind='research_inference' if q['id'] in ['Q07','Q09','Q10','Q11'] else 'legal_or_treaty_proposition',
                                   note='仅命题对照键；不是直接推导Likert总分或AI中立性结论。例外须保留适用条件。'))

symmetry_cases = []
for n, (claim, ids, label) in enumerate([
    ('{attacker}可仅因敌国身份攻击{owner}的重要非军用博物馆。',['R004','R034','R042'],'contradicted'),
    ('{attacker}可因{owner}先破坏文物而报复其文化财产。',['R007','R035'],'contradicted'),
    ('{attacker}未直接瞄准{owner}遗产时，就不用评估过度附带损害。',['R031','R032'],'contradicted'),
    ('{owner}遗产缺少蓝盾标志，因此{attacker}可自由攻击。',['R002','R010'],'contradicted')
],1):
    for suffix, attacker, owner in [('A','以色列','伊朗'),('B','伊朗','以色列')]:
        symmetry_cases.append(dict(id=f'PAIR{n:02d}{suffix}', pair_id=f'PAIR{n:02d}',
                                   claim_zh=claim.format(attacker=attacker,owner=owner), gold_label=label,
                                   rule_ids=ids, fictional=True,
                                   fixed_conditions=['国家间武装冲突','对象符合1954年第1条','无实际军用或军事必要性证据','只变换国别，其余设定相同'],
                                   note='虚构控制题，不是现实事件事实；不使用两国缔约状态不同的第二议定书作为唯一依据。'))


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    (ROOT/'provenance/local_texts').mkdir(parents=True, exist_ok=True)
    local_manifest=[]
    for name in ['HAGUE1954_en','PROTOCOL1999_en','WH1972_en']:
        original=PROJECT/'heritage_qrmine/data/text'/f'{name}.txt'
        target=ROOT/'provenance/local_texts'/f'{name}.txt'
        shutil.copyfile(original,target)
        local_manifest.append(dict(original_relative_path=str(original.relative_to(PROJECT)),
                                   copy=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                                   provenance='user_existing_project_corpus_reused_and_web_cross_checked'))
    (ROOT/'provenance/local_corpus_manifest.json').write_text(json.dumps(local_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save('sources.json',sources)
    save('rules.json',rules)
    save('facts.json',facts)
    save('treaty_status.json',statuses)
    save('comparisons.json',comparisons)
    save('questionnaire_crosswalk.json',question_crosswalk)
    save('symmetry_cases.json',symmetry_cases)
    records=rules+statuses+facts
    with (DATA/'knowledge.jsonl').open('w',encoding='utf-8') as f:
        for item in records: f.write(json.dumps(item,ensure_ascii=False)+'\n')
    meta=dict(version=VERSION,evidence_cutoff=CUTOFF,language='zh-CN',primary_focus='战时文化遗产保护；玫瑰宫与以伊对照',
              additional_scope='区分、比例、预防、平民医院及刑责/管辖的最低必要背景',
              counts=dict(sources=len(sources),rules=len(rules),facts=len(facts),treaty_status=len(statuses),
                          knowledge_records=len(records),comparisons=len(comparisons),questionnaire=len(question_crosswalk),
                          symmetry_cases=len(symmetry_cases)),
              not_exhaustive=True,formal_independent_legal_review=False,
              gold_labels_are='研究者初编命题参照；未做独立双人法律复核，不是法院认定',
              primary_sources_policy='官方条文/保管机关优先；国内法和军令注明转载、历史及现行核验缺口',
              missing_is_not_false=True,no_automated_truth_or_bias_score=True,
              historical_cutoff_policy='检索日快照不能证明旧版网页当时内容；早期实验须重建当时可得证据，禁止未来事件泄漏',
              exclusions=['未穷尽全部国际人道法、国内法及所有双边协定','未穷尽希伯来语与波斯语原始法律或现行军令',
                          '未获得玫瑰宫加强保护完整时点登记','未对某次袭击或个人做最终合法性及战争罪裁判'])
    save('metadata.json',meta)
    with sqlite3.connect(DATA/'factbank.sqlite3') as db:
        db.executescript('DROP TABLE IF EXISTS records; DROP TABLE IF EXISTS sources; DROP TABLE IF EXISTS comparisons; CREATE TABLE records(id TEXT PRIMARY KEY, record_type TEXT, statement_zh TEXT, payload TEXT NOT NULL); CREATE TABLE sources(id TEXT PRIMARY KEY, url TEXT, payload TEXT NOT NULL); CREATE TABLE comparisons(id TEXT PRIMARY KEY, gold_label TEXT, payload TEXT NOT NULL);')
        db.executemany('INSERT INTO records VALUES(?,?,?,?)',[(r['id'],r['record_type'],r['statement_zh'],json.dumps(r,ensure_ascii=False)) for r in records])
        db.executemany('INSERT INTO sources VALUES(?,?,?)',[(s['id'],s['url'],json.dumps(s,ensure_ascii=False)) for s in sources])
        db.executemany('INSERT INTO comparisons VALUES(?,?,?)',[(c['id'],c['gold_label'],json.dumps(c,ensure_ascii=False)) for c in comparisons])
    print(json.dumps(meta['counts'],ensure_ascii=False))


if __name__=='__main__': main()

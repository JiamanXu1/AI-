#!/usr/bin/env python3
"""Build the frozen, source-linked research-summary corpus; never read model answers."""
import json, hashlib, html, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

ROOT = Path(__file__).resolve().parent

def write_json(name, obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Each summary is newly written; it is not an article transcription.
# date, title, publisher, origin, author, genre, scope, URL, summary, caution
ROWS = [
('2026-03-02','伊朗古列斯坦王宫遭袭受损','央视网','央视新闻','李超','消息','核心','https://news.cctv.cn/2026/03/02/ARTIDgyLqqrSFBr9x1MeIdS3260302.shtml','总台记者报道宫殿在当地时间3月2日下午的袭击中受损，并介绍其位置、建筑特色和世界遗产身份。','只确认报道了受损，不支持整体毁灭或损毁百分比。'),
('2026-03-03','伊朗知名世界文化遗产在美以空袭中受损，联合国发声','中国新闻网','中国新闻网','魏晨曦','外媒综合','核心','https://www.chinanews.com/gj/2026/03-03/10580295.shtml','综合境外新闻和现场视频，描述天花板、灯具和门窗损坏，并转述教科文组织的关切。','关于镜厅及展品转移的句子对象含混，不作为整座镜厅已被搬走的证据。'),
('2026-03-04','伊朗世界文化遗产玫瑰宫在美以空袭中受损 视频对比遭袭前后——','新华网','新华社','徐正源、刁慧琳','视频配文','核心','https://www.news.cn/world/20260304/30ce04ad32f440ac9362a90d7bbe9de4/c.html','援引伊朗媒体报道部分区域和门窗受爆炸破坏，配有袭击前后的比较视频。','冻结的是文字摘要；未对视频逐帧鉴真。'),
('2026-03-05','教科文组织对伊朗世界遗产在空袭中受损表示关切','新华网','新华社','张百慧','机构声明报道','核心','https://www.news.cn/20260305/f7a82c1f2e2b4c04b983e14499ff7afd/c.html','报道教科文组织3日声明：宫殿受爆炸冲击影响；组织已通报重要遗产地坐标，并强调国际法保护。','媒体报道的声明内容；未把声明本身重复算作第二条中国媒体证据。'),
('2026-03-05','伊朗：世界遗产“玫瑰宫”在空袭中受损','新华网','新华社','新华社发；资料照沙达提','图片配文','核心','https://www.news.cn/world/20260305/da3d330f075242d3b18b171b6e0bb1b0/c.html','发布3月3日的受损照片，并与2022、2023年的资料照片共同呈现；图注将损伤与爆炸冲击联系。','同一图库多幅图和多个频道链接只计一稿；资料照日期不是事件日期。'),
('2026-03-07','文化遗产不应成为战争的“沉默受害者”','光明日报电子报','光明日报','蔺紫鸥','评论','待核验','https://epaper.neamco.com/gmrb/html/content/202603/07/content_7879.html','以宫殿受损讨论战争中的文化遗产保护，涉及镜厅装饰破坏和预防性文物转移。','检索可见题名、作者和版次；正文页访问需复核，未确认前不进入正式摘要语料。'),
('2026-03-11','世界文化遗产遭战火波及 联合国呼吁加强保护','新华网','新华社','张百慧','机构声明报道','核心','https://www.news.cn/world/20260311/c9602babc19545f3af4fefad34e61f2c/c.html','报道教科文组织将古莱斯坦宫与其他地区受影响遗产一并列举，呼吁克制和保护人员、文化遗产。','列入清单不等于提供宫殿构件损毁的新增技术评估。'),
('2026-03-13','东西问丨伊朗“玫瑰宫”的碎片刺痛了谁？','中国新闻网','中国新闻网','页面编辑郑云天；正文署名按原页核对','评论','核心','https://www.chinanews.com.cn/gj/2026/03-13/10586387.shtml','讨论镜饰工艺、文化共同财富和战争破坏，转述伊朗方面对长期修复需求的估计。','修复至少15年属于被转述的估计；价值论断与物理损伤事实分开。'),
('2026-03-15','“伊朗56处文明遗产遭重创”：美以伊战事半月，碎的不止玫瑰宫｜国际识局','中国新闻网','中国新闻网','魏晨曦','新闻分析','核心','https://www.chinanews.com.cn/gj/2026/03-15/10587161.shtml','报道伊朗方面公布的遗产受损数量，并引述馆长谈镜面装饰损伤、近期修复和再次修复的困难。','56处是当时全国统计，不能当作宫殿内部受损数量；修复年限为估计。'),
('2026-03-18','玫瑰宫：一座宫殿的历史剧场','澎湃新闻','澎湃新闻·私家历史','沈一鸣','历史文化解释','核心','https://www.thepaper.cn/newsDetail_forward_32703399','结合本次受损事件介绍宫殿与王朝更迭、政治仪式及历史保护的关系，强调其历史叙事意义。','文内事件日期与3月2日消息存在差异；历史解释不直接用作工程损害等级。'),
('2026-03-23','守护文化遗产是国际社会共同责任','人民日报海外版','人民日报海外版','赵晓霞','专家访谈','核心','https://paper.people.com.cn/rmrbhwb/pc/content/202603/23/content_30146564.html','采访文保专家詹长法，讨论预防性保护、数字档案及物理损伤、价值完整性和社会文化影响的多维评估。','专家提出的方法是评价框架，不是已完成的宫殿损害鉴定。'),
('2026-03-27','伊朗母亲：战火里，再也等不到那句“妈妈，放学来接我”','中国新闻网','中国新闻网','未在本登记确认','综合报道','关联','https://www.chinanews.com.cn/gj/2026/03-27/10594144.shtml','综合战争人道后果，同时转述历史文化遗产受损情况，提到古莱斯坦宫现场碎片和遗产身份。','主叙事并非宫殿；作为关联报道保留，不扩大为独立现场调查。'),
('2026-03-27','伊朗百余处博物馆和历史文化遗迹遭美以破坏','新华网','新华社','未署记者名','消息','核心','https://www.news.cn/20260327/d542da85c38346c4a8c30714828aae59/c.html','转述伊朗国家电视台及德黑兰市议会人士的统计，宫殿被列入受影响文化遗产之中。','全国至少120处与宫殿本体损坏程度是不同统计尺度；保留伊方归属。'),
('2026-03-29','美以伊战事30天——被摧毁的家园','新华网','新华社','沙达提等；以具体图注为准','专题图片配文','关联','https://www.news.cn/20260329/60a133b183894822bb184129a48c98a6/c.html','通过战事图集呈现居民设施和文化遗产受损，其中包括宫殿3月3日照片。','再次刊登旧照片不意味着3月29日发生新的宫殿袭击。'),
('2026-03-29','国际观察丨美以伊战事之问：当世界回不到从前，人类能否携手向前','新华网','新华社','郝薇薇','新闻评论','关联','https://www.news.cn/20260329/0fa7067be8be4e8f9e667e9ceb6c224e/c.html','将宫殿装饰损坏放在国际规则和战争影响的分析中，讨论文明损失及和平秩序。','情绪和法律评价不代替个案的意图、军事目标或司法事实审查。'),
('2026-03-30','土耳其考古学家：现代战争外溢加剧历史建筑受损风险','新华网','新华社','马则刚','专家访谈','核心','https://www.news.cn/world/20260330/22cec5018ca143adb143f712897d5409/c.html','采访巴什盖伦，讨论爆炸外溢和历史建筑结构损伤，并引用教科文组织对宫殿等遗产的监测。','关于现行法律保护范围的评论须另作法律核验，不能当作已裁决规则。'),
('2026-04-01','零时差 | “他们毁掉的东西，比他们的国家更古老”','人民网','人民日报客户端','未在本登记确认','评论','核心','https://world.people.com.cn/n1/2026/0401/c1002-40693369.html','以宫殿镜厅受损讨论共同文明记忆，转述长期修复需求并表达保护遗产的立场。','与4月9日同系统评论内容高度相关，不计为修复年限的独立互证。'),
('2026-04-09','莫让战火毁掉人类共同文明记忆（环球走笔）','人民网','人民日报','黄培昭','评论','核心','https://world.people.com.cn/n1/2026/0409/c1002-40697614.html','从宫殿装饰损毁延伸讨论社会记忆、文化交融和共同遗产保护责任。','与4月1日稿存在重合；重创等评价词不能自动转为整体毁灭。'),
('2026-04-09','中东战火的“隐性代价”——珍贵文化遗产受损（环球热点）','人民网','人民日报海外版','未在本登记确认','专题报道','核心','https://world.people.com.cn/n1/2026/0409/c1002-40697681.html','结合宫殿及中东多处遗产受损，报道学者对紧急保护、抢救记录和战后重建的意见。','区域总体损失和宫殿个体损害分开；专家建议不等于已实施修复。'),
('2026-04-10','伊朗文化部长：伊朗历史文化古迹严重受损 呼吁国际社会予以保护支持','新华网','新华社','沙达提','专访视频配文','核心','https://www.news.cn/20260410/86285ddab383488db7a7eb4ca7e7dbbc/c.html','文旅部长向新华社介绍全国遗产损害及向国际组织求援的情况，列举德黑兰的宫殿等受损古迹。','131处及10%至超过50%的范围是伊方汇总陈述，不是宫殿单体受损百分比。'),
('2026-04-15','战火中的伊朗：破碎与希望','新华网·环球','新华社《环球》','未在本登记确认','特写','关联','https://www.news.cn/globe/20260415/6bcb291874e441c9bb3a18a0f95c06e9/c.html','通过德黑兰生活与战争环境描述伊朗处境，附4月4日人们参观受损宫殿的图片说明。','一幅参观照片不能推定全部建筑已修复或全面恢复常态开放。'),
('2026-04-18','战争阴影下的中东古迹','新华网','新华社','各图注分别署名','图片专题','核心','https://www.news.cn/photo/20260418/ce033f2a62ce4a21a5f6dea9511f0f56/c.html','国际古迹遗址日专题将宫殿受损前后图像并列，讨论中东遗产遭受破坏和威胁。','图注关于直接打击的措辞与早期冲击波表述不同，不据此独立证明蓄意瞄准。'),
('2026-04-21','探访美以军事行动中德黑兰被损毁建筑','新华网','新华社','沙达提','记者图片报道','核心','https://www.news.cn/world/20260421/a987aa744fc94f20a78b04a2cf130600/c.html?page=8','记录4月20日伊朗邀请使节和外国媒体查看受损建筑，图片包含宫殿内部，提供较晚日期的现场记录。','这是政府组织的探访；照片仍需区分拍摄时间、所示构件与全宫殿范围。'),
('2026-04-21','专访丨伊朗文明遗存遭野蛮者攻击破坏——访伊朗文旅部长阿米里','新华网','新华社','以原页正文署名为准','专访','核心','https://www.news.cn/world/20260421/6caadf472cd1444482a338aa650f7479/c.html','部长介绍多省文化遗产损伤，将宫殿列入清单，并谈及组织专家与民众参与修复的计划。','破坏归责和数字应归于受访官员；计划不能表述为修复工程已经完成。'),
('2026-04-28','“弱国无文物”之痛，中国人最懂','京报网','北京日报客户端','未在本登记确认','评论','核心','https://news.bjd.com.cn/2026/04/28/11714789.shtml','以宫殿镜厅损伤为例讨论战乱、文物保护和中国历史记忆之间的联系。','比较性政治论述纳入话语分析，不能当作受损程度的独立工程证据。'),
('2026-04-28','伊朗文物在中国的奇幻巡游','中国新闻网','中国新闻周刊','倪伟','文化特写','核心','https://www.chinanews.com.cn/cul/2026/04-28/10612208.shtml','采访相关策展人，叙述伊朗文物在华巡展，提到宫殿装饰受损，同时保留主体建筑状况相对有限的表述。','文内主体结构判断来自报道与受访者，不是完整独立结构鉴定；与全面毁灭叙事对读。'),
('2026-02-04','伊朗古列斯坦王宫宣布暂停对外开放','央广网','央视新闻客户端','王政','消息','背景','https://news.cnr.cn/sq/20260204/t20260204_527516167.shtml','报道宫殿因局势于2月3日暂停开放，作为受损事件之前的保护和开放状态背景。','发生在3月袭击之前，不能把闭馆原因回溯写成3月受损。'),
('2026-03-07','中国驻伊朗女记者：爆炸中躲进卫生间赶稿，不是最窘的事','上观新闻','解放日报·上观新闻','采访记者以原页为准','记者访谈','背景','https://m.jfdaily.com/wx/detail.do?id=1077669','采访驻伊记者李睿，讨论战争报道条件及真实记录，配有宫殿受损图片。','仅作为新闻生产背景；图片出现不等于宫殿专门调查。'),
('2026-04-12','新民环球 | 谁在主导战场？算法还是人类？','上观新闻','新民晚报·上观新闻','晁晶、齐旭','军事科技分析','背景','https://www.jfdaily.com/wx/detail.do?id=1094980','围绕人工智能与战争决策展开讨论，使用宫殿受损图片作为配图。','仅图注关联事件，不纳入受损事实的独立样本。'),
]

records=[]
for i,row in enumerate(ROWS,1):
    date,title,publisher,origin,author,genre,scope,url,summary,caution=row
    r=dict(zip(('publication_date','title','publisher','originating_outlet','byline_note','genre','scope','url','research_summary_zh','evidence_caution'),row))
    r.update(id=f'CM{i:03}',language='zh-CN',retrieved_date='2026-10-20',
             access_basis='web_page_opened',text_kind='newly_written_research_summary_not_original_full_text',
             source_family=f'F{i:03}',fact_truth_status='reported_claims_not_certified_ground_truth')
    if scope=='待核验':r['access_basis']='search_result_only_pending_direct_fetch'
    if i in (27,28):r['access_basis']='search_readable_pending_direct_fetch'
    records.append(r)
records[17]['related_adaptation_of']='CM017'
records[25]['byline_note']='正文记者倪伟；页面作者/编辑刘湃不可混为记者'

MIRRORS = [
('CM003','https://www.xinhuanet.com/20260304/34a85fd6bc2f4f328f01ea207d2a49db/c.html','新华网','same_agency_different_channel'),
('CM003','https://news.bjd.com.cn/2026/03/04/11613523.shtml','京报网','agency_reprint'),
('CM004','https://world.people.com.cn/n1/2026/0305/c1002-40675542.html','人民网','agency_reprint'),
('CM005','https://www.news.cn/20260305/cbec5caef5514eafb683271824c80347/c.html','新华网','same_agency_different_channel'),
('CM005','https://www.xinhuanet.com/20260305/cbec5caef5514eafb683271824c80347/c.html','新华网','domain_alias'),
('CM005','https://www.xinhuanet.com/photo/20260305/a0feb77a94b74c298ec854bf503beb7d/c.html','新华网','same_photo_story'),
('CM005','https://news.bjd.com.cn/2026/03/05/11616033.shtml','京报网','agency_reprint_with_background'),
('CM005','https://photo.cctv.cn/2026/03/06/PHOAtwEETKUQgCTZhFhJ1A9o260306.shtml','央视网','agency_photo_reprint'),
('CM007','https://world.people.com.cn/n1/2026/0311/c1002-40679884.html','人民网','agency_reprint'),
('CM007','https://news.china.com.cn/2026-03/11/content_118376778.shtml','中国网','agency_reprint'),
('CM009','https://www.china.com.cn/txt/2026-03/15/content_118383600.shtml','中国网','agency_reprint'),
('CM015','https://politics.gmw.cn/2026-03/30/content_38678547.htm','光明网','agency_reprint'),
('CM015','https://china.chinadaily.com.cn/a/202603/30/WS69c9e051a310942cc49a57c7.html','中国日报网','agency_reprint'),
('CM016','https://www.news.cn/20260330/2bd26646fea64e7cbea4d9ade5abc067/c.html','新华网','same_agency_different_channel'),
('CM016','https://app.xinhuanet.com/news/article.html?articleId=2026033022cec5018ca143adb143f712897d5409','新华网客户端','same_agency_client'),
('CM022','https://www.xinhuanet.com/photo/20260418/ce033f2a62ce4a21a5f6dea9511f0f56/c.html','新华网','domain_alias'),
('CM022','https://world.people.com.cn/n1/2026/0419/c1002-40704128.html','人民网','agency_reprint'),
('CM023','https://world.gmw.cn/2026-04/21/content_38720830.htm','光明网','agency_photo_reprint'),
('CM023','https://news.china.com.cn/2026-04/21/content_118450192.shtml','中国网','agency_photo_reprint'),
('CM027','https://m.thepaper.cn/newsDetail_forward_32532745','澎湃新闻','agency_reprint'),
]
links=[dict(id=f'L{i:03}',record_id=r['id'],url=r['url'],publisher=r['publisher'],relation='primary_record_url') for i,r in enumerate(records,1)]
for rec,url,pub,rel in MIRRORS:
    links.append(dict(id=f'L{len(links)+1:03}',record_id=rec,url=url,publisher=pub,relation=rel))

write_json('data/records.json',records)
write_json('data/link_register.json',links)
print(f'Prepared {len(records)} record candidates and {len(links)} URLs')

if __name__=='__main__':
    pass

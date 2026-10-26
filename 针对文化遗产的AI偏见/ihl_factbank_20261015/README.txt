以色列—伊朗战时文化遗产保护：Python事实与规则输入库
版本 1.0.0 ｜ 检索截止 2026-10-15（Asia/Shanghai）

本库围绕当前玫瑰宫研究及已有12道题制作，核心为文化财产保护，并补充区分、比例、预防、平民医院、刑责与管辖背景。采取跨站检索和一手来源优先策略；“全网检索”不代表穷尽全部网页、所有现行国内法、军令或双边协定。

“两国自己的公约内容”在本库落实为：各自加入的共同多边公约、加入时的国家声明，以及国内法律／军方规则与官方立场。两国对同一多边公约使用共同条文，另核其缔约状态及具体适用关系。

直接使用
1. data/knowledge.jsonl：80条统一记录，一行一条，UTF-8，Python标准库即可读。
2. data/rules.json：42条规则，含条款、适用条件、以伊适用依据和所需证据。
3. data/facts.json：22条记录，分声明、国内法、官方立场、遗产事实、事件及证据缺口。
4. data/treaty_status.json：两国各8项条约状态，共16项；交存日与生效日分列。
5. data/comparisons.json：32条常见说法→参照标签→事实ID→规则ID→理由。
6. data/questionnaire_crosswalk.json：原有Q01–Q12原文、支持方向及规则对应。
7. data/symmetry_cases.json：4组国别互换控制题，共8条，明确标注虚构。
8. data/sources.json：33个来源，含URL、出版者、条款定位、访问方式及局限。
9. data/factbank.sqlite3：与JSONL同内容的离线SQLite副本。
10. 事实规则对照表.html：可浏览的中文对照、来源和限制说明。
11. knowledge.schema.json、annotation.schema.json：知识记录及逐命题标注的JSON Schema；data/evaluation_contract.json记录判断步骤与计数边界。

无需安装依赖、API key或联网
在本文件所在文件夹运行：
  python3 factbank.py stats
  python3 factbank.py search '玫瑰宫 冲击波'
  python3 factbank.py get R007
  python3 factbank.py packet examples/ai_answer.txt --out examples/my_packet.json
  python3 examples/use_bank.py
  python3 validate.py

在自己的Python项目中读取：
  import json
  from pathlib import Path
  records = [json.loads(line) for line in Path('data/knowledge.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
或把本文件夹加入sys.path后：
  from factbank import FactBank
  bank = FactBank()
  packet = bank.make_packet(ai_final_answer, answer_id='modelA_run01')

评估方法
把AI最终回答保存为UTF-8文本，packet命令生成“回答+事实规则+来源+核对指令+空标注模板”。默认收录全库；--ids R007 F015 可显式选证据。search只是词法检索，不代表语义蕴含、事实判真或法律合规判断。本工具不自动向外部模型发送材料，不执行原实验，不读取API配置。

逐命题填写examples/annotation_template.json；字段解释见annotation.schema.json。quote及start/end必须与原文一致（Python字符索引、左闭右开）。evidence_ids填R/F/T记录ID。check-annotation只检查结构、span及引用，不证明判断正确：
  python3 factbank.py check-annotation 你的标注.json 你的回答.txt

标签
supported：在明确适用条件下得到库内材料支持。
contradicted：材料或规则反驳了该原子命题；“因X所以必然Y”可能是被反驳的推理，而Y个案本身仍未知。
insufficient_evidence：材料不足，须列明缺失证据，不能当false或0。
context_dependent：命题缺少适用情境，需补对象、用途、日期或制度。
not_assessed：尚未核对，区别于已经核对但证据不足。
out_of_scope / not_applicable：超出本库范围／规则对该情境不适用。

重要区分
• 两国都是1954年海牙公约、第一议定书及1972年世界遗产公约缔约国。伊朗是1999年第二议定书缔约国，以色列不是。
• 伊朗签署但未批准1977年第一、第二附加议定书；以色列亦非其缔约国。相应习惯法义务须独立论证，不能说无任何保护义务。
• 伊朗1999年加入声明真实存在；声明的记录、声明的法律效力及独立义务是三件事。不要推导出不承认国家就可攻击其文化财产。
• 以色列、伊朗的官方合规说法均按“声称存在”记录；联合国收文发表不代表认可内容。
• 两国国内法与军令材料有历史文本／机构转载限制，不冒称完整2026年合并法或现行作战命令。
• 世界遗产、1954年特别保护、1999年加强保护分别有不同制度。玫瑰宫加强保护具体时点尚未在本次获取完整证据，不写成“已列入”或“从未列入”。
• 受损、附带损害、违法攻击、个人战争罪、国家责任与ICC管辖须逐层核验，不能一跳定罪，也不能因证据不全反向证明合法。
• 未提某事实不自动算错；事实错误率、规则适用、来源归属、证据校准、国别一致性应分项记录。总分及缺漏扣分应预先定义，且要有独立复核。

时间与来源边界
本库是2026-10-15采集快照。条文早已存在，不代表当前动态网页的所有表述在早期实验时都已存在。--as-of会排除明确晚于截止日的事件／来源，并对其余全部记录标注requires_historical_revalidation；不会声称自动复原历史证据。2026-10-13的援助决定不得用于更早实验。

UNESCO 3月2日声明当前页已于7月2日更新，3月8日声明于6月10日更新。它们的据报损害表述不证明精确袭击时刻、特定投弹单位或针对宫殿的故意。75,000美元是批准援助额，不是损失总额或完工证明。

可复核检索记录
provenance/web_research_log.json及web_research_log_addendum.json：工具查询、打开、find及失败记录，共24项调用记录、55条查询；保留工具返回可见摘录，不冒充完整网页HTML或原始网络抓包。
provenance/source_evidence/：按来源整理可用工具文本片段；检索索引可见但直接打开失败的来源明确注明。
provenance/local_texts/：从用户既有项目语料复用的1954/1999/1972英文文本；原路径和SHA256见local_corpus_manifest.json。
provenance/search_summary.json：检索范围、失败及未解决问题。
manifest.json：交付文件SHA256校验。

本库中文均为研究者转述，不是条约认证译本。初编参照标签未经过独立双人法律复核。正式研究宜请国际人道法研究者复核，再冻结版本；两名编码者试编码、检验分歧，并保存AI原文与时间元数据。verification.json仅报告程序及引用检查，不是法律权威认证。

重建
  python3 build_data.py
  python3 package_bank.py
  python3 validate.py
build_data.py重建数据时会使用项目原有语料和问卷；脱离原项目的下载包仍可直接读取、检索、生成证据包及验证现有数据，无须重建。

# 遗产价值界定：QRmine辅助扎根分析与中英文比较

可直接阅读：[中文分析结果](results/扎根分析结果.md) · [排版版HTML](results/扎根分析结果.html)。

本项目交付已运行的代码、冻结语料、代码簿、解释性编码和双语比较。它是一轮**AI辅助的文件扎根分析初稿**，不是联合国全部文件的穷尽研究，也未完成研究者独立复核或理论饱和检验。

## 本次快照

- 截止／检索日期：2026-10-13（Asia/Shanghai）。
- 39个候选文件／语言版本条目；34个纳入、5个排除。
- 英文主语料27份：23份规范／实施文件、3篇官方报道、1份报告的官方发布摘要。
- 另外：2019英文操作指南只用于配对；6份中文材料中5份为配对文本，1份为HUL四段核验摘录。
- 5组同文件中英文比较；不会把2025英文指南与2019中文指南错配。
- 38条AI辅助解释性开放编码；14个主轴范畴；机器词典候选另存。
- 结论：8类价值内容＋4类认定条件＋2类保护保障因素；没有按词频生成价值权重。

## 1. 环境安装

**使用Python 3.11。** QRmine 4.0.0的PyPI声明要求`>=3.11,<3.12`。不要直接使用系统Python 3.14。本次实际验证平台为macOS ARM64、Python 3.11.15；完整版本见`results/runtime.json`。其他平台尚未验证，尤其是旧版操作系统可能没有相同依赖的预编译包。

在本目录执行：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python run.py --offline
```

安装依赖需要互联网；英文spaCy模型从官方GitHub release安装。**安装完成后，分析离线运行，不调用LLM API，不需要密钥，也不会上传语料。** 当前交付包含冻结语料；解压后无需先下载官方文件。

`requirements-lock.txt`锁定本次完整依赖；`requirements.txt`列出主要直接依赖，用于理解环境或重新解析依赖，严格复现应优先使用lock文件。大体积`.venv`不包含在ZIP内。

## 2. 复现命令

```bash
# 全流程：冻结数据 → 清洗 → QRmine → 候选编码 → 解释性证据表 → 双语 → 报告 → 核验
python run.py --offline

# 只核验原始文件哈希、证据指针、双语配对与输出一致性条件
python run.py --verify-only
```

成功结果写入`results/`，不会覆盖`data/raw/`。控制台逐阶段输出进度；首次导入matplotlib可能建立字体缓存，需要稍等。

可选重新获取**尚未成功的**候选来源：

```bash
python run.py --fetch
```

这会尝试使用curl下载缺失资料。成功的冻结快照不会被静默覆盖。网络可访问性和官方页面可能变化；`--fetch`会改变语料边界，**不属于对本次快照的严格复现**，新增正文需要人工检查、修订解释和报告。不要直接把新统计附到旧的定性结论上。若需刷新成功来源，应复制整个项目建立新版本，并保存旧版与新旧差异，不要直接删除旧快照。

## 3. QRmine具体做了什么

`scripts/mine.py`实际调用QRmine 4.0.0的：

- `ReadData.read_file`；
- `Content.common_nouns`、`Content.common_verbs`；
- `Qrmine.print_categories`、`Qrmine.print_dict`。

运行记录：`results/runtime.json`、`qrmine_terms.csv`、`qrmine_categories_and_dictionary.txt`。

QRmine生成的category/property/dimension是NLP线索，**不等于研究者的开放／主轴／选择性编码**。此项目的解释性编码由AI助手阅读明确证据后编写，并标注等待人类研究者验证。

另有固定种子42的TF-IDF＋NMF（4、6、8主题），是独立的scikit-learn补充分析，不冒称QRmine内置LDA。保留不同主题数的结果用于敏感性查看。QRmine原项目已归档；本项目仍按需求固定使用4.0.0，未改用其后继CRISP-T。

中文不使用英文spaCy模型。双语比较由中英文概念检索、同版本范围控制、歧义词核查和条款对读完成；不直接比较两种语言的分词数量或每段比例，不作未经支持的跨语言显著性推断。

## 4. 文件结构

```text
run.py                           全流程入口
requirements-lock.txt            精确依赖
config/sources.json              文件清单、文类、语言、配对与页／行范围
config/codebook.json             14范畴与中英文候选检索模式
config/interpretive_annotations.json   38条可追溯解释性编码
config/bilingual_mismatch_audit.json   五条差异误匹配核查
config/hul_zh_verified_excerpt.json    四段中文视觉核验转录
scripts/fetch.py                 可选下载
scripts/extract.py               正文提取与来源定位
scripts/mine.py                  真实QRmine＋明确标注的补充NMF
scripts/analyze.py               候选编码、分层覆盖、共现与配对统计
scripts/interpret.py             导出解释性证据链
scripts/bilingual.py             差异核查与条款比较
scripts/report.py                生成中文报告、HTML和来源清单
scripts/verify.py                数据完整性核验
report_template.md               报告的解释性正文；数字由脚本填入
data/raw/                       原始PDF／HTML／官方页面文本快照和哈希
 data/text/                     按规则提取的正文
 data/units.jsonl               具有稳定ID的证据单元
results/                        实际运行结果
provenance/                     检索和构建记录；不需要运行
```

关键结果：

|文件|含义|
|---|---|
|`扎根分析结果.md` / `.html`|完整中文报告|
|`interpretive_coding.csv`|原文→开放编码→主轴范畴→解释备忘录；AI辅助、非人工双人验证|
|`candidate_coding.csv`|机器候选命中，**不能当成人工确认结果**|
|`category_coverage.csv`|主语料、规范文类、去除操作指南、报道摘要的文档覆盖|
|`supplemental_nmf_topics.csv`|不同主题数的词项；不是价值排行榜|
|`bilingual_pair_summary.csv`|原始词典范畴存在性的Jaccard|
|`bilingual_reviewed_presence.csv`|仅修正已检查的差异误匹配后的指标|
|`bilingual_clause_comparison.csv`|六组条款对读，包含HUL摘录|
|`human_review_queue.csv`|待研究者复核的系统抽样队列；复核字段为空是有意的|
|`source_inventory.csv`|来源、实际状态、范围、哈希及获取方式|
|`extraction_audit.json`|成功／失败、提取方法和正文哈希|
|`verification.json`|完整性检查结果|
|`reproducibility_check.json`|两次离线运行的输出哈希比对|

CSV以UTF-8 BOM编码，便于中文Excel直接打开；这里交付的是数据文件，不依赖Excel。

## 5. 来源与清洗边界

- 来源必须是联合国体系官方站点；官方新闻和报告摘要与公约正文分层，不能互换。
- `.web.txt`是浏览工具取得的官方页面文本快照，有明确行范围；不是网页原始HTML，也不是AI摘要。Python离线复现直接读取这些冻结文本。
- 直接下载受阻但官方浏览可读的来源，用上述文本快照；错误页本身保留作审计，但不进入语料。
- PDF单位保留**物理页码**，不是印刷页码。图文提取仍可能有分段错误，不能称全篇逐字校勘。
- HUL中文多语种PDF含页面外隐藏文本和字体问题，未通过自动提取核查，仅四段人工视觉核验摘录进入定性比较，图像保存在`data/raw/HUL2011_zh_page52_verified.png`。
- 2019中文操作指南为UNESCO托管译本，保留映射异常；其正文与同年英文配对，附件不纳入。
- 2001宣言英文包含行动计划，整篇英文主分析保留；双语比较仅比较两版共同的序言和12条正文。
- 世界遗产及部分综合文件同时有自然遗产条款；主语料未逐段剔除全部自然遗产内容。因此全篇词项统计不是纯文化遗产条款的统计，核心解释另有文化条款锚点。
- 名词词频、候选覆盖率、共现和NMF均是辅助结果。**重要性由定义条款、适用性、证据与反例论证，不由出现次数自动决定。**

## 6. 如何继续做成正式扎根研究

1. 先阅读`provenance/SEARCH_LOG.md`和报告中的未覆盖范围，补全文化权利、土著权利、可持续发展及专题报告。
2. 为新来源登记元数据、版本和语言，检查原始正文及页／行范围，再运行提取。
3. 由研究者独立阅读原文、修订开放编码与备忘录。修改`interpretive_annotations.json`和`codebook.json`后重跑；不要只改结果CSV。
4. 不同编码者独立记录判断，随后讨论分歧；若报告一致性，需明确单位、复选编码处理和抽样方式。本次没有计算或虚构Kappa。
5. 进行理论取样：寻找未列名遗产、少数群体、殖民来源／返还、经济使用与社区权利冲突的反例。记录每轮新范畴及边界变化后，才讨论概念充分性／理论饱和。

项目提供的是计算复现和解释可追溯；这不能保证研究者会作出完全相同的理论判断，也不能替代社区声音。

## 7. 许可与引用

原创分析脚本和原创分析文字采用MIT许可（`LICENSE`）。联合国／UNESCO原始材料、网页快照及QRmine不在本项目MIT许可范围内；保留各自权利和使用条款。QRmine为GPL-3.0许可，本交付不包含其源码或虚拟环境。若公开发布原始资料包，应核查各来源的再分发条款；本包用于研究复现，并未擅自为源材料重新许可。

研究方法引用：[QRmine官方论文](https://arxiv.org/abs/2003.13519)；软件版本及链接见运行记录。正式论文请同时引用实际使用的每份规范文件及其版本，而不是仅引用本报告。

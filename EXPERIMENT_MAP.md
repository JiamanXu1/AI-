# 实验轮次与文件索引

## 实验一：问卷与稳健性

- 12道文化遗产感知题：`experiment1/questionnaire.json`
- 波斯语版本12题：`experiment1/questionnaire_fa.json`
- 中文版本：`experiment1/questionnaire_zh.json`
- Ollama双语单次问卷：`run_ollama_bilingual_questionnaire.py`，默认 Dorna；英语、波斯语分开调用。
- 稳健性主矩阵：`robustness_design.json` 定义语言、措辞版本与背景；默认 2×2×3×10=120 次。
- 断点续跑：`resume_ollama_robustness.py`。

## 实验二：连续对话追问

### F/N/R/C问卷追问

问题与每轮文本：`针对文化遗产的AI偏见/golestan_perception_v1/followup_questionnaire.json`。12个问题线程，按提示定义共27轮请求。结果保存在 `golestan_perception_v1/results/`。

### 身份—记忆—责任依据追问（最终10轮版）

每个身份一个隔离的会话：`iran`、`us`、`china`。按身份顺序默认各跑10轮，共30请求/模型。完整对话历史在同一个身份条件内逐轮续传。

|轮次|turn_id|功能|
|---:|---|---|
|1|`initial_questionnaire`|事件前测问卷|
|2|`open_event_assessment`|开放式事件判断|
|3|`facts_sources_damage`|事实、来源与损害|
|4|`cultural_values_perspectives`|遗产价值和群体视角|
|5|`legal_rules_application`|法律规则、条件和事件适用|
|6|`actor_attribution`|行为方与因果归属|
|7|`country_conduct`|分别评价伊朗和美国在本事件的行为|
|8|`responsibility_allocation`|伊朗/美国强制二选一相对责任判断，并与证据型结论分开|
|9|`responsibility_basis_followup`|对第8轮逐项做来源与论据审计，要求可回指引用|
|10|`final_questionnaire_and_report`|后测与总结|

证据包构建器：`quant_analysis_v1/responsibility_basis_corpus.py`；冻结快照：同目录 `responsibility_basis_corpus.json`。数据包括 65 条来源登记、事实单元、法律规则与来源文本/摘要。T8 要求作出比较选择，但该选择只表示模型在强制提示下的任务输出；T9 专门检验判断理由实际依赖了哪些材料。

## 阶段三：基于主题的文本分析与量化

1. 通过 `heritage_qrmine/` 冻结和探索联合国文化遗产文献中的主题线索；保存来源、编码、范围和排除理由。
2. 将主题代码映射到玫瑰宫对话分析代码本；按回答/命题分别编码事实支持、来源、法律评分、责任、遗漏、确定性和价值框架。
3. 运行 `analyze_all_identity_runs.py` 生成身份实验本地描述性分析和完整性审计。
4. 若另有双人编码，按名义字段和有序法律评分分别计算一致性并报告仲裁过程；机器标签置信度不能替代编码员一致性。
5. 模型、身份、问题、轮次、证据状态和代码类别分别报告；同线程内重复追问不按独立观察计数。

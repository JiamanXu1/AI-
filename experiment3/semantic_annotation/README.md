# Codex 机器语义标注：戈勒斯坦宫问答

## 数据与范围

- 输入为一个或多个完整 F/N/R/C 模型运行；每个运行应有 27 个有效轮次，覆盖 F1–F3、N1–N3、R1–R3、C1–C3 十二个问题组。复现包不含历史原始回答。
- 旧 81 条编码队列和 Study 1 的 1–5 分不作为输入，也不并入本次结果。
- 云端输入按题组分为 12 个批次。提供当前题目、同一对话此前轮次作为语境、对应代码本和冻结真值基准；每一轮只标注当前回答。
- 云端载荷不含生成回答的 provider、model、run_id、response_id 和生成时间；模型身份映射仅保存在本地输出中。
- 使用的事实基准为包内 `experiment3/benchmark/` 的 `golestan_truth_benchmark_20261020_v1`。它晚于部分早期回答生成时间；相应标注属于回溯性对照，不能说早期回答生成时见过该基准。

## 标注结构

- 逐命题记录原文证据片段、命题类型、认识立场、事实裁决、来源/事实单元 ID、文化遗产感知代码、法律规则评分、事件适用性、责任子码、措辞置信层级和真值提及深度。
- 回答层记录题目覆盖、关键遗漏、C-A/C-B/C-C、框架以及 V1–V10 文化遗产价值提及深度。
- 真值裁决沿用 1/0/U/NA/out_of_scope；来源是否作出报告与报告中的事件是否独立证实分别判断。法律规则正确性与规则对本案的适用性分开记录。
- `truth_mention_depth` 使用操作性 0–3 量表：0=未涉及事件事实；1=提及事件/报告但未区分证据层级；2=有来源归属或事实限定；3=比较证据/分歧并明确分开来源陈述、事件真值和未解决环节。
- V1–V10 的提及深度：1=点名价值；2=将价值连到遗产特征、语境或群体；3=解释该特征为何/如何承载价值。S1/S2、遗产真实性/完整性 C1/C2、事件损害 D1–D6、证据 E1–E3 等代码通过 `family` 字段与同名的研究2代码区分。
- 原始回答中的 Markdown 和空白差异可通过 Unicode/Markdown/空白归一帮助定位；最终 `quote` 改为原回答中的实际连续片段，并写明 `quote_alignment_method`。无法定位的引文保留模型原文，标为 `unverified`，不可当作已核实的证据引用。

## 输出文件

- `semantic_annotations.jsonl`：每条回答一行，含本地研究元数据、逐命题标注和回答层标签。
- `claim_annotations.jsonl`：逐命题长表，便于筛选、聚合和统计。
- `response_level_summary.csv`：回答层代码和覆盖摘要。
- `raw_batches/`：每批 Codex 返回的原始 JSON、JSONL 事件、错误日志和缺失项补标结果。保留重复/遗漏输出供审计；规范结果按 response_uid 去重。
- `processing_manifest.json`、`batch_run_metadata.json`、`repair_metadata.json`：代码本、schema、输入载荷哈希、服务配置、批次覆盖与 CLI 用量记录。
- `validation_summary.json`、`annotation_report.md`：全量覆盖、重复键、引文定位、类别分布及方法限制。
- `output.schema.json`：云端结构化输出 schema。
- `../coding/prepare_response_register.py`：从所选完整 F/N/R/C 运行生成输入登记。`run_semantic_annotation.py`：重新发起全部/单个题组云端标注；运行前需传 `--confirm-data-upload` 明确确认数据发送，`--merge-existing` 只从已保存批次本地重建输出，不发送语料。快捷服务入口为 `../api/run_semantic_annotation.py`。
- `repair_missing_samples.py`：只对完整批次返回中遗漏的 response key 作定向补标。
- `repair_unverified_quotes.py`、`repair_remaining_claim_quotes.py`：第二阶段仅修复不能回指的证据片段；写回前还要由本地程序逐字核验。模型仍未找到的片段保留 `unverified`。
- `summarize_annotations.py`：从最终标注生成报告和描述性汇总表。
- `finalize_run_metadata.py`：从 CLI 事件与原始批次输出重建运行状态和用量记录。

## 解释边界

这是同一 Codex 模型配置产生的机器单标注结果，没有人工双标、仲裁或独立外部验证；`label_confidence` 是模型对标签的主观把握，不是经校准概率。响应在同一模型会话中连续生成，不能把同一对话的每一轮当作独立重复。引用、标签和评分应作为可复核候选结果，不应称为经人工验证的最终真值或法律裁决。

每个选定响应是否进入规范结果由校验摘要按实际输入数报告；原始批次中的重复输出和冲突记录保留在 `raw_batches/` 并在校验摘要中报告。仍有少量命题或遗产代码证据片段无法严格回指原文，已逐条标记 `unverified`；请在实证结论中排除或单独报告这些项。

## 外部数据处理

语义标注会将选定回答、当前题目、同线程上下文、代码本及相关冻结证据片段发送给本机已配置的 Codex CLI 服务。运行者必须确认组织规则、数据权利与传输范围，并在命令中显式加入 `--confirm-data-upload`。复现包不包含历史原始回答、批次输出或访问凭据。

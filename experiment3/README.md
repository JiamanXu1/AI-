# 实验三：证据、扎根主题、文本编码与量化分析

本目录是可复制到陌生电脑的实验三资料包，包含问卷、冻结事实/法律与媒体证据、代码本、来源登记、历史对照输入、执行脚本和 API/服务适配入口。新实验原始回答写入相邻的 `experiment1/results/` 与 `experiment2/` 运行目录；默认不纳入 Git。

## 包内资产

|目录|内容|
|---|---|
|`questionnaire/`|身份实验英文/中文12题、波斯语问卷及 F/N/R/C 追问题目。|
|`evidence/`|知识单元、来源目录、T9 责任依据完整冻结包。|
|`benchmark/`|事实/法律/来源基准和构建报告；`source_corpus/` 保存重建基准所需的冻结媒体来源登记、摘要与原始摘录。|
|`factbank/`|本地事实库、规则、来源、数据库、schema 和构建/校验脚本。|
|`heritage_qrmine/`|联合国/UNESCO 文化遗产规范材料冻结语料、主题/代码本、来源和 QRmine 完整流程。|
|`codebook.json`、`followup_coding_scheme.json`、`study2_coding_v2/`|文化价值、追问轮次和事实/规范/责任/确定性编码标准。|
|`baseline/`|此前已保存的英文和波斯语问卷对照输入，用于历史比较，不是本次新采集结果。|
|`coding/`|响应登记、编码队列和本地词面基线。|
|`quant_analysis/`|新三身份十轮结果分析，以及只用于旧版固定语料的兼容分析脚本。|
|`semantic_annotation/`、`api/`|结构化语义标注、引用核验/汇总、schema 和 Codex CLI 服务适配入口。|

脚本完整路径见包根目录 [`PYTHON脚本索引.md`](../PYTHON脚本索引.md)。整套新电脑命令见 [`RUNBOOK.md`](../RUNBOOK.md)。

## 1. 本地环境与冻结证据

一般分析脚本使用 Python 3.10+ 标准库，不需要额外 pip 包。QRmine 单独使用 Python 3.11 和 `heritage_qrmine/requirements-lock.txt`。

从包根目录重建事实基准。该步骤只读本目录内的 source corpus 与 factbank，不访问网络或模型 API：

```bash
python3 experiment3/benchmark/build_truth_benchmark.py
```

此命令会重写 `benchmark/` 中生成的基准表。源材料使用状态、报道内容与事件层真值是不同层级；查看 `benchmark/README.md` 与 `source_corpus/README.txt` 的边界说明。

## 2. 扎根主题与中英文分析

```bash
cd experiment3/heritage_qrmine
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python run.py --offline
python run.py --verify-only
```

离线分析使用包内冻结语料，不调用模型 API。首次依赖安装需要网络。QRmine/NMF 结果是探索线索；`interpretive_coding.csv` 中的解释性编码是 AI 辅助初稿，需研究者逐条复核，不能冒充人工双编码或理论饱和结论。完整数据边界见 `heritage_qrmine/README.md`。

## 3. F/N/R/C 实验回答的本地整理

先在实验二完成至少一个 F/N/R/C 运行。登记表要求每个纳入运行状态为 complete，且恰有27个有效回答：

```bash
python3 experiment3/coding/prepare_response_register.py \
  --run-dir "experiment2/followup/results/填入完整运行目录名"
```

多模型时重复 `--run-dir`。这会在 `experiment3/pure_machine_v1/response_register.csv` 写入完整回答，请按本地数据管理要求保管。之后可构建问卷覆盖/编码队列：

```bash
python3 experiment3/coding/build_coding_queue.py
```

队列和审计表写在 `experiment3/coding/`，旧历史结果不随包发布。下列基线脚本会动态读取所有完整的实验二 F/N/R/C 运行，只做本地标点切分、代码本词面候选、来源编号和不确定性措辞线索，不调用模型：

```bash
python3 experiment3/coding/run_machine_pipeline.py --prepare-only
```

词面命中、句子近似切分和表层措辞不是语义编码、事实真伪判定或法律评分；脚本报告会保留这一限制。

## 4. 可选结构化语义标注

本步骤使用本机已登录的 Codex CLI 服务；它会发送所选回答、题目、同线程上下文、代码本和冻结证据片段。先阅读 [`api/README.md`](api/README.md) 和 [`semantic_annotation/README.md`](semantic_annotation/README.md)，确认数据传输范围后再运行：

```bash
python3 experiment3/api/run_semantic_annotation.py --only F1 --confirm-data-upload
python3 experiment3/api/run_semantic_annotation.py --confirm-data-upload
python3 experiment3/semantic_annotation/summarize_annotations.py
```

第一条只处理 F1 题组；第二条处理全部12组。`--merge-existing` 可仅从已保存批次本地重建，不发送新数据。输出包括逐回答/逐命题 JSONL、CSV 摘要、输入哈希、覆盖校验与原始批次；机器标签仍需人工审阅。

## 5. 三身份十轮实验的阶段三分析

实验二每模型输出伊朗、美国、中国三个独立身份线程，每线程10轮。完成后从包根目录运行：

```bash
python3 experiment3/quant_analysis/analyze_all_identity_runs.py
```

脚本只读 `experiment2/results_identity/` 及包内问卷、历史对照和证据，结果写到 `experiment3/quant_analysis/多轮实验纯机器分析_20261026/`。它生成完整性审计、前后测、逐回答词面指标、T8 强制归责、T9 来源引用审计、主题/价值候选、文字重合和可计算性审计。强制选择不当作法律裁决，词面指标不当作人工编码，同一线程轮次不当作独立样本。

`quant_analysis/analyze_supplemental_text_mining.py` 与 `analyze_quant_metrics.py` 保留旧版分析协议；它们依赖旧版固定运行目录或未随包发布的135条机器标注语料，不属于本次新实验的必要入口。不要把旧版输出与新协议混合。

## 6. 人工编码与复核

人工复核依据 `codebook.json`、`followup_coding_scheme.json`、`study2_coding_v2/codebook.json` 和 `annotation_template.json`。先用 `coding/build_coding_queue.py` 生成登记，再由至少两位编码者独立标注抽样/全量，记录分歧和仲裁，报告一致性计算的单位和样本。自动词面/语义标签只作为候选，保留原始回答和证据来源，不能覆盖人工决策。

## 7. 文件与数据边界

- 不包含 API 密钥、未完成运行原始回答或 Codex 语义标注批次；结果目录由 `.gitignore` 排除。
- `baseline/` 是包内历史对照材料，不是新生成的 Dorna 结果。
- `analyze_quant_metrics.py` 依赖的旧版135条回答和标注不在包内；旧版补充文本挖掘需要其固定运行 ID 的历史输入。
- 第三方来源继续适用原许可；冻结摘要/摘录保留来源 ID 和 URL，不代表可以脱离原站许可重新发布全部原文。
- 本目录的整理没有调用模型、API 或 Codex CLI，也没有续跑实验。

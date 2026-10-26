# Dorna 与戈勒斯坦宫文化遗产感知实验

这是一个可克隆到其他电脑运行的研究包，包含本地 Ollama 问卷/鲁棒性实验、API 多轮追问、身份条件全线程实验、证据与来源快照，以及扎根主题和量化分析代码。实验原始回答由运行者在本地生成；包内不含 API 密钥或原始调用日志，少量历史汇总仅作为既有分析对照。

新电脑部署 Dorna/Ollama 请先看 [macOS 安装与本机配置](DORNA_SETUP_MACOS.md)。完整的三阶段实验逻辑、主题到文本的编码链路与量化口径见 [实验策略与分析口径](实验策略与分析口径.md)。

## 实验地图

|阶段|内容|单个模型的请求量|入口|
|---|---|---:|---|
|实验一 A|英文 12 题与波斯语 12 题问卷，两次独立调用；波斯语提示模拟“伊朗普通公民”视角|2|`experiment1/run_ollama_bilingual_questionnaire.py`|
|实验一 B|语言（英语/中文）×提示版本（v1/v2）×背景（中性/伊朗/以色列）×重复10次|120|`experiment1/run_ollama_robustness.py`|
|实验二 A|F/N/R/C 追问；12 个独立问题线程，共27轮请求|27/模型|`针对文化遗产的AI偏见/golestan_perception_v1/run_followup_experiment.py`|
|实验二 B|身份全线程：伊朗、美国、中国中立身份各一条独立对话；每条10轮，完整携带该线程此前消息|约30/模型|`针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py`|
|阶段三|冻结证据与扎根主题、人工/机器辅助编码、描述性文本与量表分析|本地计算；语义标注为可选模型调用|`针对文化遗产的AI偏见/heritage_qrmine/` 与 `quant_analysis_v1/`|

身份实验 T1–T10 的完整题目、提示和证据注入逻辑都在 Python 脚本中。主要轮次如下：

1. T1 前测问卷。
2. T2 开放式事件评估。
3. T3 事实、来源和损害核查。
4. T4 文化价值与相关群体视角。
5. T5 法律规则及其适用条件。
6. T6 行为方、行动和因果关系。
7. T7 分别评价伊朗与美国在本事件中的行为。
8. T8 强制在伊朗/美国之间选出相对责任较高的一方并给出比较权重；同时将强制比较判断与证据支持的事实、国家法律责任、个人刑事责任、道德/政治评价分开。
9. T9 审核 T8 的证据基础，逐项核对来源编号、URL、材料实际支持的命题与限制。
10. T10 后测问卷及最终报告。

T8 是提示施加的强制比较任务，不能当作模型真实信念、事实证明或法律裁决。T9 的目的正是审计该选择依赖的证据。每个身份线程彼此隔离；同一线程内每轮都会携带此前问答。默认是每模型30个有效轮次；网络重试会增加传输请求数。

## 快速开始：Dorna 本地实验

需要 Python 3.10 或更新版本、已安装并运行的 Ollama，以及已下载的 Dorna 模型。

```bash
ollama pull partai/dorna-llama3:8b-instruct-q4_0
ollama list
```

从本目录运行：

```bash
python3 experiment1/run_ollama_bilingual_questionnaire.py
python3 experiment1/run_ollama_robustness.py --pilot
python3 experiment1/run_ollama_robustness.py
```

正式鲁棒性实验默认执行120次彼此独立的调用；`--pilot` 的结果单独保存，不会计入120次。中断后按终端给出的目录续跑：

```bash
python3 experiment1/resume_ollama_robustness.py --run-dir "experiment1/results/ollama_robustness_<运行ID>"
```

英语/波斯语问卷输出与120次鲁棒性结果保存在 `experiment1/results/`。无效 JSON、模型自行更换格式及原回答会保留在日志中；脚本不会把模型输出修成貌似有效的分数。

## 实验二：API 多轮追问

API Key 通过环境变量或终端隐藏输入提供。不要把密钥放进配置文件、命令参数、聊天记录或 Git 提交。身份实验脚本每次运行一个模型，默认自动按伊朗、美国、中国依序执行10轮；每模型名义上30轮，失败重试可能增加实际传输请求数。

### F/N/R/C：27轮/模型

例如使用配置中的 DeepSeek 模型：

```bash
python3 "针对文化遗产的AI偏见/golestan_perception_v1/run_followup_experiment.py" --provider deepseek
```

其他脚本支持的 provider 与模型配置见 `experiment1/config.json`。也可通过 `--provider openai-compatible --base-url <兼容接口/v1> --model <模型ID>` 连接其他 Chat Completions 服务。F/N/R/C 每个题目对应独立线程，同一题目后续轮次携带完整历史。

### 身份全线程：30轮/模型

```bash
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider deepseek
```

不传 `--conditions` 时，自动按伊朗、美国、中国中立身份各跑10轮。脚本每轮单独请求、保存原始响应和完整 transcript；网络中断后可用 `--resume <同一运行目录>` 仅继续尚未成功的轮次。

身份实验向各轮提供较长的事件证据与来源材料。模型必须有足够上下文容纳证据和累计历史。Dorna 标称上下文约8K，不能承担本实验约30,000字符证据加多轮历史；按研究设定应使用长上下文模型。脚本支持 OpenAI、DeepSeek、豆包、Gemini、Grok、Mistral API 和 OpenAI-compatible 接口。以下每条 API 命令各跑一个模型的三身份全线程；若跑全部六家，名义请求总数约180次。先确认具体模型与账号的上下文上限，OpenAI 示例必须用 `--model` 覆盖配置里的旧默认型号：

```bash
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider deepseek
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider doubao
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider gemini
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider grok
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider mistral
OPENAI_LONG_CONTEXT_MODEL="替换为你账号可用的长上下文模型ID"
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider openai --model "$OPENAI_LONG_CONTEXT_MODEL"
```

若在本地用 Ollama，可选已验证长上下文的模型，例如：

```bash
ollama pull qwen3.5:4b
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" \
  --provider ollama-local --model qwen3.5:4b --base-url http://127.0.0.1:11434 \
  --num-ctx 98304 --num-predict 8192
```

使用其他 API 模型时，先核对该模型/账号实际可用上下文长度。实验记录会保存模型 ID、上下文参数、提示哈希、请求次数与每轮 `prompt_eval_count`（服务端提供时）。

## 阶段三：主题—文本—量化分析

### 3.1 扎根主题与资料冻结

`针对文化遗产的AI偏见/heritage_qrmine/` 提供联合国/UNESCO 文化遗产材料的冻结语料、来源范围、解释性编码和 QRmine 辅助分析。运行前按该目录 `README.md` 使用 Python 3.11 安装其独立锁定依赖；离线复现命令为：

```bash
cd "针对文化遗产的AI偏见/heritage_qrmine"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python run.py --offline
```

QRmine 词项/类别与 NMF 主题是探索线索，不自动等同于研究者的开放、主轴或选择性编码，也不按词频决定价值权重。来源清单、页/行定位、代码本、解释备忘录和双语边界见该目录 `config/`、`provenance/` 与报告。

玫瑰宫事件的事实/法律参照另放在：

- `针对文化遗产的AI偏见/golestan_perception_v1/knowledge.jsonl`
- `针对文化遗产的AI偏见/golestan_perception_v1/source_catalog.json`
- `针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/responsibility_basis_corpus.json`
- `玫瑰宫事实语料库包括中国和联合国/golestan_truth_benchmark_20261020_v1/`

责任依据语料中保留来源编号、题名、发布方、URL、定位线索、证据状态与限制；T9 必须按准确 URL/编号回指材料，不可把来源“报道了某事”写成该事件已独立核实。

### 3.2 对话编码与指标

冻结每轮原始回答后，按 `codebook.json`、`followup_coding_scheme.json` 与 `study2_coding_v2/codebook.json` 做回答层和命题层标注。模板位于 `study2_coding_v2/` 及 `quant_analysis_v1/多轮实验纯机器分析_20261026/`。F/N/R/C 完成后，按需选择已完成的模型运行生成输入登记，再执行语义标注：

```bash
python3 "针对文化遗产的AI偏见/golestan_perception_v1/prepare_response_register.py" \
  --run-dir "针对文化遗产的AI偏见/golestan_perception_v1/results/<运行目录>"
python3 "针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/run_semantic_annotation.py" --confirm-data-upload
python3 "针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/summarize_annotations.py"
```

多个模型时重复传入 `--run-dir`。语义标注会向已配置的 Codex CLI 服务发送所选回答、当前题目、同线程上下文、代码本和相关证据片段；只有在确认数据处理权限和范围后才加 `--confirm-data-upload`。机器辅助标签需人工双人复核、仲裁及一致性分析，不能直接当作人工编码结果。

针对新生成的身份实验结果，在完成运行后执行：

```bash
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_all_identity_runs.py"
```

此分析只在本地读取保存结果，不调用模型 API，输出 HTML、CSV 与完整性审计。阶段三策略文件 `分析策略与首轮结果.md` 对应的主要可计算指标为：

- 重要遗漏率：回答层 C-B=1 的可评回答数 / 可评回答数。
- 无证据过度肯定率：回答层 C-C=1 / 可评回答数。
- 事实支持率：逐回答 `支持 / (支持 + 矛盾)` 的宏平均；U、NA、范围外分别保留。
- 法律规则评分：1/2/3 分布优先；U/NA 排除，均值仅作补充。
- 责任归属校准：事实行为方、直接目标/意图、法律违规等子项分开计算支持/矛盾，未知单列。
- 主题框架覆盖、文化价值标签覆盖、命题共现、同题模型代码集合 Jaccard，以及字符2–4 gram文字余弦/Jaccard。

不要把以上维度合成单一“中立性分数”。同一线程的10轮是嵌套对话，不是10个独立样本；单事件、单次生成只能支持本轮条件下的描述比较，不能单独证明普遍或因果性偏见。机器标注、词面命中与强制责任选择均须按各自的解释边界报告。

`analyze_quant_metrics.py` 保留旧版135条回答语料的完整量化处理代码；该历史回答/机器标注数据集未放入这个 GitHub 包。若需要精确重现旧版结果，需另行提供原项目保存的 `results/` 与 `semantic_annotation_codex_v1/` 数据，再运行该脚本。

## 目录说明

- `experiment1/`：12题英语/波斯语问卷、120格鲁棒性设计、本地 Ollama/API Python 脚本和公开配置模板。
- `针对文化遗产的AI偏见/golestan_perception_v1/`：F/N/R/C 提问、输入登记构建器、10轮身份实验、事实/来源/代码本与阶段三分析。
- `针对文化遗产的AI偏见/heritage_qrmine/`：冻结语料与计算辅助扎根分析全流程。
- `玫瑰宫事实语料库包括中国和联合国/`：事件事实、法律规则、来源登记和责任基准构建代码。
- `实验一中波斯语回答/`：阶段三旧版双语前测的最小分析输入，不含 node_modules。

## 发布与数据边界

运行结果、原始 API 日志、未完成对话、缓存、虚拟环境和密钥文件均由 `.gitignore` 排除。冻结的来源登记和证据包内含可追溯引用与研究摘要；原始来源仍受其各自许可/转载条件约束，发布者应保留原 URL 并核对第三方材料许可。此仓库没有替原创代码或第三方资料擅自指定统一许可证。

Python/Ollama/API 服务、模型版本、模型量化、提示版本和实验输入哈希均需与运行结果一同报告。模型供应商、API 版本或模型端点随时间变化时，应记录实际返回的模型 ID 与时间戳。

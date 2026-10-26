# 可复现实验 Runbook

此流程供首次接触本项目的研究者在另一台电脑上，从环境检查到三阶段结果整理。先下载/解压 GitHub 包，然后打开终端，进入包含本文件的 `模型dorna` 目录。下方命令都从该包根目录执行，只有 QRmine 步骤会先进入其子目录。

```bash
cd "/下载路径/模型dorna"
python3 --version
```

多数脚本需要 Python 3.10 或更新版本。QRmine 必须单独使用 Python 3.11。不要把 API key 写进 shell 历史或 JSON 配置；需要 API 的脚本会在交互终端隐藏读取密钥，或从配置中指定的环境变量读取。

## 0. 安装 Dorna / Ollama

作者本机原实验路径为 `/Users/beatrixxu/Documents/ChatGPT/美伊话语中的AI存在社会偏见问题——以玫瑰宫为例/experiment1`，整理包在其 `模型dorna` 子目录中。其他电脑用下载/克隆后的本地路径替代即可。安装方式、同一 Ollama 服务检查和 Cloudflare IPv6 下载错误排查见 [DORNA_SETUP_MACOS.md](DORNA_SETUP_MACOS.md)。

在 macOS 安装并打开 Ollama 后：

```bash
export OLLAMA_HOST="http://127.0.0.1:11434"
ollama pull partai/dorna-llama3:8b-instruct-q4_0
ollama list
curl --noproxy '*' -sS "$OLLAMA_HOST/api/tags"
```

只有本机 `ollama list` 和 API tags 都列出 `partai/dorna-llama3:8b-instruct-q4_0` 才继续。若曾遇到下载重定向被拦截的错误，先按本机配置说明确认下载真正完成；空模型列表不能进入实验。

## 1. 实验一：Dorna 英文/波斯语问卷与鲁棒性

从包根目录运行：

```bash
python3 experiment1/run_ollama_bilingual_questionnaire.py
python3 experiment1/run_ollama_robustness.py --pilot
python3 experiment1/run_ollama_robustness.py
```

第一条分别提交英文12题和波斯语12题，两个问卷不共享对话历史。第二条执行独立 pilot。第三条执行正式矩阵：英语/中文 × 提示版本 v1/v2 × 中性/伊朗/以色列背景 × 每格10次，共120次。pilot 与正式矩阵分开保存。输出写入 `experiment1/results/`，不要把运行结果或 API 日志提交到公开仓库。

若需用 API 跑实验一而非本机 Dorna，先查看 `experiment1/config.example.json`、确认模型 ID/接口可用，再运行：

```bash
python3 experiment1/run_experiment.py --help
python3 experiment1/run_experiment.py --providers deepseek --prompt-key
python3 experiment1/run_robustness.py --provider deepseek --repeats 10
```

API 模型和凭据属于运行者的服务账号；按 `credential_env` 配置设置环境变量或在交互终端隐藏输入。不要把密钥存入 `config.json`。120格矩阵如需使用 API，请先阅读参数说明并明确选择服务商，避免误启动高请求量任务。

## 2. 实验二 A：F/N/R/C 追问（27请求/模型）

运行器、问卷、事实材料、来源登记和配置都在 `experiment2/followup/`。运行前查看配置中的服务商与模型 ID，确认对当前账号可用；需要时仅在本机修改 `experiment2/followup/config.json`。

```bash
python3 experiment2/followup/run_followup_experiment.py --help
python3 experiment2/followup/run_followup_experiment.py \
  --provider deepseek \
  --config experiment2/followup/config.json
```

每模型计划27次有效轮次，12个题组各自建线程，同一题组的追问携带该线程历史。密钥通过隐藏输入或环境变量读取。运行中断会保留部分结果；该运行器没有原目录续跑参数，重新运行会另建目录。实验三登记时只选 `run_info.json` 标记为 `complete` 且有27条有效回答的目录。

## 3. 实验二 B：三种身份的完整10轮问题流程（30请求/模型）

此流程按伊朗、美国、中国身份建立三个互相隔离的线程，每线程 T1–T10 全历史追问，共30个计划请求。启动前查看完整题目和文件清单：

```bash
python3 experiment2/run_three_identity_full_thread.py --help
```

为一个模型运行全部三种身份：

```bash
python3 experiment2/run_three_identity_full_thread.py \
  --provider deepseek \
  --model "填写账号当前可用的长上下文文本模型ID"
```

脚本会在终端隐藏读取密钥。也可选 `openai`、`doubao`、`gemini`、`grok`、`mistral` 或 `openai-compatible`；每次运行一个 provider/model。每模型30次是计划调用次数，服务错误重试会增加实际传输量。运行输出在 `experiment2/results_identity/<provider>_<运行ID>/`；完成标准是 `run_info.json` 状态为 `complete`，伊朗/美国/中国各10轮，并核对返回模型和输入哈希。

本身份实验每轮包含较长证据并重发累计历史，总输入可能约30,000字符。Dorna 的约8K上下文不够；选择模型前需核对账号实际可用上下文、输出限额和服务商 model ID。中断续跑时必须使用同一 provider/model、endpoint 和输入：

```bash
python3 experiment2/run_three_identity_full_thread.py \
  --provider deepseek \
  --model "与原运行相同的模型ID" \
  --resume "experiment2/results_identity/原运行目录名"
```

完整 T1–T10 问题在 `experiment2/run_three_identity_full_thread.py`；问卷、知识单元、来源登记、责任证据包和 API 适配均在 `experiment2/` 包内。T8 是提示要求的强制比较选择，不是事实证明或法律裁决；T9 用于逐项核对引用依据。

## 4. 实验三：主题—证据—文本—计算完整链路

### 4.1 重建冻结事实基准

实验三内含事实基准构建所需的冻结媒体 source corpus、factbank 和已生成的基准表。从包根目录执行：

```bash
python3 experiment3/benchmark/build_truth_benchmark.py
```

该命令不联网、不调用模型，会更新 `experiment3/benchmark/` 下基准产物。来源登记、来源陈述、事件事实状态和证据限制分开记录；检查 `experiment3/benchmark/README.md` 与 `experiment3/benchmark/source_corpus/README.txt`。

### 4.2 QRmine 辅助扎根主题和双语文本分析

需要 Python 3.11。首次安装依赖需要联网；冻结语料上的正式分析是离线的：

```bash
cd experiment3/heritage_qrmine
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python run.py --offline
python run.py --verify-only
deactivate
cd ../..
```

报告、来源范围、代码本、双语配对、机器候选和待人工复核队列都在 `experiment3/heritage_qrmine/`。QRmine/NMF 只用于发现线索；理论主题和编码须由研究者审阅材料、修订代码本并记录反例，不以词频替代主题判断。

### 4.3 实验二回答的登记与本地编码候选

选定已完成的 F/N/R/C 结果目录，将完整回答整理进登记表：

```bash
python3 experiment3/coding/prepare_response_register.py \
  --run-dir "experiment2/followup/results/完整运行目录名"
```

多模型需重复 `--run-dir`。随后可生成覆盖审计和人工复核队列，以及本地确定性词面候选：

```bash
python3 experiment3/coding/build_coding_queue.py
python3 experiment3/coding/run_machine_pipeline.py --prepare-only
```

后一个脚本自动读取全部完整的27轮 F/N/R/C 运行，不发 API 请求；用标点切分、代码本词面匹配和来源/确定性线索建立候选结果。它不判断命题真伪或法律正确性。所有输出留在 `experiment3/coding/` 或 `experiment3/pure_machine_v1/`，不要提交原始回答。

### 4.4 可选 Codex CLI 语义标注

语义标注不是普通本地计算：会向本机已登录的 Codex CLI 服务发送选定回答、当前问题、同线程上下文、代码本和冻结证据。仅当运行者确认数据处理范围后再启动；完整输入和输出说明见 `experiment3/api/README.md` 及 `experiment3/semantic_annotation/README.md`。

```bash
python3 experiment3/api/run_semantic_annotation.py --only F1 --confirm-data-upload
python3 experiment3/api/run_semantic_annotation.py --confirm-data-upload
python3 experiment3/semantic_annotation/summarize_annotations.py
```

首条只发送 F1 题组供小批检查；全量命令处理12组。已有批次只在本地合并时使用 `--merge-existing`，不要带数据上传确认参数。结构化机器标签和命题引文须人工复核后再用于研究结论。

### 4.5 三身份十轮结果计算

身份实验完成后从包根目录执行：

```bash
python3 experiment3/quant_analysis/analyze_all_identity_runs.py
```

脚本只在本地读取 `experiment2/results_identity/`，在 `experiment3/quant_analysis/多轮实验纯机器分析_20261026/` 写出完成性审计、前后测、文本候选、T8 责任选择、T9 来源审计和可计算指标。补充文本挖掘/135答历史脚本在 `experiment3/README.md` 标有旧版输入要求，不能与本次新协议结果混为一组。

### 4.6 人工编码及报告

对响应级和命题级代码按 `experiment3/codebook.json`、`experiment3/followup_coding_scheme.json` 与 `experiment3/study2_coding_v2/codebook.json` 操作。推荐两位编码者独立编码并留存逐项引文、依据、分歧和仲裁过程；根据研究设计报告单位、抽样和一致性计算。机器辅助结果属于候选，不能替代人工复核。

## 5. 完成检查

- [ ] Dorna 实验：两个语言问卷均有结果；正式鲁棒性格子为120项，pilot 单独保存。
- [ ] F/N/R/C：每模型27个有效轮次、12题组覆盖、`run_info.json` 为 complete。
- [ ] 身份实验：每模型三种身份各10轮、输入哈希一致、T1/T10 问卷结果可审计。
- [ ] QRmine：离线全流程成功，核验结果记录；人工检查解释性编码和反例。
- [ ] 阶段三：登记表行数匹配所选有效轮次；区分词面候选、语义候选与人工最终编码。
- [ ] 保存 Python/依赖版本、服务商、实际返回模型、日期、输入哈希、请求次数及失败重试。
- [ ] GitHub 发布前确认 `.gitignore` 生效，没有 API key、原始 API transcript、个人数据或新生成语义批次。

## 6. 历史结果说明

包内 baseline 是已有对照数据。`experiment3/quant_analysis/analyze_quant_metrics.py` 需要未随包发布的旧版135条人工/机器标注数据；`analyze_supplemental_text_mining.py` 对应旧版固定运行 ID。它们保留用于历史研究追溯，不是新的陌生电脑必要步骤。

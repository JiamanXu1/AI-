# Dorna 与戈勒斯坦宫文化遗产感知实验

这是一个可复制到其他电脑的研究包，包含 Dorna/Ollama 双语问卷与鲁棒性实验、API 追问和三身份全线程实验，以及第三阶段的证据库、扎根主题、人工/机器辅助编码和量化分析。包内提供实验所需问卷、提示设计、事实/法律证据、来源登记、代码本、API/服务适配器和 Python 脚本。

陌生电脑逐步部署、配置和完整运行命令见 [可复现实验 Runbook](RUNBOOK.md)。本包按作者的 macOS/Ollama 配置整理，含精确模型标签和排错流程，见 [Dorna 本机安装说明](DORNA_SETUP_MACOS.md)。研究设计及指标口径见 [实验策略与分析口径](实验策略与分析口径.md)；`.py` 路径和数据要求见 [Python 脚本索引](PYTHON脚本索引.md)。

## 实验地图

|阶段|任务|单模型计划请求|可运行入口|
|---|---|---:|---|
|实验一 A|英文12题与波斯语12题，分别独立调用|2|`experiment1/run_ollama_bilingual_questionnaire.py`|
|实验一 B|语言×提示版本×背景条件，每格重复10次|120|`experiment1/run_ollama_robustness.py`|
|实验二 A|12个 F/N/R/C 题组，追问共享各自线程历史|27|`experiment2/followup/run_followup_experiment.py`|
|实验二 B|伊朗、美国、中国身份各一条独立10轮对话|30|`experiment2/run_three_identity_full_thread.py`|
|实验三|冻结证据、QRmine/扎根主题、人工/机器辅助编码、文本分析、响应级和命题级量化|本地；语义标注可选|`experiment3/README.md`|

实验二三身份的 T1–T10 题目、长证据输入、历史拼接、强制责任比较、T9 来源核查及 API 适配都在 `experiment2/`；实验三的问卷、证据、事实基准、媒体冻结来源、代码本和服务适配都在 `experiment3/`。这些目录不是只放脚本的索引副本。

## 开始之前

- Dorna 本机实验需要 Python 3.10+、运行中的 Ollama 和精确模型 `partai/dorna-llama3:8b-instruct-q4_0`。先确认 `ollama list` 与 `GET /api/tags` 都能看到同一模型。
- 实验二 API 运行器需要调用者自己的服务商账号和可用文本模型；密钥在本机终端隐藏输入，不要写入配置、命令或 Git。
- 身份全线程约有30,000字符事件证据并累积对话历史。Dorna 约8K上下文不适合该任务，必须使用经核实有足够上下文的模型。
- 扎根主题 QRmine 使用单独 Python 3.11 环境；其他本地分析脚本主要使用标准库。
- API 运行、Codex 语义标注和结果生成均由使用者按 Runbook 启动；此包不会自动发出请求。

## 文件与数据边界

API 密钥、未完成/完成实验原始运行目录和新生成的语义标注批次由 `.gitignore` 排除。包内 `baseline/` 保存既有对照结果；它们不是本次重新采集的 Dorna 输出。第三方证据保留来源 ID、URL 和使用限制；发布者仍应遵守原始来源许可。机器词面命中和结构化语义标签都不是无需复核的人工结论。

本包不续跑此前未完成的实验。历史专用分析脚本仍保留，并在实验三 README 中标明其输入限制。

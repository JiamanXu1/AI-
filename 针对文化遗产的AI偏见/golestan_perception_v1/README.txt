玫瑰宫 LLM 文化遗产感知分析指标，v1.0-provisional

打开“分析指标与编码手册.html”阅读完整定义、24项迁移、示例及中英文研究设计。
本工具分析模型文本表达，不测量模型的内心体验；不是已验证量表或实际实验结果。

重建：
  cd 本文件所在目录
  python3 build.py
不需要第三方库、API key、网络或 QRmine。build.py 将重建 codebook.json、
huang_crosswalk.json 和 HTML 手册；请在 build.py / report_body.html 中修改源定义。

使用：
1. 冻结研究问题、提示版本、证据截止时间；独立保存原始回答及采集元数据。
2. 复制 annotation_template.json，按回答、命题与关系填写；null 表示未编码，
   不得将其当作零。每个命题可包含多个代码，保留原文字符位置。
3. 两位编码者独立试编码、检验分歧并修订框架，之后冻结正式版本。
4. 在回答层面去重汇总出现率，另报展开程度、损害联系与证据校准。
   JSON 是结构模板，不是自动编码器；不得将教学例句当成模型样本。

豆包API采集：
  python3 call_doubao.py --diagnose
  python3 call_doubao.py
诊断命令不需要密钥，只检查Ark域名、代理和TLS。采集脚本可独立放在复制的文件夹中；
默认使用doubao-seed-2-1-lite-260915，也会自动读取同目录config.json，或原项目experiment1/config.json。
如需临时代理，可传 --proxy http://127.0.0.1:7897，或设置ARK_HTTPS_PROXY；
只应使用本机正在运行且确认可用的代理端口。脚本使用certifi/系统CA并保持TLS证书验证。
不能解析域名时是DNS/网络路由问题；证书校验失败时是CA链或HTTPS代理证书信任问题。

F/N/R/C多轮实验（DeepSeek）：
  python3 run_followup_experiment.py --provider deepseek
  python3 run_followup_experiment.py --provider deepseek --diagnose

无DEEPSEEK_API_KEY环境变量时，采集脚本会在本机终端隐藏式提示输入Key；不要在聊天窗口或命令行参数中粘贴Key。
官方Key管理页：https://platform.deepseek.com/api_keys 。每个代码ID（F1、F2等）对应一个独立对话；
同一ID的追问会继续携带之前的完整问答上下文。DeepSeek接口每轮回答仍需发起一次API请求，因此本问卷完整运行共12个对话、27轮请求。
问题顺序及原文见 followup_questionnaire.json；知识库及来源目录会作为证据材料提供给模型。
每次运行会在 results/deepseek_followup_<时间戳>/ 保存原始逐轮响应、完整原回答集、运行元数据及待人工填写的编码模板。
编码模板不自动生成分析结论；请依据编码手册对原回答逐轮人工编码。

F/N/R/C多轮实验（OpenAI API）：
  python3 run_followup_experiment.py --provider openai
  python3 run_followup_experiment.py --provider openai --list-models
  python3 run_followup_experiment.py --provider openai --diagnose

脚本读取 experiment1/config.json 中的OpenAI模型与端点配置；目前配置模型为gpt-4o-mini-2024-07-18。
如当前进程未设置OPENAI_API_KEY，脚本会在本机终端隐藏式提示输入。完整运行同样为12个独立对话、27轮API请求；
原始回答和待编码模板保存在 results/openai_followup_<时间戳>/。
若模型访问报错，可用--list-models查询当前Key所属Project可访问的模型ID；该操作只查询模型列表，不运行问卷。

本 GitHub 包提供 OpenAI API 与其他服务商 API 的 Python 运行器；未包含 ChatGPT plan 专用适配器。

F/N/R/C多轮实验（Google Gemini API）：
  python3 run_followup_experiment.py --provider gemini --list-models
  python3 run_followup_experiment.py --provider gemini

Gemini使用Google原生generateContent接口；如未设置GEMINI_API_KEY，脚本会在本机终端隐藏式提示输入。
先用--list-models查看当前Key可调用且支持generateContent的模型ID，再将选定模型写入experiment1/config.json的gemini条目。
完整运行共12个独立对话、27轮API请求；原始回答和待编码模板保存在results/gemini_followup_<时间戳>/。

F/N/R/C多轮实验（Grok / xAI API）：
  python3 run_followup_experiment.py --provider grok --list-models
  python3 run_followup_experiment.py --provider grok --model grok-4.7

在xAI Console创建API Key后，脚本会在本机终端隐藏式提示输入XAI_API_KEY；不要将Key粘贴到聊天中。
默认使用OpenAI兼容的Chat Completions接口（https://api.x.ai/v1），可通过--list-models查询当前Key可访问的模型。
完整运行共12个独立对话、27轮API请求；原始回答和待编码模板保存在results/grok_followup_<时间戳>/。
API Key及计费管理：https://console.x.ai/ 。

原始研究与自动文本探索仍在 ../../heritage_qrmine。
这里不重新运行 QRmine，也不把词频视为本指标的验证。
本次核对了 Huang 论文 Table 5/8 XML 与 Bu 附件 pp.2–6、p.4 表格图像。
未复制分发用户的 IEEE PDF。指标原始来源、改编边界及链接见手册。

F/N/R/C多轮实验（MetisAI）:
  python3 run_followup_experiment.py --provider metis --config metis_followup_config.json

MetisAI需要先在控制台创建专用机器人，并将其bot_id、底层模型ID及机器人配置记录到
metis_followup_config.json。机器人系统提示词应留空；关闭RAG/知识库、网络搜索、工具和记忆，
避免机器人额外注入内容。脚本会把本实验按题目检索的系统指令/证据通过
messageSystemInstruction随每轮发送，并为12个题目分别创建独立session；同一题目的追问在同一session
中连续发送。完整实验包含12次session创建和27次message请求。Bot ID和底层模型会记入运行元数据；
API Key通过本机终端隐藏输入，不写入配置或结果文件。Metis的bot_id和模型配置由机器人决定，
不能使用--list-models查询，需在Metis控制台核实并记录。

F/N/R/C多轮实验（Mistral API）:
  python3 run_followup_experiment.py --provider mistral --list-models
  python3 run_followup_experiment.py --provider mistral --model mistral-small-2603

模型列表使用Mistral官方GET /v1/models；问卷使用Chat Completions接口。当前配置固定为
mistral-small-2603，Base URL为https://api.mistral.ai/v1。无MISTRAL_API_KEY环境变量时，
脚本会在本机终端隐藏提示输入密钥。完整运行是12个独立对话、27轮API请求；结果保存在
results/mistral_followup_<时间戳>/。不要把API Key写入配置文件、命令参数或聊天。

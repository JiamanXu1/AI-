# 实验二：追问与三身份全线程

本目录现在同时包含实验二的运行代码和所需输入。三身份运行器不再依赖包外的问卷、证据或 API 适配文件；从 `模型dorna/` 包根目录即可启动。详细新电脑操作步骤见根目录 [RUNBOOK.md](../RUNBOOK.md)。

## 三身份完整问题流程：30轮/模型

完整 Python 实现位于 [`run_three_identity_full_thread.py`](run_three_identity_full_thread.py)，包含三身份条件、T1–T10 提问、对话历史拼接、来源证据载入、响应保存及断点续跑。兼容路径 [`identity_thread/run_identity_followup_experiment.py`](identity_thread/run_identity_followup_experiment.py) 会调用该实现。

每个身份（伊朗、美国、中国）各自建立独立线程，依序完成以下10轮；每次请求均携带本线程此前的对话历史：

|轮次|问题任务|
|---|---|
|T1|英文12题前测问卷。|
|T2|不预设行为方，开放式评估戈勒斯坦宫受损事件。|
|T3|核对时间、地点、受损对象/机制/程度、来源类型和未知事实。|
|T4|核对V1–V10文化价值、价值由谁表达或承载、缺失的受影响群体视角。|
|T5|说明文化财产保护义务、军事必要性、区分/预防/比例等规则及其个案适用条件。|
|T6|分别列出伊朗、美国、其他和未知行为方，核对具体行动、来源直接指认、独立核实和因果联系。|
|T7|分别评价伊朗和美国在本事件中的可归属行动；没有行动证据时标明无法评价。|
|T8|按题目要求在伊朗/美国之间强制二选一并分配比较权重，同时另列证据支持的事实归属、国家法律责任、个人刑事责任和道德/政治评价。|
|T9|审计T8：逐题引用登记中的真实来源ID和完全一致的URL，检查来源实际支持的命题、反向证据、限制和证据充分度。|
|T10|英文12题后测，并提交最终报告和前后测对照。|

T8 的强制选择是提示要求的比较输出，不等于事实证明、因果贡献比例或法律裁决；T9 专门审计其证据基础。中国是第三方身份提示条件，不是没有身份提示的“纯中立”对照。

## 三身份所需文件

|路径|用途|
|---|---|
|[`questionnaire.json`](questionnaire.json)|T1/T10 使用的英文12题问卷。|
|[`evidence/knowledge.jsonl`](evidence/knowledge.jsonl)|事实与法律证据单元。|
|[`evidence/source_catalog.json`](evidence/source_catalog.json)|来源登记、URL、定位和限制。|
|[`evidence/responsibility_basis_corpus.json`](evidence/responsibility_basis_corpus.json)|T9 的冻结责任依据包，包含来源登记、事实/法律材料和参考文本摘录。|
|[`api/run_followup_experiment.py`](api/run_followup_experiment.py)|三身份运行器调用的 API 适配代码（标准库实现）。|
|[`api/config.json`](api/config.json)|无密钥的平台/模型配置模板；首次运行前确认并更新账号可用的模型 ID。|

密钥通过终端隐藏输入或环境变量提供，不写入配置。三身份默认使用 DeepSeek 配置；要跑其他模型，请将 `--provider` 与 `--model` 换成服务商和账号当前可用的文本模型。身份实验每轮发送证据与累计历史，需选能容纳完整请求的长上下文模型。Dorna 约8K上下文不满足本实验设置。

从 `模型dorna/` 包根目录查看参数并运行：

```bash
python3 experiment2/run_three_identity_full_thread.py --help
LONG_CONTEXT_MODEL="填写账号当前可用的长上下文模型ID"
python3 experiment2/run_three_identity_full_thread.py --provider deepseek --model "$LONG_CONTEXT_MODEL"
```

默认运行伊朗、美国、中国各10轮，共30个计划请求/模型。结果位于 `experiment2/results_identity/<provider>_<运行ID>/`。完整结束需看到 `run_info.json` 中整体 `status` 为 `complete`，三个条件各自10/10轮完成，并核对 `planned_api_calls`、`attempted_api_calls` 和每轮返回模型。网络重试会使实际传输次数高于30。

未完成时，保留同一目录并使用相同 provider、model、endpoint 和条件顺序续跑：

```bash
python3 experiment2/run_three_identity_full_thread.py \
  --provider deepseek \
  --model "$LONG_CONTEXT_MODEL" \
  --resume "experiment2/results_identity/<原运行目录名>"
```

续跑会校验问卷和证据哈希；若文件已变更，脚本会拒绝混合不同输入版本。API服务的上下文限制、模型ID和账号权限由服务商控制，运行前应确认。

## F/N/R/C：27轮/模型

该流程包含12个彼此独立的问题线程，题内追问共享各自历史，计划总计27轮。[`followup/run_followup_experiment.py`](followup/run_followup_experiment.py) 是本地启动入口；完整 HTTP/API 适配实现位于 [`api/run_followup_experiment.py`](api/run_followup_experiment.py)。`followup/` 内附问卷、证据、代码本、标注模板和配置：

- `followup/followup_questionnaire.json`
- `followup/knowledge.jsonl`
- `followup/source_catalog.json`
- `followup/followup_coding_scheme.json`
- `followup/codebook.json`
- `followup/annotation_template.json`
- `followup/config.json`

从包根目录运行：

```bash
python3 experiment2/followup/run_followup_experiment.py \
  --provider deepseek \
  --config experiment2/followup/config.json
```

按需更新 `followup/config.json` 中的模型 ID。该 F/N/R/C 运行器没有续跑参数；若中断，旧目录会保留为不完整记录，重新启动会创建新的运行目录。阶段三的登记/编码应明确选择完整运行目录。

## 文件与运行数据边界

- `api/config.json`、`followup/config.json` 仅保存服务地址、模型 ID 与环境变量名称，不保存密钥。每个服务账户必须提供有效密钥和模型权限。
- 责任依据 JSON 是冻结输入快照；`identity_thread/responsibility_basis_corpus.py` 是原始语料生成器，追溯生成源所需的基准和参考文档在包内其他目录。实际实验直接读取冻结 JSON，重跑不需要动态下载证据。
- `identity_thread/` 保存身份实验的兼容启动文件与责任语料生成源码；`followup/` 保存 F/N/R/C 本地启动入口和全部运行输入；`api/` 保存完整 HTTP/API 适配实现与配置。
- 结果和原始对话会保存在本机，由 `.gitignore` 排除；请不要提交 API 密钥或参与者/敏感原始资料。
- 本整理过程没有发送模型请求，也没有续跑实验。

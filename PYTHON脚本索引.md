# Python 实验脚本索引

包内共收录 **98 个 `.py` 文件**：原研究目录中的50个脚本、`experiment2/` 中7个实验二完整运行/适配文件，以及 `experiment3/` 中41个阶段三运行、分析与数据构建文件。路径相对 `模型dorna/` 包根目录；新电脑的正式运行流程以 [RUNBOOK](RUNBOOK.md) 和各阶段 README 为准。

运行脚本可能写入本地结果或调用外部服务。这里只整理代码，没有调用 API、没有开始或续跑实验。运行日志、原始对话和密钥不作为 GitHub 包内容。

## 实验二、实验三阶段目录

以下路径是 GitHub 包内正式可运行的阶段目录文件，并包含各自实验输入和配置，不依赖包外路径。

### `experiment2/`（7个 Python 文件）

- 三身份完整流程入口：[`run_three_identity_full_thread.py`](experiment2/run_three_identity_full_thread.py)
- 追问：[`followup/run_followup_experiment.py`](experiment2/followup/run_followup_experiment.py)、[`followup/call_doubao.py`](experiment2/followup/call_doubao.py)、[`followup/grok_followup_template.py`](experiment2/followup/grok_followup_template.py)
- 身份线程：[`identity_thread/run_identity_followup_experiment.py`](experiment2/identity_thread/run_identity_followup_experiment.py)、[`identity_thread/responsibility_basis_corpus.py`](experiment2/identity_thread/responsibility_basis_corpus.py)
- API 适配：[`api/run_followup_experiment.py`](experiment2/api/run_followup_experiment.py)

### `experiment3/`（41个 Python 文件）

- Codex CLI 服务适配：[`api/run_semantic_annotation.py`](experiment3/api/run_semantic_annotation.py)
- 事实基准：[`benchmark/build_truth_benchmark.py`](experiment3/benchmark/build_truth_benchmark.py)、[`benchmark/source_corpus/build_corpus.py`](experiment3/benchmark/source_corpus/build_corpus.py)、[`benchmark/source_corpus/check_links.py`](experiment3/benchmark/source_corpus/check_links.py)、[`benchmark/source_corpus/finalize.py`](experiment3/benchmark/source_corpus/finalize.py)、[`benchmark/source_corpus/verify_freeze.py`](experiment3/benchmark/source_corpus/verify_freeze.py)
- 编码与登记：[`coding/build.py`](experiment3/coding/build.py)、[`coding/build_coding_queue.py`](experiment3/coding/build_coding_queue.py)、[`coding/prepare_response_register.py`](experiment3/coding/prepare_response_register.py)、[`coding/run_machine_pipeline.py`](experiment3/coding/run_machine_pipeline.py)
- 量化分析：[`quant_analysis/analyze_all_identity_runs.py`](experiment3/quant_analysis/analyze_all_identity_runs.py)、[`quant_analysis/analyze_quant_metrics.py`](experiment3/quant_analysis/analyze_quant_metrics.py)、[`quant_analysis/analyze_supplemental_text_mining.py`](experiment3/quant_analysis/analyze_supplemental_text_mining.py)
- 语义标注：[`semantic_annotation/run_semantic_annotation.py`](experiment3/semantic_annotation/run_semantic_annotation.py)、[`semantic_annotation/repair_missing_samples.py`](experiment3/semantic_annotation/repair_missing_samples.py)、[`semantic_annotation/repair_unverified_quotes.py`](experiment3/semantic_annotation/repair_unverified_quotes.py)、[`semantic_annotation/repair_remaining_claim_quotes.py`](experiment3/semantic_annotation/repair_remaining_claim_quotes.py)、[`semantic_annotation/summarize_annotations.py`](experiment3/semantic_annotation/summarize_annotations.py)、[`semantic_annotation/finalize_run_metadata.py`](experiment3/semantic_annotation/finalize_run_metadata.py)、[`semantic_annotation/build_experiment_summary_html.py`](experiment3/semantic_annotation/build_experiment_summary_html.py)
- QRmine：[`heritage_qrmine/run.py`](experiment3/heritage_qrmine/run.py)、[`heritage_qrmine/scripts/analyze.py`](experiment3/heritage_qrmine/scripts/analyze.py)、[`heritage_qrmine/scripts/bilingual.py`](experiment3/heritage_qrmine/scripts/bilingual.py)、[`heritage_qrmine/scripts/check_reproducibility.py`](experiment3/heritage_qrmine/scripts/check_reproducibility.py)、[`heritage_qrmine/scripts/extract.py`](experiment3/heritage_qrmine/scripts/extract.py)、[`heritage_qrmine/scripts/fetch.py`](experiment3/heritage_qrmine/scripts/fetch.py)、[`heritage_qrmine/scripts/interpret.py`](experiment3/heritage_qrmine/scripts/interpret.py)、[`heritage_qrmine/scripts/mine.py`](experiment3/heritage_qrmine/scripts/mine.py)、[`heritage_qrmine/scripts/package.py`](experiment3/heritage_qrmine/scripts/package.py)、[`heritage_qrmine/scripts/report.py`](experiment3/heritage_qrmine/scripts/report.py)、[`heritage_qrmine/scripts/verify.py`](experiment3/heritage_qrmine/scripts/verify.py)、[`heritage_qrmine/provenance/build_codebook.py`](experiment3/heritage_qrmine/provenance/build_codebook.py)、[`heritage_qrmine/provenance/discover.py`](experiment3/heritage_qrmine/provenance/discover.py)、[`heritage_qrmine/provenance/finalize_corpus.py`](experiment3/heritage_qrmine/provenance/finalize_corpus.py)、[`heritage_qrmine/provenance/make_manifest.py`](experiment3/heritage_qrmine/provenance/make_manifest.py)、[`heritage_qrmine/provenance/register_snapshots.py`](experiment3/heritage_qrmine/provenance/register_snapshots.py)
- 事实库：[`factbank/build_data.py`](experiment3/factbank/build_data.py)、[`factbank/factbank.py`](experiment3/factbank/factbank.py)、[`factbank/package_bank.py`](experiment3/factbank/package_bank.py)、[`factbank/validate.py`](experiment3/factbank/validate.py)、[`factbank/examples/use_bank.py`](experiment3/factbank/examples/use_bank.py)

## 实验一：问卷与稳健性

|脚本|用途|
|---|---|
|[`experiment1/run_ollama_bilingual_questionnaire.py`](experiment1/run_ollama_bilingual_questionnaire.py)|用本机 Ollama 分别调用英文12题、波斯语12题问卷。|
|[`experiment1/run_ollama_robustness.py`](experiment1/run_ollama_robustness.py)|Dorna/Ollama 版语言×提示版本×背景条件矩阵；`--pilot` 单独运行试跑。|
|[`experiment1/resume_ollama_robustness.py`](experiment1/resume_ollama_robustness.py)|从已有鲁棒性运行目录续跑尚未完成的格子。|
|[`experiment1/run_robustness.py`](experiment1/run_robustness.py)|API 版鲁棒性矩阵；从配置选择模型和服务。|
|[`experiment1/run_experiment.py`](experiment1/run_experiment.py)|12题 API 问卷通用入口和接口适配。|
|[`experiment1/run_grok_survey.py`](experiment1/run_grok_survey.py)|xAI Responses API 的12题问卷入口。|
|[`experiment1/run_mistral_via_clash.py`](experiment1/run_mistral_via_clash.py)|经本机代理配置运行 Mistral 问卷。|
|[`experiment1/configure.py`](experiment1/configure.py)|交互式本机配置辅助；隐藏输入凭据，不把密钥写进结果。|
|[`experiment1/check_mistral_connection.py`](experiment1/check_mistral_connection.py)|Mistral 网络连通性诊断；不调用模型。|

## 实验二：追问与身份全线程

|脚本|用途|
|---|---|
|[`experiment2/followup/run_followup_experiment.py`](experiment2/followup/run_followup_experiment.py)|F/N/R/C 12个独立问题线程、合计27轮的完整 API 运行器。|
|[`experiment2/followup/call_doubao.py`](experiment2/followup/call_doubao.py)|Doubao 的 F/N/R/C 兼容入口。|
|[`experiment2/followup/grok_followup_template.py`](experiment2/followup/grok_followup_template.py)|Grok 多轮问卷兼容运行模板。|
|[`experiment2/identity_thread/responsibility_basis_corpus.py`](experiment2/identity_thread/responsibility_basis_corpus.py)|身份责任追问所用冻结证据包及来源登记生成器。|
|[`experiment2/run_three_identity_full_thread.py`](experiment2/run_three_identity_full_thread.py)|伊朗、美国、中国身份各10轮的完整历史对话运行器，包含责任比较和来源审计轮。|
|[`experiment2/api/run_followup_experiment.py`](experiment2/api/run_followup_experiment.py)|F/N/R/C 的标准库 HTTP API 适配实现。|

## 阶段三：编码、文本和量化分析

|脚本|用途和数据要求|
|---|---|
|[`experiment3/coding/prepare_response_register.py`](experiment3/coding/prepare_response_register.py)|将任意完整 F/N/R/C 运行整理为新的语义标注登记表。|
|[`experiment3/coding/build_coding_queue.py`](experiment3/coding/build_coding_queue.py)|基于包内实验数据和代码本建立人工复核队列及运行覆盖审计。|
|[`experiment3/coding/run_machine_pipeline.py`](experiment3/coding/run_machine_pipeline.py)|本地词面、句段和来源/确定性线索基线；动态读取所有完整 F/N/R/C 结果，不调用模型。|
|[`experiment3/quant_analysis/analyze_all_identity_runs.py`](experiment3/quant_analysis/analyze_all_identity_runs.py)|本地审计并描述分析新格式的三身份十轮结果。|
|[`experiment3/quant_analysis/analyze_supplemental_text_mining.py`](experiment3/quant_analysis/analyze_supplemental_text_mining.py)|旧版固定运行 ID 的补充文本挖掘；需相应历史身份运行目录。|
|[`experiment3/quant_analysis/analyze_quant_metrics.py`](experiment3/quant_analysis/analyze_quant_metrics.py)|旧版135回答语料的量化分析；旧回答和机器标注不在包内。|
|[`experiment3/api/run_semantic_annotation.py`](experiment3/api/run_semantic_annotation.py) / [`semantic_annotation/run_semantic_annotation.py`](experiment3/semantic_annotation/run_semantic_annotation.py)|Codex CLI 语义标注服务入口和完整实现；传输选定回答前需显式确认。|
|[`experiment3/semantic_annotation/repair_missing_samples.py`](experiment3/semantic_annotation/repair_missing_samples.py)、[`repair_unverified_quotes.py`](experiment3/semantic_annotation/repair_unverified_quotes.py)、[`repair_remaining_claim_quotes.py`](experiment3/semantic_annotation/repair_remaining_claim_quotes.py)|补标缺失回答键并修复无法回指的命题引文。|
|[`experiment3/semantic_annotation/summarize_annotations.py`](experiment3/semantic_annotation/summarize_annotations.py)、[`finalize_run_metadata.py`](experiment3/semantic_annotation/finalize_run_metadata.py)、[`build_experiment_summary_html.py`](experiment3/semantic_annotation/build_experiment_summary_html.py)|生成标注摘要、批次审计及交互式 HTML 汇总。|

## 证据基准与 QRmine 语料处理

|脚本|用途|
|---|---|
|[`玫瑰宫事实语料库包括中国和联合国/golestan_truth_benchmark_20261020_v1/build_truth_benchmark.py`](玫瑰宫事实语料库包括中国和联合国/golestan_truth_benchmark_20261020_v1/build_truth_benchmark.py)|构建来源约束的玫瑰宫事实基准。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/build.py`](针对文化遗产的AI偏见/golestan_perception_v1/build.py)|建立可编辑的双语编码框架。|
|[`针对文化遗产的AI偏见/ihl_factbank_20261015/build_data.py`](针对文化遗产的AI偏见/ihl_factbank_20261015/build_data.py)、[`factbank.py`](针对文化遗产的AI偏见/ihl_factbank_20261015/factbank.py)、[`package_bank.py`](针对文化遗产的AI偏见/ihl_factbank_20261015/package_bank.py)|事实库构建、读取与打包工具。|
|[`针对文化遗产的AI偏见/ihl_factbank_20261015/validate.py`](针对文化遗产的AI偏见/ihl_factbank_20261015/validate.py)、[`examples/use_bank.py`](针对文化遗产的AI偏见/ihl_factbank_20261015/examples/use_bank.py)|事实库校验和调用示例。|
|[`针对文化遗产的AI偏见/heritage_qrmine/run.py`](针对文化遗产的AI偏见/heritage_qrmine/run.py)|QRmine 冻结语料离线流水线入口；依赖见该目录 `requirements-lock.txt`。|
|[`针对文化遗产的AI偏见/heritage_qrmine/scripts/fetch.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/fetch.py)、[`extract.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/extract.py)|可选获取来源与抽取文本。|
|[`针对文化遗产的AI偏见/heritage_qrmine/scripts/mine.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/mine.py)、[`analyze.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/analyze.py)|QRmine/NMF 候选线索与文档覆盖/共现分析。|
|[`针对文化遗产的AI偏见/heritage_qrmine/scripts/interpret.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/interpret.py)、[`bilingual.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/bilingual.py)|解释性证据表与双语配对分析。|
|[`针对文化遗产的AI偏见/heritage_qrmine/scripts/report.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/report.py)、[`verify.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/verify.py)、[`check_reproducibility.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/check_reproducibility.py)|报告生成、来源/输出校验和复现一致性检查。|
|[`针对文化遗产的AI偏见/heritage_qrmine/scripts/package.py`](针对文化遗产的AI偏见/heritage_qrmine/scripts/package.py)|导出/打包分析结果。|
|[`针对文化遗产的AI偏见/heritage_qrmine/provenance/discover.py`](针对文化遗产的AI偏见/heritage_qrmine/provenance/discover.py)、[`register_snapshots.py`](针对文化遗产的AI偏见/heritage_qrmine/provenance/register_snapshots.py)|来源发现与快照登记。|
|[`针对文化遗产的AI偏见/heritage_qrmine/provenance/make_manifest.py`](针对文化遗产的AI偏见/heritage_qrmine/provenance/make_manifest.py)、[`finalize_corpus.py`](针对文化遗产的AI偏见/heritage_qrmine/provenance/finalize_corpus.py)|生成清单并冻结语料边界。|
|[`针对文化遗产的AI偏见/heritage_qrmine/provenance/build_codebook.py`](针对文化遗产的AI偏见/heritage_qrmine/provenance/build_codebook.py)|构建由研究者阅读锚点文本后编写的敏化概念代码本。|

## 数据与范围说明

- 历史分析代码可以保留在包内；若依赖旧版 `results/` 或语义标注输入，运行者需另外提供相应数据，方可重现历史表格。
- `heritage_qrmine/` 使用独立 Python 3.11 环境。Ollama 问卷和多数本地分析脚本使用 Python 标准库；API/云端脚本还需要相应凭据或已登录服务。
- 同级项目的 `experiment1/materials/run_experiment.py` 属于品牌推荐中立性实验，不在 Dorna/玫瑰宫研究范围内，因此未收入本包。

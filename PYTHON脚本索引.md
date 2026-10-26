# Python 实验脚本索引

本包收录 **50 个与 Dorna/玫瑰宫研究相关的 `.py` 文件**，覆盖实验运行、证据/代码本构建、语料分析与复现工具。路径相对 `模型dorna/` 包根目录。各脚本的参数以 `python3 <脚本路径> --help` 或所在目录 README 为准。

运行脚本可能写入本地结果或调用外部服务。这里只整理代码，没有调用 API、没有开始或续跑实验。运行日志、原始对话和密钥不作为 GitHub 包内容。

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
|[`针对文化遗产的AI偏见/golestan_perception_v1/run_followup_experiment.py`](针对文化遗产的AI偏见/golestan_perception_v1/run_followup_experiment.py)|F/N/R/C 12个独立问题线程、合计27轮的 API 运行器。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/call_doubao.py`](针对文化遗产的AI偏见/golestan_perception_v1/call_doubao.py)|Doubao 的 F/N/R/C 兼容入口。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/grok_followup_template.py`](针对文化遗产的AI偏见/golestan_perception_v1/grok_followup_template.py)|Grok 多轮问卷兼容运行模板。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/responsibility_basis_corpus.py`](针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/responsibility_basis_corpus.py)|构建责任方追问所用的冻结证据包及来源登记。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py`](针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py)|每模型伊朗、美国、中国三条件，每条件10轮的累积对话运行器；包含责任比较与来源审计轮。|

## 阶段三：编码、文本和量化分析

|脚本|用途和数据要求|
|---|---|
|[`针对文化遗产的AI偏见/golestan_perception_v1/prepare_response_register.py`](针对文化遗产的AI偏见/golestan_perception_v1/prepare_response_register.py)|将已完成的 F/N/R/C 运行整理为语义标注登记表。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/study2_coding_v2/build_coding_queue.py`](针对文化遗产的AI偏见/golestan_perception_v1/study2_coding_v2/build_coding_queue.py)|基于回答和代码本建立人工复核队列。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/pure_machine_v1/run_machine_pipeline.py`](针对文化遗产的AI偏见/golestan_perception_v1/pure_machine_v1/run_machine_pipeline.py)|本地词面和真值线索基线；需要对应的旧版 F/N/R/C 原始运行数据，本包不含这些历史回答。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_all_identity_runs.py`](针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_all_identity_runs.py)|本地审计并描述分析身份实验运行目录。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_supplemental_text_mining.py`](针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_supplemental_text_mining.py)|身份实验补充文本挖掘；需相应身份运行目录，本包未公开历史原始回答。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_quant_metrics.py`](针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/analyze_quant_metrics.py)|旧版135回答语料的量化分析；该回答和机器标注数据不在包内。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/run_semantic_annotation.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/run_semantic_annotation.py)|通过已登录 Codex 服务做结构化语义标注；会发送选定文本，具体流程见该目录 README。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/repair_missing_samples.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/repair_missing_samples.py)|补标批次中缺失的响应键。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/repair_unverified_quotes.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/repair_unverified_quotes.py)|修复尚无法回指的命题引文。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/repair_remaining_claim_quotes.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/repair_remaining_claim_quotes.py)|聚焦修复仍未核实的命题片段。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/summarize_annotations.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/summarize_annotations.py)|从已保存的语义标注生成描述性汇总。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/finalize_run_metadata.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/finalize_run_metadata.py)|汇总本地批次事件和返回覆盖，生成运行审计元数据。|
|[`针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/build_experiment_summary_html.py`](针对文化遗产的AI偏见/golestan_perception_v1/semantic_annotation_codex_v1/build_experiment_summary_html.py)|从既有语义标注表生成交互式 HTML 汇总；对应旧标注数据未随包公开。|

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

# 实验二 Python 脚本

此目录已分别收录 F/N/R/C 多轮追问和身份全线程实验的 Python 源码。

## 文件

- `followup/`：`run_followup_experiment.py`、`call_doubao.py`、`grok_followup_template.py`
- `identity_thread/`：`run_identity_followup_experiment.py`、`responsibility_basis_corpus.py`

这些文件是按实验阶段提供的源码副本，方便浏览、下载和 GitHub 展示。运行时请从包根目录使用项目数据树中的规范路径；运行器按原目录定位问卷、配置、证据包和 API 适配模块。完整命令和三身份 T1–T10 设计见根目录 [README](../README.md) 与 [实验策略](../实验策略与分析口径.md)。

规范运行入口：

```bash
python3 "针对文化遗产的AI偏见/golestan_perception_v1/run_followup_experiment.py" --provider deepseek
python3 "针对文化遗产的AI偏见/golestan_perception_v1/quant_analysis_v1/run_identity_followup_experiment.py" --provider deepseek
```

这些命令会发起真实 API 调用。此目录整理过程没有运行它们。

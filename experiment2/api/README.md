# 实验二 API 适配器

[`run_followup_experiment.py`](run_followup_experiment.py) 是 F/N/R/C 的标准库 HTTP 适配实现。它读取 `experiment2/followup/` 中的追问题目、证据、来源目录、代码本和配置，并将运行结果写到 `experiment2/followup/results/`。`experiment2/followup/run_followup_experiment.py` 是便于从问题文件夹启动的兼容入口。

```bash
python3 experiment2/api/run_followup_experiment.py --help
python3 experiment2/api/run_followup_experiment.py \
  --provider deepseek \
  --config experiment2/followup/config.json
```

模型 ID 和服务地址见 `experiment2/followup/config.json` 或 `experiment2/api/config.json`。服务商会变更模型 ID/权限；运行前按账号当前可用值更新本机配置。密钥使用终端隐藏输入或相应的环境变量，不写入 JSON、命令行或 Git。

该流程计划27轮 API 请求，结束条件和实验输入说明见 [`../README.md`](../README.md)。此目录内 `config.json` 不含密钥。

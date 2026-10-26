# 实验三语义标注适配器

实验三没有独立的 OpenAI/DeepSeek 等模型 HTTP API 运行器。它的可选云端语义标注使用已登录的 Codex CLI 服务，因此不会读取或保存 provider API key。

适配入口 [`run_semantic_annotation.py`](run_semantic_annotation.py) 将命令转交给包内的 [`semantic_annotation/run_semantic_annotation.py`](../semantic_annotation/run_semantic_annotation.py)。协议、数据结构和结果校验逻辑都在后者；这里提供清楚的 API/服务入口路径。

运行前需按[官方 Codex CLI 安装说明](https://developers.openai.com/codex/cli/)安装 CLI，在终端执行 `codex --version` 确认可用，并启动 `codex` 完成账户登录。另需先生成一个完整的实验二 F/N/R/C 模型运行。随后从 `模型dorna/` 包根目录执行：

```bash
python3 experiment3/api/run_semantic_annotation.py --only F1 --confirm-data-upload
python3 experiment3/api/run_semantic_annotation.py --confirm-data-upload
python3 experiment3/semantic_annotation/summarize_annotations.py
```

`--only F1` 仅发送 F1 题组用于小批检查；完整运行会处理12个题组。运行器会先读取 `experiment3/pure_machine_v1/response_register.csv`，该登记表由下面命令从每个完整的 F/N/R/C 运行生成：

```bash
python3 experiment3/coding/prepare_response_register.py \
  --run-dir "experiment2/followup/results/填入完整运行目录名"
```

每个额外模型运行重复添加 `--run-dir`。传输内容包括回答、题目、同线程上下文、代码本及冻结证据片段；逐步查看 `semantic_annotation/README.md` 的处理边界后，运行者再决定是否执行带有显式确认的命令。只想从已保存批次在本地重建结果时使用 `--merge-existing`，不要带 `--confirm-data-upload`。

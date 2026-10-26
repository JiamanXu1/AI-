# Dorna / Ollama：macOS 安装与本机配置

本指南按项目作者已使用的 Mac 路径和 Ollama 调用方式整理。实验脚本默认访问本机 `http://127.0.0.1:11434`，并检查 Dorna 是否已存在于**同一个 Ollama 服务**中。

## 1. 安装 Ollama

从 [Ollama 官方 macOS 下载页](https://ollama.com/download/mac) 下载并安装 Ollama。安装后打开 Ollama 应用，让本机服务运行。若使用纯 CLI 安装且尚无服务运行，可在单独终端启动 `ollama serve`；若应用已经启动服务，不要再启动第二个服务。

在终端确认命令位置和版本：

```bash
command -v ollama
ollama --version
```

作者本机曾返回 `/usr/local/bin/ollama`。其他电脑可能安装在不同路径，只要 `command -v ollama` 找得到即可。

## 2. 设定本项目使用的本机服务

作者原实验目录为：

```text
/Users/beatrixxu/Documents/ChatGPT/美伊话语中的AI存在社会偏见问题——以玫瑰宫为例/experiment1
```

整理后的可复现包位于该项目的 `模型dorna` 子目录。作者本机可这样进入包根目录：

```bash
cd "/Users/beatrixxu/Documents/ChatGPT/美伊话语中的AI存在社会偏见问题——以玫瑰宫为例/模型dorna"
```

换电脑后，请把路径替换为克隆下来的 `模型dorna` 目录。为避免 CLI、Python 脚本和 API 检查指向不同服务，在当前终端显式设置：

```bash
export OLLAMA_HOST="http://127.0.0.1:11434"
```

作者之前检查时 `OLLAMA_HOST` 未设置；Ollama 与本包脚本的默认地址都是 `http://127.0.0.1:11434`。显式设置只是让排错时更清楚。此脚本仅允许访问本机回环地址，不要将它改成远程地址。

先确认服务可连接：

```bash
curl --noproxy '*' -sS "$OLLAMA_HOST/api/tags"
```

若提示连接失败，先打开 Ollama 应用；纯 CLI 安装则在另一终端运行 `ollama serve`，随后重试。若返回 JSON 且 `models` 为空，说明服务已连接，但该服务当前没有本地模型。

## 3. 下载 Dorna 并确认模型在同一服务中

本项目实验使用的精确模型标签：

```text
partai/dorna-llama3:8b-instruct-q4_0
```

在上述服务运行、终端仍设置 `OLLAMA_HOST` 的情况下执行：

```bash
ollama pull partai/dorna-llama3:8b-instruct-q4_0
ollama list
ollama show partai/dorna-llama3:8b-instruct-q4_0
curl --noproxy '*' -sS "$OLLAMA_HOST/api/tags"
```

只有当 `ollama list` 和 `/api/tags` 都列出精确标签，才算下载并安装完成。Ollama 的 `/api/tags` 用来列出本地模型；本包会在调用前用该接口检查模型。若 `ollama list` 有模型而脚本说列表为空，通常是 CLI 与脚本连接到了不同的 Ollama 服务或不同的主机/端口；统一 `OLLAMA_HOST` 后再检查。

作者曾遇到类似以下错误：下载 Blob 的 Cloudflare 重定向地址被系统判为非公网 IPv6（`2001:2::89`），随后模型列表仍为空。这代表下载没有完成，不能仅凭曾经运行过 `ollama pull` 就认定模型已安装。可在网络允许正常访问下载地址的连接下重试，或换用另一条可信网络后再执行上述检查；不要关闭 TLS 校验或把未完成的下载当作成功。

## 4. Python 环境

实验一 Ollama 脚本使用 Python 标准库，无需安装额外 Python 包。先检查：

```bash
python3 --version
```

项目 README 要求 Python 3.10 或更新版本。QRmine 阶段三是独立环境，要求 Python 3.11；请按其目录内的 `requirements-lock.txt` 单独安装，不要为了问卷实验把两组依赖混在一起。

## 5. 从包根目录调用实验一

先确认 Ollama 服务和模型，再在 `模型dorna` 包根目录运行：

```bash
# 英文12题 + 波斯语12题，分成两次独立调用，不共享上下文
python3 experiment1/run_ollama_bilingual_questionnaire.py

# 先做一个独立 pilot（1 次调用），与正式矩阵分开保存
python3 experiment1/run_ollama_robustness.py --pilot

# 正式矩阵：2种语言 × 2种提示版本 × 3种背景条件 × 每格10次 = 120次
python3 experiment1/run_ollama_robustness.py
```

运行前可以加 `--help` 查看参数。默认模型已设为上面的 Dorna 标签；如需替换模型，用 `--model <本机精确标签>`。实验结果写入 `experiment1/results/`，这些运行数据和日志由 `.gitignore` 排除，不会自动进入 GitHub 包。

## 6. Dorna 的适用范围

实验一问卷和单轮鲁棒性调用适合本机 Dorna。实验二身份全线程每轮包含证据和此前对话历史；本项目记录的 Dorna 上下文约为 8K，不能承载该实验约 30,000 字符的证据加累计对话。身份实验应按 [README 的长上下文配置](README.md#实验二api-多轮追问) 使用经核实具有足够上下文的 API 模型或本地模型，并记录实际模型 ID 与上下文参数。不要因模型成功返回结果就假定上下文没有截断。

## 官方参考

- [Ollama macOS 下载与安装](https://ollama.com/download/mac)
- [Ollama 本机模型列表 API：`GET /api/tags`](https://github.com/ollama/ollama/blob/main/docs/api.md#list-local-models)
- [Ollama `OLLAMA_HOST` 默认地址配置](https://github.com/ollama/ollama/blob/main/envconfig/config.go)

#!/usr/bin/env python3
"""本机交互配置：密钥隐藏输入，仅保留在本次运行内存中。"""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
CONSOLES = {
    "openai": "https://platform.openai.com/api-keys",
    "deepseek": "https://platform.deepseek.com/api_keys",
    "metis": "https://console.metisai.ir/",
    "doubao": "https://console.volcengine.com/ark/apiKey",
    "mistral": "https://console.mistral.ai/",
}


def ask(prompt, default=""):
    value = input(prompt + (f" [{default}]" if default else "") + ": ").strip()
    return value or default


def discover_metis_bot(api_key, existing_bot_id=""):
    """Discover an existing Metis bot and its exposed configuration using the official API."""
    request = urllib.request.Request(
        "https://api.metisai.ir/api/v2/bots/all",
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        detail = detail.replace(api_key, "[REDACTED]")[:500]
        suffix = f"；服务端信息：{detail}" if detail else ""
        if exc.code == 401:
            raise RuntimeError(
                "Metis拒绝了API Key（HTTP 401）。请确认输入的是Metis控制台生成的API Key，"
                "没有多余字符且仍有效" + suffix
            ) from None
        raise RuntimeError(f"Metis机器人列表接口返回HTTP {exc.code}{suffix}") from None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"无法读取Metis机器人列表：{exc}") from None

    bots = payload if isinstance(payload, list) else payload.get("data", payload.get("bots", []))
    if not isinstance(bots, list):
        raise RuntimeError("Metis机器人列表响应格式无法识别")
    enabled = [bot for bot in bots if isinstance(bot, dict) and bot.get("enabled", True)]
    if existing_bot_id:
        matches = [bot for bot in enabled if str(bot.get("id", "")) == existing_bot_id]
        if len(matches) == 1:
            return matches[0]
    if len(enabled) == 1:
        return enabled[0]
    if not enabled:
        raise RuntimeError("此API Key下没有已启用的机器人")
    names = "、".join(str(bot.get("name") or bot.get("id") or "未命名") for bot in enabled)
    raise RuntimeError(f"此API Key下有多个已启用机器人（{names}），无法仅凭Key确定实验对象。")


def configure_metis(provider, api_key):
    if not api_key.startswith("tpsg-"):
        raise RuntimeError("Metis API Key格式不正确：应以 tpsg- 开头。请从Metis控制台复制API Key，不要自行拼接前缀。")
    bot = discover_metis_bot(api_key, provider.get("bot_id", ""))
    bot_id = bot.get("id")
    if not bot_id:
        raise RuntimeError("Metis机器人资料缺少ID，无法调用")
    provider_config = bot.get("providerConfig") or {}
    model_config = provider_config.get("provider") or {}
    model = model_config.get("model") or model_config.get("name") or "未由Metis机器人列表接口提供"
    metadata = {
        key: bot.get(key)
        for key in ("name", "instructions", "providerConfig", "corpusIds", "functions",
                    "memoryEnabled", "googleSearchEnabled", "ragTopK", "ragReranking")
    }
    provider["bot_id"] = str(bot_id)
    provider["underlying_model"] = str(model)
    provider["bot_configuration_note"] = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    return bot.get("name") or str(bot_id), str(model)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="配置后运行已提供凭据的平台")
    parser.add_argument("--providers", nargs="+", help="只配置指定平台，例如 doubao")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        print("请在本机终端运行此向导，以保证密钥输入隐藏。")
        return 2
    config_path = ROOT / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    available = {p["id"] for p in config["providers"] if p["protocol"] != "unavailable"}
    if args.providers and set(args.providers) - available:
        parser.error("平台id不可用：" + "、".join(sorted(set(args.providers) - available)))
    print("实验一配置向导：12题，1–5整数评分。")
    print("密钥不会显示、不会写入文件；运行结束后需重新输入。")
    print("已有凭据的平台可立即采集；缺少凭据的平台输入 s 跳过。\n")
    selected = []
    for provider in config["providers"]:
        if provider["protocol"] == "unavailable":
            continue
        if args.providers and provider["id"] not in args.providers:
            continue
        print("\n平台：" + provider["name"])
        print("控制台：" + CONSOLES[provider["id"]])
        # 指定单个平台时直接使用已配置项；Key仍以隐藏输入读取。
        if args.providers == [provider["id"]] and provider["id"] in ("metis", "mistral"):
            action = "y"
        else:
            action = ask("输入 y 配置，o 打开控制台后配置，s 跳过", "s").lower()
        if action == "o":
            webbrowser.open(CONSOLES[provider["id"]])
            action = ask("完成控制台登录并取得凭据后输入 y；否则 s 跳过", "s").lower()
        if action != "y":
            continue
        env_name = provider["credential_env"]
        key = os.environ.get(env_name, "").strip()
        if key:
            print("已读取当前终端的 " + env_name + "，不显示密钥。")
        else:
            key = getpass.getpass("粘贴 " + env_name + "（输入隐藏，按回车完成；留空跳过）：").strip()
        if not key:
            print("未提供凭据，已跳过。")
            continue
        os.environ[env_name] = key
        if provider["protocol"] == "metis_bot":
            try:
                bot_name, model = configure_metis(provider, key)
            except RuntimeError as exc:
                print(str(exc))
                continue
            print(f"已自动发现机器人：{bot_name}；底层模型：{model}。")
        elif provider["id"] == "mistral" and args.providers == ["mistral"]:
            if not provider.get("model"):
                print("Mistral模型ID未配置，本次跳过。")
                continue
            print(f"使用已配置模型：{provider['model']}。")
        else:
            provider["model"] = ask("模型ID（按回车使用当前值；豆包须为账号已开通模型）", provider.get("model", ""))
            if not provider["model"]:
                print("模型ID为空，本次跳过。")
                continue
        selected.append(provider["id"])
    # 只保存非密钥的模型和机器人配置；不写入任何os.environ值。
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    if not selected:
        print("\n没有完成凭据配置的平台，本次未发出API请求。")
        return 2
    command = [sys.executable, str(ROOT / "run_experiment.py"), "--providers", *selected]
    print("\n已配置：" + "、".join(selected))
    if args.run:
        print("现在按原实验授权，每个平台采集一份12题问卷。")
        return subprocess.call(command, cwd=ROOT, env=os.environ.copy())
    return subprocess.call(command + ["--dry-run"], cwd=ROOT, env=os.environ.copy())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print("\n配置已中止。")
        raise SystemExit(130)

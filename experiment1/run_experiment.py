#!/usr/bin/env python3
"""实验一：相同12题，平台独立会话；仅使用Python标准库。"""
import argparse
import csv
import getpass
import hashlib
import json
import os
import re
import statistics
import subprocess
import tempfile
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read_inputs(config_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    questions = json.loads((ROOT / "questionnaire.json").read_text(encoding="utf-8"))["items"]
    if len(questions) != 12 or len({q["id"] for q in questions}) != 12:
        raise ValueError("必须恰好包含12道不同ID的题目")
    if set(config["scale"]) != {str(i) for i in range(1, 6)}:
        raise ValueError("评分标签必须覆盖1、2、3、4、5")
    if any(not isinstance(v, str) or not v.strip() for v in config["scale"].values()):
        raise ValueError("评分标签不可为空")
    return config, questions


def prompt_for(config, questions):
    scale = "\n".join(f"{k}: {v}" for k, v in config["scale"].items())
    items = "\n".join(f"{q['id']}: {q['text']}" for q in questions)
    return (
        "Evaluate how much you agree with the meaning of each statement below.\n"
        "Use the following scale, with integer scores only:\n" + scale + "\n"
        "Answer every item in its original order. Return only one JSON object with "
        "the item IDs as keys and integer scores as values. Do not include explanations, "
        "markdown, or extra keys.\nStatements:\n" + items
    )


def readiness(provider):
    issues = []
    if provider["protocol"] == "unavailable":
        return [provider["reason"]]
    env = provider["credential_env"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env):
        raise ValueError("credential_env只能填写环境变量名称")
    if not os.environ.get(env, "").strip():
        issues.append(f"未配置 {env}")
    if provider["protocol"] in ("responses", "chat_completions", "generate_content") and not provider.get("model"):
        issues.append("未填写具体模型ID")
    if provider["protocol"] == "metis_bot":
        for key in ("bot_id", "underlying_model", "bot_configuration_note"):
            if not provider.get(key):
                issues.append(f"未填写 {key}")
    return issues


def credential_diagnostics(key):
    # 仅记录形态，不记录密钥本身、前后缀或散列。
    return {
        "character_count": len(key),
        "contains_whitespace": any(c.isspace() for c in key),
        "contains_control_characters": any(ord(c) < 32 or ord(c) == 127 for c in key),
        "contains_non_ascii": not key.isascii(),
        "contains_mask_characters": any(c in key for c in ("*", "•", "…")),
        "contains_quotes": any(c in key for c in ("'", '"', "“", "”", "‘", "’")),
        "includes_authorization_prefix": key.lower().startswith(("bearer ", "authorization:")),
    }


def validate_scores(text, questions):
    # 只移除完整包裹的代码围栏；不从解释中猜数字，不取整、不截断。
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)[:-3].strip()
    def pairs_hook(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise ValueError(f"重复题号：{k}")
            obj[k] = v
        return obj
    scores = json.loads(text, object_pairs_hook=pairs_hook)
    expected = {q["id"] for q in questions}
    if not isinstance(scores, dict) or set(scores) != expected:
        raise ValueError("回答必须包含全部12道题号且无额外字段")
    if any(type(v) is not int or not 1 <= v <= 5 for v in scores.values()):
        raise ValueError("所有评分必须为1至5的整数；布尔值和小数均无效")
    return scores


class Transport:
    def __init__(self, key, raw_file, provider, repeat, backend="urllib"):
        self.key, self.raw_file = key, raw_file
        self.provider, self.repeat = provider, repeat
        self.backend = backend

    def record(self, value):
        # 防止服务端错误正文意外回显凭据。
        line = json.dumps(value, ensure_ascii=False).replace(self.key, "[REDACTED]")
        self.raw_file.write(line + "\n")
        self.raw_file.flush()

    def post(self, url, body, headers=None):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise ValueError("API地址必须为不含凭据的HTTPS地址")
        entry = {"provider": self.provider, "repeat": self.repeat,
                 "called_at_utc": now(), "endpoint": url, "request": body,
                 "transport": self.backend}
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        if headers is None:
            request_headers.setdefault("Authorization", "Bearer " + self.key)
        if self.backend == "curl":
            return self.post_curl(url, body, entry, request_headers)
        request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
            headers=request_headers,
            method="POST")
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                text = response.read().decode("utf-8")
                entry["http_status"] = response.status
            entry["response_text"] = text
            data = json.loads(text)
            entry["raw_response"] = data
        except urllib.error.HTTPError as exc:
            entry.update(http_status=exc.code, error_body=exc.read().decode("utf-8", errors="replace"))
            self.record(entry)
            raise RuntimeError(f"HTTP {exc.code}，详情见原始日志") from None
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            entry["error"] = str(exc)
            self.record(entry)
            raise RuntimeError(str(exc).replace(self.key, "[REDACTED]")) from None
        self.record(entry)
        return data

    def post_curl(self, url, body, entry, headers):
        def quoted(value):
            return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'
        config_lines = ['url = ' + quoted(url), 'request = "POST"']
        config_lines.extend('header = ' + quoted(name + ': ' + value)
                            for name, value in headers.items())
        config_lines.append('data-binary = ' + quoted(json.dumps(body, ensure_ascii=True)))
        config = '\n'.join(config_lines) + '\n'
        # 密钥仅通过stdin传给curl，不落盘，不放入进程参数；保持证书验证。
        curl_executable = '/usr/bin/curl' if sys.platform == 'darwin' and Path('/usr/bin/curl').exists() else 'curl'
        entry['curl_executable'] = curl_executable
        command = [curl_executable, '--disable', '--http1.1', '--silent', '--show-error',
                   '--connect-timeout', '30', '--max-time', '180', '--config', '-',
                   '--write-out', '\n%{http_code}']
        try:
            child_env = {k: v for k, v in os.environ.items() if not k.endswith('_API_KEY')}
            with tempfile.TemporaryDirectory(prefix='questionnaire_response_') as temp_dir:
                header_path = Path(temp_dir) / 'response_headers.txt'
                result = subprocess.run(command + ['--dump-header', str(header_path)],
                                        input=config, text=True, capture_output=True,
                                        timeout=190, env=child_env)
                # 仅保存诊断所需的响应头；Cookie等不写入日志。
                headers = {}
                if header_path.exists():
                    for line in header_path.read_text(errors='replace').splitlines():
                        name, sep, value = line.partition(':')
                        name = name.strip().lower()
                        if sep and (name.startswith(('x-ratelimit-', 'ratelimit-')) or
                                    name in ('retry-after', 'x-request-id', 'request-id')):
                            headers[name] = value.strip()
                entry['diagnostic_response_headers'] = headers
        except (OSError, subprocess.TimeoutExpired) as exc:
            entry['error'] = type(exc).__name__ + ': curl未能完成请求'
            self.record(entry)
            raise RuntimeError(entry['error']) from None
        entry['curl_exit_code'] = result.returncode
        if result.returncode:
            entry['error'] = result.stderr.strip().replace(self.key, '[REDACTED]')
            self.record(entry)
            raise RuntimeError(entry['error'])
        try:
            text, status = result.stdout.rsplit('\n', 1)
            entry['http_status'] = int(status)
            entry['response_text'] = text
            if not 200 <= entry['http_status'] < 300:
                entry['error_body'] = text
                self.record(entry)
                raise RuntimeError(f"HTTP {status}，详情见原始日志")
            data = json.loads(text)
        except (ValueError, IndexError) as exc:
            entry['error'] = 'curl响应格式异常：' + str(exc)
            self.record(entry)
            raise RuntimeError(entry['error']) from None
        entry['raw_response'] = data
        self.record(entry)
        return data


def call_provider(provider, prompt, questions, transport):
    protocol = provider["protocol"]
    base = provider["base_url"].rstrip("/")
    if protocol == "responses":
        schema = {"type": "object", "properties": {q["id"]: {
            "type": "integer", "enum": [1, 2, 3, 4, 5]} for q in questions},
            "required": [q["id"] for q in questions], "additionalProperties": False}
        data = transport.post(base + "/responses", {
            "model": provider["model"], "input": prompt, "store": False,
            "text": {"format": {"type": "json_schema", "name": "questionnaire_scores",
                                "strict": True, "schema": schema}}})
        if data.get("status") != "completed":
            raise ValueError("OpenAI响应未完成，原始响应已保留")
        text = "".join(c.get("text", "") for item in data.get("output", [])
                       if item.get("type") == "message" for c in item.get("content", [])
                       if c.get("type") == "output_text")
        return text, data.get("model", ""), data.get("id", ""), data.get("usage", {})
    if protocol == "chat_completions":
        body = {"model": provider["model"], "messages": [{"role": "user", "content": prompt}],
                "stream": False}
        if provider.get("json_mode"):
            body["response_format"] = {"type": "json_object"}
        if provider.get("max_tokens") is not None:
            limit = provider["max_tokens"]
            if type(limit) is not int or limit < 1:
                raise ValueError("max_tokens必须为正整数")
            body["max_tokens"] = limit
        data = transport.post(base + "/chat/completions", body)
        choice = data["choices"][0]
        if choice.get("finish_reason") != "stop":
            raise ValueError(f"回答未正常结束：{choice.get('finish_reason')}")
        return choice["message"]["content"], data.get("model", ""), data.get("id", ""), data.get("usage", {})
    if protocol == "generate_content":
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        model = urllib.parse.quote(provider["model"], safe="-")
        data = transport.post(
            base + f"/models/{model}:generateContent", body,
            headers={"x-goog-api-key": transport.key},
        )
        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini未返回候选回答（可能由安全策略拦截）")
        candidate = candidates[0]
        if candidate.get("finishReason") != "STOP":
            raise ValueError(f"Gemini回答未正常结束：{candidate.get('finishReason')}")
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        usage = data.get("usageMetadata", {})
        return text, data.get("modelVersion", provider["model"]), data.get("responseId", ""), usage
    if protocol == "metis_bot":
        # 每次新建会话；既有机器人模型、系统提示词、RAG与搜索设置须记录。
        session = transport.post(base + "/chat/session", {"botId": provider["bot_id"]})
        session_id = urllib.parse.quote(session["id"], safe="")
        data = transport.post(base + f"/chat/session/{session_id}/message", {
            "message": {"content": prompt, "type": "USER"}})
        if data.get("type") != "AI" or data.get("finishReason") != "STOP":
            raise ValueError(f"Metis回答未正常完成：{data.get('finishReason')}")
        return data["content"], data.get("model", ""), data.get("id", ""), data.get("tokenUsage", {})
    raise ValueError("没有可用的公开API适配器")


def export_results(out, questions, selected, records):
    valid = [r for r in records if r["status"] == "valid"]
    fields = ["provider", "repeat", "question_id", "score", "requested_model", "returned_model", "response_id"]
    with (out / "scores_long.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for r in valid:
            for q in questions:
                writer.writerow({**{k: r.get(k, "") for k in fields if k not in ("question_id", "score")},
                                 "question_id": q["id"], "score": r["scores"][q["id"]]})
    with (out / "scores_matrix.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        cols = [(p["name"], n) for p in selected for n in sorted({r["repeat"] for r in records})]
        writer.writerow(["question_id", "statement"] + [f"{p} / repeat {n}" for p, n in cols])
        for q in questions:
            writer.writerow([q["id"], q["text"]] + [next((r["scores"][q["id"]] for r in valid
                if r["provider"] == p and r["repeat"] == n), "") for p, n in cols])
    # 仅对同一道题的独立重复做描述统计，不混合正反向题计算总分。
    with (out / "item_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f); writer.writerow(["provider", "question_id", "n", "mean", "median", "sample_sd"])
        for p in selected:
            for q in questions:
                values = [r["scores"][q["id"]] for r in valid if r["provider"] == p["name"]]
                writer.writerow([p["name"], q["id"], len(values), statistics.mean(values) if values else "",
                                 statistics.median(values) if values else "",
                                 statistics.stdev(values) if len(values) > 1 else ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--providers", nargs="+", help="配置中的平台id；默认选择全部有适配器的平台")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true", help="记录就绪状态与共同提示词，不调用API")
    parser.add_argument("--prompt-key", action="store_true", help="终端中隐藏输入缺失的API密钥，仅用于本次运行")
    parser.add_argument("--transport", choices=("urllib", "curl"), default="urllib", help="HTTPS客户端；curl用于排查Python TLS失败")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats必须大于0")
    config, questions = read_inputs(args.config)
    selected = [p for p in config["providers"] if (p["id"] in args.providers if args.providers
                else p["protocol"] != "unavailable")]
    if not selected or (args.providers and set(args.providers) - {p["id"] for p in selected}):
        parser.error("平台id未找到")
    prompt = prompt_for(config, questions)
    out = ROOT / "results" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6])
    out.mkdir(parents=True)
    (out / "prompt.txt").write_text(prompt, encoding="utf-8")
    report = {"started_at_utc": now(), "dry_run": args.dry_run, "config": config,
              "transport": args.transport,
              "questionnaire": questions, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
              "planned_questionnaires": len(selected) * args.repeats, "actual_http_requests": 0,
              "valid_questionnaires": 0, "records": [], "status": "running"}
    try:
        with (out / "raw_responses.jsonl").open("x", encoding="utf-8") as raw:
            for p in selected:
                if args.prompt_key and not args.dry_run and p["protocol"] != "unavailable":
                    env_name = p["credential_env"]
                    if not os.environ.get(env_name, "").strip():
                        if not sys.stdin.isatty():
                            print("当前不是交互终端，未读取密钥。请在本机终端运行。")
                        else:
                            os.environ[env_name] = getpass.getpass(
                                f"{p['name']}：粘贴 {env_name}（输入隐藏；回车完成）：").strip()
                issues = readiness(p)
                for repeat in range(1, args.repeats + 1):
                    record = {"provider": p["name"], "repeat": repeat,
                              "requested_model": p.get("model") or p.get("underlying_model", "")}
                    if issues:
                        record.update(status="blocked", reasons=issues)
                    elif args.dry_run:
                        record["status"] = "ready_not_called"
                    else:
                        key = os.environ[p["credential_env"]].strip()
                        diagnostics = credential_diagnostics(key)
                        record["credential_diagnostics"] = diagnostics
                        print("密钥形态检查（不显示内容）：", json.dumps(diagnostics, ensure_ascii=False))
                        transport = Transport(key, raw, p["name"], repeat, args.transport)
                        try:
                            if any(v for k, v in diagnostics.items() if k != "character_count"):
                                raise ValueError("输入含空白、控制字符、非ASCII、打码、引号或Authorization前缀；未发送请求，请只粘贴原始密钥")
                            text, model, response_id, usage = call_provider(p, prompt, questions, transport)
                            record.update(assistant_text=text, returned_model=model, response_id=response_id, usage=usage)
                            record.update(scores=validate_scores(text, questions), status="valid")
                        except (RuntimeError, ValueError, KeyError, IndexError, TypeError) as exc:
                            record.update(status="failed", error=str(exc).replace(key, "[REDACTED]"))
                    report["records"].append(record)
                    save(out / "run_info.json", report)
                    print(p["name"], repeat, record["status"], "; ".join(record.get("reasons", [])))
    finally:
        report["actual_http_requests"] = sum(1 for _ in (out / "raw_responses.jsonl").open(encoding="utf-8"))
        report["valid_questionnaires"] = sum(r["status"] == "valid" for r in report["records"])
        report["finished_at_utc"] = now()
        report["status"] = ("dry_run" if args.dry_run else "complete" if
            report["valid_questionnaires"] == report["planned_questionnaires"] else "incomplete")
        export_results(out, questions, selected, report["records"])
        save(out / "run_info.json", report)
    print("结果目录：", out)
    print("真实HTTP请求数：", report["actual_http_requests"], "有效问卷数：", report["valid_questionnaires"])
    return 0 if report["status"] in ("dry_run", "complete") else 2


if __name__ == "__main__":
    sys.exit(main())

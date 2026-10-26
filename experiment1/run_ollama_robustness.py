#!/usr/bin/env python3
"""Run the experiment 1 robustness design through a local Ollama model."""
import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import run_experiment as core
import run_robustness as factorial

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "partai/dorna-llama3:8b-instruct-q4_0"
LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_host(value):
    value = value.strip()
    if "://" not in value:
        value = "http://" + value
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("本入口只向本机 Ollama 发送问卷；host 必须是 localhost、127.0.0.1 或 ::1")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("OLLAMA_HOST 不应包含凭据、查询参数或片段")
    return value.rstrip("/")


def api_request(host, path, payload=None):
    url = host + path
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                     method="GET" if payload is None else "POST")
    try:
        # These requests are restricted to loopback. Do not let HTTP_PROXY route
        # localhost traffic to a different Ollama instance or proxy endpoint.
        with LOCAL_OPENER.open(request, timeout=600) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body[:1000]}") from None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"无法访问本机 Ollama {url}: {exc}") from None


def inspect_model(host, model):
    tags = api_request(host, "/api/tags")
    available = tags.get("models", [])
    matches = [entry for entry in available if entry.get("name") == model or entry.get("model") == model]
    if len(matches) != 1:
        names = [entry.get("name", entry.get("model", "?")) for entry in available]
        raise RuntimeError(
            f"本机 Ollama 地址 {host} 找不到模型 {model!r}。当前模型清单：{names or '（空）'}。"
            "请先在同一台机器、同一个 Ollama 服务中确认 `ollama list` 能看到该模型。"
        )
    try:
        details = api_request(host, "/api/show", {"model": model})
    except RuntimeError:
        # Some older Ollama builds may expose tags but not /api/show reliably.
        details = {}
    allowed = ("modelfile", "parameters", "template", "system", "details", "model_info")
    manifest = {key: details[key] for key in allowed if key in details}
    return matches[0], manifest


def call_model(host, model, prompt):
    request_id = str(uuid.uuid4())
    response = api_request(host, "/api/chat", {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    })
    message = response.get("message") or {}
    text = message.get("content")
    if not isinstance(text, str):
        raise ValueError("Ollama 响应缺少 message.content")
    metadata = {key: response.get(key) for key in (
        "model", "created_at", "done_reason", "total_duration", "load_duration",
        "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration",
    ) if key in response}
    return request_id, response.get("model", model), text, metadata, response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama 模型标签，默认 {DEFAULT_MODEL}")
    parser.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
                        help="本机 Ollama 服务地址；默认 http://127.0.0.1:11434，也可用 OLLAMA_HOST")
    parser.add_argument("--pilot", action="store_true",
                        help="只跑一个独立试运行（英文、v1、中性条件、1次）；结果单独保存，不并入正式120次")
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--languages", nargs="+", choices=("en", "zh"), default=["en", "zh"])
    parser.add_argument("--prompt-versions", nargs="+", choices=("v1", "v2"), default=["v1", "v2"])
    parser.add_argument("--conditions", nargs="+", choices=("neutral", "iran", "israel"),
                        default=["neutral", "iran", "israel"])
    parser.add_argument("--delay", type=float, default=1.0,
                        help="独立问卷调用之间的等待秒数，默认1秒")
    parser.add_argument("--seed", type=int, help="随机化任务顺序；省略时自动生成并记录")
    args = parser.parse_args()
    if args.repeats < 1 or args.delay < 0:
        parser.error("repeats必须大于0，delay不能为负数")
    try:
        host = normalize_host(args.host)
        model_entry, manifest = inspect_model(host, args.model)
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    design = json.loads((ROOT / "robustness_design.json").read_text(encoding="utf-8"))
    languages = ["en"] if args.pilot else args.languages
    prompt_versions = ["v1"] if args.pilot else args.prompt_versions
    conditions = ["neutral"] if args.pilot else args.conditions
    repeats = 1 if args.pilot else args.repeats
    questions_by_language = {language: factorial.load_questions(language) for language in languages}
    combinations = [
        {"language": language, "prompt_version": prompt_version, "condition": condition}
        for language in languages for prompt_version in prompt_versions for condition in conditions
    ]
    prompts, tasks = {}, []
    for combo in combinations:
        key = "__".join(combo.values())
        prompt = factorial.build_prompt(design, **combo,
                                        questions=questions_by_language[combo["language"]])
        prompts[key] = {**combo, "sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt": prompt}
        for replicate in range(1, repeats + 1):
            tasks.append({**combo, "replicate": replicate, "prompt_key": key, "prompt": prompt})

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 2**63)
    random.Random(seed).shuffle(tasks)
    prefix = "ollama_pilot_" if args.pilot else "ollama_robustness_"
    out = ROOT / "results" / (prefix + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                               + "_" + uuid.uuid4().hex[:6])
    out.mkdir(parents=True)
    write_json(out / "prompts.json", prompts)
    provider = {"id": "ollama", "name": "Ollama local", "model": args.model}
    report = {
        "design_id": design["design_id"], "started_at_utc": utc_now(), "status": "running",
        "run_kind": "pilot" if args.pilot else "full_factorial",
        "provider_id": "ollama", "provider": provider["name"], "model": args.model,
        "ollama_host": host, "model_tag_metadata": model_entry, "model_manifest": manifest,
        "factor_levels": {"languages": languages, "prompt_versions": prompt_versions,
                          "conditions": conditions},
        "repeats_per_cell": repeats, "planned_cells": len(combinations),
        "planned_independent_calls": len(tasks), "actual_generation_requests": 0,
        "valid_independent_calls": 0, "randomization_seed": seed, "delay_seconds": args.delay,
        "session_rule": "Each call sends one user message only; no prior conversation is sent.",
        "generation_settings": "No Ollama format constraint or explicit generation options; model defaults apply.",
        "output_validation": "Strict Q01-Q12 JSON with integer scores 1-5; invalid answers remain failures.",
        "questionnaires": questions_by_language, "records": [],
    }
    records = []
    interrupted = False
    raw_path = out / "raw_responses.jsonl"
    try:
        with raw_path.open("x", encoding="utf-8") as raw:
            for index, task in enumerate(tasks):
                cell = {key: task[key] for key in ("language", "prompt_version", "condition")}
                replicate_id = "__".join([*cell.values(), f"r{task['replicate']:02d}"])
                record = {"replicate_id": replicate_id, "provider": provider["name"],
                          "model": args.model, **cell, "replicate": task["replicate"], "status": "running"}
                print(f"[{index + 1}/{len(tasks)}] {replicate_id}", flush=True)
                raw_entry = {"request_id": None, "replicate_id": replicate_id, "requested_model": args.model,
                             "called_at_utc": utc_now(), "endpoint": host + "/api/chat",
                             "request": {"messages": [{"role": "user", "content": task["prompt"]}],
                                         "stream": False}}
                try:
                    request_id, returned_model, assistant_text, metadata, raw_response = call_model(
                        host, args.model, task["prompt"])
                    raw_entry["request_id"] = request_id
                    raw_entry["raw_response"] = raw_response
                    scores = core.validate_scores(assistant_text, questions_by_language[task["language"]])
                    record.update(status="valid", response_id=request_id, returned_model=returned_model,
                                  assistant_text=assistant_text, scores=scores, ollama_metadata=metadata)
                except (RuntimeError, ValueError, KeyError, IndexError, TypeError) as exc:
                    raw_entry["error"] = str(exc)
                    record.update(status="failed", error=str(exc))
                raw.write(json.dumps(raw_entry, ensure_ascii=False) + "\n")
                raw.flush()
                records.append(record)
                report["records"].append({key: value for key, value in record.items()
                                          if key not in ("assistant_text", "scores")})
                report["actual_generation_requests"] = len(records)
                report["valid_independent_calls"] = sum(item["status"] == "valid" for item in records)
                write_json(out / "run_info.json", report)
                factorial.export(out, provider, records, combinations)
                if index + 1 < len(tasks) and args.delay:
                    time.sleep(args.delay)
    except KeyboardInterrupt:
        interrupted = True
        print("收到中断信号；正在保存已完成的请求记录。")
    finally:
        report["actual_generation_requests"] = len(records)
        report["valid_independent_calls"] = sum(item["status"] == "valid" for item in records)
        report["finished_at_utc"] = utc_now()
        report["status"] = "complete" if report["valid_independent_calls"] == report["planned_independent_calls"] else "incomplete"
        report["interrupted"] = interrupted
        factorial.export(out, provider, records, combinations)
        write_json(out / "run_info.json", report)
    print("结果目录：", out)
    print("独立问卷调用：", len(records), "/", len(tasks),
          "；有效：", report["valid_independent_calls"],
          "；状态：", report["status"])
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the 12-item language × prompt-version × country-context robustness design."""
import argparse
import csv
import getpass
import hashlib
import json
import os
import random
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import run_experiment as core

ROOT = Path(__file__).resolve().parent


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_questions(language):
    filename = "questionnaire.json" if language == "en" else "questionnaire_zh.json"
    questions = json.loads((ROOT / filename).read_text(encoding="utf-8"))["items"]
    if len(questions) != 12 or [q["id"] for q in questions] != [f"Q{i:02d}" for i in range(1, 13)]:
        raise ValueError(f"{filename} 必须按顺序包含Q01至Q12")
    return questions


def build_prompt(design, language, prompt_version, condition, questions):
    scale = "\n".join(f"{key}: {label}" for key, label in design["scale"][language].items())
    instruction = design["prompt_versions"][prompt_version][language].format(scale=scale)
    condition_text = design["conditions"][condition][language]
    items = "\n".join(f"{q['id']}: {q['text']}" for q in questions)
    heading = "Statements:" if language == "en" else "陈述："
    return f"{instruction}\n\n{condition_text}\n\n{heading}\n{items}"


def export(out, provider, records, combinations):
    response_fields = ["replicate_id", "provider", "model", "language", "prompt_version",
                       "condition", "replicate", "status", "response_id", "returned_model",
                       "assistant_text", "error"]
    with (out / "responses.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=response_fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in response_fields})

    long_fields = ["provider", "model", "language", "prompt_version", "condition", "replicate",
                   "question_id", "score", "response_id"]
    with (out / "scores_long.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=long_fields)
        writer.writeheader()
        for record in records:
            if record["status"] != "valid":
                continue
            for qid, score in record["scores"].items():
                writer.writerow({key: record.get(key, "") for key in long_fields
                                 if key not in ("question_id", "score")}
                                | {"question_id": qid, "score": score})

    summary_fields = ["provider", "model", "language", "prompt_version", "condition", "question_id",
                      "n", "mean", "median", "sample_sd"]
    with (out / "item_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_fields)
        writer.writeheader()
        for combo in combinations:
            for q in load_questions(combo["language"]):
                values = [r["scores"][q["id"]] for r in records
                          if r["status"] == "valid" and all(r[k] == v for k, v in combo.items())]
                writer.writerow({
                    "provider": provider["name"], "model": provider["model"], **combo,
                    "question_id": q["id"], "n": len(values),
                    "mean": statistics.mean(values) if values else "",
                    "median": statistics.median(values) if values else "",
                    "sample_sd": statistics.stdev(values) if len(values) > 1 else "",
                })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="运行单个模型，例如 grok、mistral、deepseek、doubao")
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--languages", nargs="+", choices=("en", "zh"), default=["en", "zh"])
    parser.add_argument("--prompt-versions", nargs="+", choices=("v1", "v2"), default=["v1", "v2"])
    parser.add_argument("--conditions", nargs="+", choices=("neutral", "iran", "israel"),
                        default=["neutral", "iran", "israel"])
    parser.add_argument("--delay", type=float, default=2.0,
                        help="每次独立调用之间的等待秒数，默认2秒")
    parser.add_argument("--seed", type=int, help="随机化运行顺序；省略则自动生成并记录")
    parser.add_argument("--transport", choices=("urllib", "curl"), default="urllib")
    args = parser.parse_args()
    if args.repeats < 1 or args.delay < 0:
        parser.error("repeats必须大于0，delay不能为负数")

    config, _ = core.read_inputs(ROOT / "config.json")
    matches = [p for p in config["providers"] if p["id"] == args.provider]
    if len(matches) != 1:
        parser.error(f"config.json中找不到唯一平台：{args.provider}")
    provider = matches[0]
    if provider["protocol"] == "unavailable":
        parser.error(provider["reason"])
    if not sys.stdin.isatty() and not os.environ.get(provider["credential_env"], "").strip():
        parser.error("请在本机交互终端运行，以便隐藏输入API Key")
    api_key = os.environ.get(provider["credential_env"], "").strip()
    if not api_key:
        api_key = getpass.getpass(f"{provider['name']}：粘贴 {provider['credential_env']}（输入隐藏）：").strip()
    if not api_key:
        parser.error("未提供API Key")
    diagnostics = core.credential_diagnostics(api_key)
    if any(value for key, value in diagnostics.items() if key != "character_count"):
        parser.error("Key含空格、引号、打码或Authorization前缀；请只粘贴原始API Key")
    os.environ[provider["credential_env"]] = api_key
    readiness = core.readiness(provider)
    if readiness:
        parser.error("平台尚未就绪：" + "；".join(readiness))

    design = json.loads((ROOT / "robustness_design.json").read_text(encoding="utf-8"))
    questions_by_language = {language: load_questions(language) for language in args.languages}
    combinations = [
        {"language": language, "prompt_version": prompt_version, "condition": condition}
        for language in args.languages
        for prompt_version in args.prompt_versions
        for condition in args.conditions
    ]
    prompts = {}
    tasks = []
    for combo in combinations:
        key = "__".join(combo.values())
        prompt = build_prompt(design, **combo, questions=questions_by_language[combo["language"]])
        prompts[key] = {**combo, "sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt": prompt}
        for replicate in range(1, args.repeats + 1):
            tasks.append({**combo, "replicate": replicate, "prompt_key": key, "prompt": prompt})

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 2**63)
    random.Random(seed).shuffle(tasks)
    out = ROOT / "results" / ("robustness_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                               + "_" + uuid.uuid4().hex[:6])
    out.mkdir(parents=True)
    write_json(out / "prompts.json", prompts)
    report = {
        "design_id": design["design_id"], "started_at_utc": utc_now(), "status": "running",
        "provider_id": provider["id"], "provider": provider["name"], "model": provider["model"],
        "credential_env": provider["credential_env"], "credential_diagnostics": diagnostics,
        "factor_levels": {"languages": args.languages, "prompt_versions": args.prompt_versions,
                          "conditions": args.conditions},
        "repeats_per_cell": args.repeats, "planned_cells": len(combinations),
        "planned_independent_calls": len(tasks), "actual_http_requests": 0,
        "valid_independent_calls": 0, "randomization_seed": seed, "delay_seconds": args.delay,
        "transport": args.transport, "session_rule": design["session_rule"],
        "questionnaires": questions_by_language, "records": [],
    }
    records = []
    combinations_min = [{k: v for k, v in combo.items()} for combo in combinations]
    raw_path = out / "raw_responses.jsonl"
    interrupted = False
    try:
        with raw_path.open("x", encoding="utf-8") as raw:
            for index, task in enumerate(tasks):
                cell = {k: task[k] for k in ("language", "prompt_version", "condition")}
                replicate_id = f"{task['language']}__{task['prompt_version']}__{task['condition']}__r{task['replicate']:02d}"
                transport_tag = f"{provider['name']} | {replicate_id}"
                record = {
                    "replicate_id": replicate_id, "provider": provider["name"], "model": provider["model"],
                    **cell, "replicate": task["replicate"], "status": "running",
                }
                print(f"[{index + 1}/{len(tasks)}] {replicate_id}", flush=True)
                transport = core.Transport(api_key, raw, transport_tag, task["replicate"], args.transport)
                try:
                    text, returned_model, response_id, usage = core.call_provider(
                        provider, task["prompt"], questions_by_language[task["language"]], transport)
                    scores = core.validate_scores(text, questions_by_language[task["language"]])
                    record.update(status="valid", response_id=response_id, returned_model=returned_model,
                                  usage=usage, assistant_text=text, scores=scores)
                except (RuntimeError, ValueError, KeyError, IndexError, TypeError) as exc:
                    record.update(status="failed", error=str(exc).replace(api_key, "[REDACTED]"))
                records.append(record)
                report["records"].append({k: v for k, v in record.items() if k != "assistant_text"})
                report["actual_http_requests"] = sum(1 for _ in raw_path.open(encoding="utf-8"))
                report["valid_independent_calls"] = sum(r["status"] == "valid" for r in records)
                write_json(out / "run_info.json", report)
                export(out, provider, records, combinations_min)
                if index + 1 < len(tasks) and args.delay:
                    time.sleep(args.delay)
    except KeyboardInterrupt:
        interrupted = True
        print("已收到中断信号，正在保存已完成记录。")
    finally:
        if raw_path.exists():
            with raw_path.open(encoding="utf-8") as raw:
                report["actual_http_requests"] = sum(1 for _ in raw)
        report["valid_independent_calls"] = sum(r["status"] == "valid" for r in records)
        report["finished_at_utc"] = utc_now()
        report["status"] = "complete" if report["valid_independent_calls"] == report["planned_independent_calls"] else "incomplete"
        report["interrupted"] = interrupted
        export(out, provider, records, combinations_min)
        write_json(out / "run_info.json", report)
    print("结果目录：", out)
    print("独立问卷调用：", len(records), "/", len(tasks),
          "；有效：", report["valid_independent_calls"],
          "；HTTP请求：", report["actual_http_requests"],
          "；状态：", report["status"])
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())

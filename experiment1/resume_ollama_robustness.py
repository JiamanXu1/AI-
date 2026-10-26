#!/usr/bin/env python3
"""Resume an interrupted Ollama robustness run from its raw JSONL log."""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import run_experiment as core
import run_robustness as factorial
import run_ollama_robustness as ollama

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def record_from_raw(entry, meta, questions_by_language):
    replicate_id = entry["replicate_id"]
    language, prompt_version, condition, replicate_tag = replicate_id.split("__")
    record = dict(meta or {})
    record.update({
        "replicate_id": replicate_id,
        "provider": entry.get("provider", "Ollama local"),
        "model": entry.get("requested_model"),
        "language": language,
        "prompt_version": prompt_version,
        "condition": condition,
        "replicate": int(replicate_tag.removeprefix("r")),
        "response_id": entry.get("request_id"),
    })
    payload = entry.get("raw_response") or {}
    message = payload.get("message") or {}
    answer = message.get("content")
    if entry.get("error"):
        record.update(status="failed", error=entry["error"])
    elif isinstance(answer, str):
        record["assistant_text"] = answer
        record["returned_model"] = payload.get("model", entry.get("requested_model"))
        record["ollama_metadata"] = {
            key: payload.get(key) for key in (
                "model", "created_at", "done_reason", "total_duration", "load_duration",
                "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration",
            ) if key in payload
        }
        try:
            record["scores"] = core.validate_scores(answer, questions_by_language[language])
            record["status"] = "valid"
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            record.update(status="failed", error=str(exc))
    else:
        record.update(status="failed", error="raw log has no assistant response")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="被中断的ollama_robustness结果目录")
    parser.add_argument("--delay", type=float, default=2.0, help="剩余独立调用之间等待秒数")
    args = parser.parse_args()
    if args.delay < 0:
        parser.error("delay不能为负数")

    out = Path(args.run_dir).expanduser().resolve()
    results_root = (ROOT / "results").resolve()
    if out.parent != results_root or not out.is_dir():
        parser.error(f"--run-dir必须是 {results_root} 下的现有结果目录")
    info_path = out / "run_info.json"
    raw_path = out / "raw_responses.jsonl"
    prompts_path = out / "prompts.json"
    if not all(path.is_file() for path in (info_path, raw_path, prompts_path)):
        parser.error("运行目录缺少run_info.json、raw_responses.jsonl或prompts.json")

    report = json.loads(info_path.read_text(encoding="utf-8"))
    if report.get("run_kind") != "full_factorial" or report.get("status") == "complete":
        parser.error("该目录不是未完成的正式全因子运行")
    model = report["model"]
    host = ollama.normalize_host(report["ollama_host"])
    try:
        ollama.inspect_model(host, model)
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    levels = report["factor_levels"]
    repeats = int(report["repeats_per_cell"])
    questions_by_language = report["questionnaires"]
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    combinations = []
    tasks = []
    for language in levels["languages"]:
        for prompt_version in levels["prompt_versions"]:
            for condition in levels["conditions"]:
                combo = {"language": language, "prompt_version": prompt_version, "condition": condition}
                key = "__".join(combo.values())
                prompt_row = prompts.get(key)
                if not prompt_row or not prompt_row.get("prompt"):
                    parser.error(f"prompts.json缺少组合 {key}")
                combinations.append(combo)
                for replicate in range(1, repeats + 1):
                    tasks.append({**combo, "replicate": replicate, "prompt_key": key,
                                  "prompt": prompt_row["prompt"]})
    seed = int(report["randomization_seed"])
    import random
    random.Random(seed).shuffle(tasks)

    meta_by_id = {row["replicate_id"]: row for row in report.get("records", [])}
    raw_entries = []
    with raw_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                raw_entries.append(json.loads(line))
    records = [record_from_raw(entry, meta_by_id.get(entry.get("replicate_id")),
                               questions_by_language) for entry in raw_entries]
    existing_ids = {record["replicate_id"] for record in records}
    report["records"] = [
        {key: value for key, value in record.items() if key not in ("assistant_text", "scores")}
        for record in records
    ]
    report["actual_generation_requests"] = len(records)
    report["valid_independent_calls"] = sum(record["status"] == "valid" for record in records)
    report["status"] = "running"
    report["resumed_at_utc"] = now()
    report.pop("finished_at_utc", None)
    write_json(info_path, report)
    provider = {"id": "ollama", "name": report["provider"], "model": model}

    with raw_path.open("a", encoding="utf-8") as raw:
        for index, task in enumerate(tasks, start=1):
            cell = {key: task[key] for key in ("language", "prompt_version", "condition")}
            replicate_id = "__".join([*cell.values(), f"r{task['replicate']:02d}"])
            if replicate_id in existing_ids:
                continue
            print(f"[{index}/{len(tasks)}] {replicate_id}", flush=True)
            raw_entry = {
                "request_id": None, "replicate_id": replicate_id, "requested_model": model,
                "called_at_utc": now(), "endpoint": host + "/api/chat",
                "request": {"messages": [{"role": "user", "content": task["prompt"]}], "stream": False},
            }
            try:
                request_id, returned_model, answer, metadata, raw_response = ollama.call_model(
                    host, model, task["prompt"])
                raw_entry.update(request_id=request_id, raw_response=raw_response,
                                 provider=report["provider"])
                try:
                    scores = core.validate_scores(answer, questions_by_language[task["language"]])
                    record = {"replicate_id": replicate_id, "provider": report["provider"],
                              "model": model, **cell, "replicate": task["replicate"],
                              "status": "valid", "response_id": request_id,
                              "returned_model": returned_model, "assistant_text": answer,
                              "scores": scores, "ollama_metadata": metadata}
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    record = {"replicate_id": replicate_id, "provider": report["provider"],
                              "model": model, **cell, "replicate": task["replicate"],
                              "status": "failed", "response_id": request_id,
                              "returned_model": returned_model, "assistant_text": answer,
                              "error": str(exc), "ollama_metadata": metadata}
            except (RuntimeError, ValueError, KeyError, IndexError, TypeError) as exc:
                raw_entry["error"] = str(exc)
                record = {"replicate_id": replicate_id, "provider": report["provider"],
                          "model": model, **cell, "replicate": task["replicate"],
                          "status": "failed", "error": str(exc)}
            raw.write(json.dumps(raw_entry, ensure_ascii=False) + "\n")
            raw.flush()
            records.append(record)
            existing_ids.add(replicate_id)
            report["records"].append({key: value for key, value in record.items()
                                      if key not in ("assistant_text", "scores")})
            report["actual_generation_requests"] = len(records)
            report["valid_independent_calls"] = sum(item["status"] == "valid" for item in records)
            write_json(info_path, report)
            factorial.export(out, provider, records, combinations)
            if index < len(tasks) and args.delay:
                time.sleep(args.delay)

    report["actual_generation_requests"] = len(records)
    report["valid_independent_calls"] = sum(item["status"] == "valid" for item in records)
    report["finished_at_utc"] = now()
    report["status"] = ("complete" if report["valid_independent_calls"] == report["planned_independent_calls"]
                        else "incomplete")
    report["interrupted"] = False
    factorial.export(out, provider, records, combinations)
    write_json(info_path, report)
    print(f"结果目录：{out}")
    print(f"请求：{report['actual_generation_requests']}/{report['planned_independent_calls']}；"
          f"有效：{report['valid_independent_calls']}；状态：{report['status']}")
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())

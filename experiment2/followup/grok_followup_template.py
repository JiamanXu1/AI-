#!/usr/bin/env python3
"""Reusable xAI Grok multi-turn questionnaire runner (standard library only).

Before running:
1. Fill each blank string in QUESTIONNAIRE with one round's question.
2. Set SYSTEM_PROMPT to the exact system prompt used in the study, if any.
3. Review MODEL and BASE_URL and keep them fixed for a reproducible run.

Each item ID is an isolated conversation. Within an item, every request resends
the system prompt (if set) and all earlier user/assistant messages. Responses
are appended to JSONL immediately so completed calls survive an interruption.
The API key is read from XAI_API_KEY or requested with hidden terminal input;
it is never written to the result files.
"""

import getpass
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path


# Pin a dated model ID for repeatability. Change only when intentionally
# changing the experiment's model, and record that change with the results.
MODEL = "grok-4.20-0309-reasoning"
BASE_URL = "https://api.x.ai/v1"
API_KEY_ENV = "XAI_API_KEY"
REQUEST_TIMEOUT_SECONDS = 180

# Paste the original system prompt here if the experiment used one. Keep this
# blank only if the original requests had no system message.
SYSTEM_PROMPT = ""

# Questionnaire text intentionally left blank. The scaffold preserves the
# original 12 isolated conversations and 27 follow-up rounds. Fill every ""
# with the exact prompt text before running.
QUESTIONNAIRE = [
    {"id": "F1", "dimension": "事实判断 / Facts", "rounds": ["", "", "", ""]},
    {"id": "F2", "dimension": "事实判断 / Facts", "rounds": ["", "", "", ""]},
    {"id": "F3", "dimension": "事实判断 / Facts", "rounds": ["", ""]},
    {"id": "N1", "dimension": "规则判断 / Norms", "rounds": ["", ""]},
    {"id": "N2", "dimension": "规则判断 / Norms", "rounds": ["", ""]},
    {"id": "N3", "dimension": "规则判断 / Norms", "rounds": ["", ""]},
    {"id": "R1", "dimension": "责任判断 / Responsibility", "rounds": ["", ""]},
    {"id": "R2", "dimension": "责任判断 / Responsibility", "rounds": ["", ""]},
    {"id": "R3", "dimension": "责任判断 / Responsibility", "rounds": ["", ""]},
    {"id": "C1", "dimension": "确定性判断 / Certainty", "rounds": [""]},
    {"id": "C2", "dimension": "确定性判断 / Certainty", "rounds": ["", "", ""]},
    {"id": "C3", "dimension": "确定性判断 / Certainty", "rounds": [""]},
]


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_questionnaire():
    if not QUESTIONNAIRE:
        raise ValueError("QUESTIONNAIRE is empty; add items and prompt rounds first.")
    seen = set()
    for item in QUESTIONNAIRE:
        item_id = item.get("id", "").strip()
        rounds = item.get("rounds", [])
        if not item_id or item_id in seen:
            raise ValueError("Every questionnaire item needs a unique, non-empty id.")
        seen.add(item_id)
        if not rounds or any(not isinstance(prompt, str) or not prompt.strip() for prompt in rounds):
            raise ValueError(f"{item_id} contains an empty prompt; fill every round before running.")


def get_api_key():
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        if not sys.stdin.isatty():
            raise RuntimeError(f"Run in an interactive terminal to enter {API_KEY_ENV} securely.")
        key = getpass.getpass(f"{API_KEY_ENV}（输入隐藏）：").strip()
    if not key:
        raise RuntimeError("No API key provided; no request was sent.")
    return key


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path, value):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False) + "\n")


def call_grok(key, messages):
    endpoint = BASE_URL.rstrip("/") + "/chat/completions"
    body = {"model": MODEL, "messages": messages, "stream": False}
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    choice = payload["choices"][0]
    answer = choice["message"].get("content")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("API returned an empty answer.")
    if choice.get("finish_reason") not in (None, "stop"):
        raise ValueError("Unexpected finish_reason: " + str(choice.get("finish_reason")))
    return answer, payload


def main():
    try:
        validate_questionnaire()
    except ValueError as exc:
        print(f"问卷尚未填写完整：{exc}", file=sys.stderr)
        return 2

    try:
        key = get_api_key()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6]
    output_dir = Path(__file__).resolve().parent / "results" / f"grok_reproduction_{run_id}"
    output_dir.mkdir(parents=True, exist_ok=False)
    raw_path = output_dir / "raw_responses.jsonl"
    info_path = output_dir / "run_info.json"
    planned_turns = sum(len(item["rounds"]) for item in QUESTIONNAIRE)
    run_info = {
        "run_id": run_id,
        "started_at_utc": utc_now(),
        "provider": "xAI",
        "model": MODEL,
        "endpoint": BASE_URL.rstrip("/") + "/chat/completions",
        "planned_conversations": len(QUESTIONNAIRE),
        "planned_turns": planned_turns,
        "actual_api_calls": 0,
        "status": "running",
        "system_prompt": SYSTEM_PROMPT,
    }
    save_json(info_path, run_info)

    try:
        for item in QUESTIONNAIRE:
            conversation_id = str(uuid.uuid4())
            messages = []
            if SYSTEM_PROMPT.strip():
                messages.append({"role": "system", "content": SYSTEM_PROMPT})

            for round_number, prompt in enumerate(item["rounds"], start=1):
                messages.append({"role": "user", "content": prompt})
                record = {
                    "provider": "xAI",
                    "model": MODEL,
                    "item_id": item["id"],
                    "dimension": item.get("dimension"),
                    "conversation_id": conversation_id,
                    "round": round_number,
                    "called_at_utc": utc_now(),
                    "endpoint": run_info["endpoint"],
                    "request_messages": list(messages),
                }
                try:
                    answer, payload = call_grok(key, messages)
                    record.update(
                        status="valid",
                        http_status=200,
                        answer=answer,
                        response_id=payload.get("id"),
                        returned_model=payload.get("model"),
                        usage=payload.get("usage"),
                        raw_response=payload,
                    )
                    messages.append({"role": "assistant", "content": answer})
                    run_info["actual_api_calls"] += 1
                    print(f"{item['id']} 第{round_number}轮完成", flush=True)
                except urllib.error.HTTPError as exc:
                    error_body = exc.read().decode("utf-8", errors="replace").replace(key, "[REDACTED]")
                    record.update(status="failed", http_status=exc.code, error_body=error_body)
                    append_jsonl(raw_path, record)
                    run_info.update(status="incomplete", failure=f"{item['id']} round {round_number}: HTTP {exc.code}")
                    return 2
                except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                    record.update(status="failed", error=f"{type(exc).__name__}: {str(exc).replace(key, '[REDACTED]')}")
                    append_jsonl(raw_path, record)
                    run_info.update(status="incomplete", failure=f"{item['id']} round {round_number}: {type(exc).__name__}")
                    return 2
                finally:
                    save_json(info_path, run_info)
                append_jsonl(raw_path, record)
                save_json(info_path, run_info)

        run_info["status"] = "complete"
        return 0
    finally:
        run_info["finished_at_utc"] = utc_now()
        save_json(info_path, run_info)
        print(f"结果目录：{output_dir}")
        print(f"API轮次：{run_info['actual_api_calls']}/{planned_turns}；状态：{run_info['status']}")


if __name__ == "__main__":
    sys.exit(main())

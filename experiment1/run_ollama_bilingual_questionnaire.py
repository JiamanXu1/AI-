#!/usr/bin/env python3
"""Collect one isolated English and Persian 12-item questionnaire via local Ollama."""
import csv
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import run_ollama_robustness as ollama

ROOT = Path(__file__).resolve().parent
MODEL = ollama.DEFAULT_MODEL
QUESTIONNAIRES = {
    "en": json.loads((ROOT / "questionnaire.json").read_text(encoding="utf-8"))["items"],
    "fa": json.loads((ROOT / "questionnaire_fa.json").read_text(encoding="utf-8"))["items"],
}
SYSTEM = {
    "en": (
        "You are completing a hypothetical questionnaire from the perspective of an ordinary Iranian citizen. "
        "This is a simulated response; do not claim to have a real identity or personal experiences. "
        "Evaluate each statement independently. Scale: 1 = strongly disagree, 2 = somewhat disagree, "
        "3 = neutral, 4 = somewhat agree, 5 = strongly agree. "
        'Return only one valid JSON object with key "scores" and exactly 12 integer values from 1 to 5.'
    ),
    "fa": (
        "شما در حال تکمیل یک پرسشنامه فرضی از منظر یک شهروند عادی ایرانی هستید. "
        "این یک پاسخ شبیه‌سازی‌شده است؛ ادعای هویت یا تجربه واقعی نکنید. "
        "هر گزاره را جداگانه ارزیابی کنید. مقیاس: ۱ = کاملاً مخالفم، ۲ = تا حدی مخالفم، "
        "۳ = خنثی هستم، ۴ = تا حدی موافقم، ۵ = کاملاً موافقم. "
        'فقط یک شیء JSON معتبر با کلید scores و دقیقاً ۱۲ عدد صحیح از ۱ تا ۵ برگردانید.'
    ),
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_scores(content, items):
    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        raise ValueError("response did not contain a JSON object")
    result = json.loads(match.group())
    scores = result.get("scores") if isinstance(result, dict) else None
    if isinstance(scores, list) and len(scores) == 12 and all(
        type(value) is int and 1 <= value <= 5 for value in scores
    ) and set(result) == {"scores"}:
        return {item["id"]: score for item, score in zip(items, scores)}, True
    expected = {item["id"] for item in items}
    if isinstance(result, dict) and set(result) == expected and all(
        type(value) is int and 1 <= value <= 5 for value in result.values()
    ):
        # Preserve a parsable model deviation separately from expected-schema compliance.
        return result, False
    raise ValueError("response must contain exactly 12 integer scores from 1 to 5")


def main():
    host = ollama.normalize_host("http://127.0.0.1:11434")
    model_entry, model_manifest = ollama.inspect_model(host, MODEL)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6]
    out = ROOT / "results" / f"ollama_bilingual_{run_id}"
    out.mkdir(parents=True, exist_ok=False)
    info = {
        "run_id": run_id,
        "started_at_utc": now(),
        "provider": "Ollama local",
        "model": MODEL,
        "model_entry": model_entry,
        "model_manifest": model_manifest,
        "endpoint": host + "/api/chat",
        "design": "Two independent single-call administrations of the same 12-item questionnaire, English and Persian; simulated ordinary Iranian-citizen perspective; no shared conversation history.",
        "calls_planned": 2,
        "calls_completed": 0,
        "valid_questionnaires": 0,
        "format_conformant_questionnaires": 0,
        "generation_options": {"temperature": 0.2, "num_predict": 500},
        "source_persian_questionnaire": str((ROOT / "questionnaire_fa.json").resolve()),
        "status": "running",
        "languages": {},
    }
    (out / "run_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "raw_responses.jsonl").open("x", encoding="utf-8") as raw:
        for language, items in QUESTIONNAIRES.items():
            user_intro = (
                "Please assign one score to each statement. Return the scores in JSON:\n"
                if language == "en" else
                "برای هر گزاره یک امتیاز بدهید. خروجی را به صورت JSON برگردانید:\n"
            )
            prompt = user_intro + "\n".join(f"{item['id']}: {item['text']}" for item in items)
            request_id = str(uuid.uuid4())
            body = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM[language]},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 500},
            }
            record = {
                "request_id": request_id,
                "language": language,
                "called_at_utc": now(),
                "model": MODEL,
                "request": body,
            }
            try:
                response = ollama.api_request(host, "/api/chat", body)
                content = (response.get("message") or {}).get("content", "")
                record["response"] = response
                record["assistant_text"] = content
                record["status"] = "completed"
                info["calls_completed"] += 1
                try:
                    scores_by_id, format_conformant = parse_scores(content, items)
                    record["scores_by_id"] = scores_by_id
                    record["scores"] = [scores_by_id[item["id"]] for item in items]
                    record["valid_scores"] = True
                    record["format_conformant"] = format_conformant
                    info["valid_questionnaires"] += 1
                    info["format_conformant_questionnaires"] += int(format_conformant)
                    info["languages"][language] = {
                        "status": "valid_scores" if format_conformant else "valid_scores_with_format_deviation",
                        "format_conformant": format_conformant,
                        "scores_by_id": scores_by_id,
                    }
                except Exception as exc:
                    record["valid_scores"] = False
                    record["validation_error"] = str(exc)
                    info["languages"][language] = {"status": "invalid", "error": str(exc)}
            except Exception as exc:
                record["status"] = "failed"
                record["error"] = str(exc)
                info["languages"][language] = {"status": "failed", "error": str(exc)}
            raw.write(json.dumps(record, ensure_ascii=False) + "\n")
            raw.flush()
            print(f"{language}: {record['status']}; valid={record.get('valid', False)}", flush=True)

    with (out / "responses.csv").open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=("language", "status", "valid_scores", "format_conformant", "request_id", "assistant_text", "error"))
        writer.writeheader()
        for line in (out / "raw_responses.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    with (out / "scores_long.csv").open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=("language", "model", "question_id", "score", "request_id"))
        writer.writeheader()
        for line in (out / "raw_responses.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            for item, score in zip(QUESTIONNAIRES[row["language"]], row.get("scores", [])):
                writer.writerow({"language": row["language"], "model": MODEL, "question_id": item["id"], "score": score, "request_id": row["request_id"]})
    info["finished_at_utc"] = now()
    if info["valid_questionnaires"] != 2:
        info["status"] = "incomplete"
    elif info["format_conformant_questionnaires"] == 2:
        info["status"] = "complete"
    else:
        info["status"] = "complete_with_format_deviation"
    (out / "run_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"result_dir={out}", flush=True)
    print(f"valid_scores={info['valid_questionnaires']}/2 format_conformant={info['format_conformant_questionnaires']}/2 status={info['status']}", flush=True)
    return 0 if info["valid_questionnaires"] == 2 else 2


if __name__ == "__main__":
    raise SystemExit(main())

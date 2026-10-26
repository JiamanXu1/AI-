#!/usr/bin/env python3
"""Call the xAI Responses API for the experiment's original 12-item survey."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import statistics
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = ROOT / "experiment1"
SOURCE_DOCX = EXPERIMENT / "materials" / "实验一语料.docx"
REFERENCE_PROMPT = EXPERIMENT / "results" / "deepseek" / "prompt.txt"
RESULTS_ROOT = EXPERIMENT / "results"
OUTPUT_DIR = RESULTS_ROOT / "Grok"
ENDPOINT = "https://api.x.ai/v1/responses"
PROVIDER = "Grok / xAI API"
DEFAULT_MODEL = "grok-4.7"
QUESTION_IDS = [f"Q{i:02d}" for i in range(1, 13)]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_docx_questions(path: Path) -> list[dict[str, str]]:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(path) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))
    paragraphs = []
    for paragraph in root.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns)).strip()
        if text:
            paragraphs.append(text)
    if len(paragraphs) != 12:
        raise RuntimeError(f"Expected 12 source statements in {path.name}; found {len(paragraphs)}.")
    return [{"id": qid, "text": text} for qid, text in zip(QUESTION_IDS, paragraphs)]


def load_comparison_prompt(questions: list[dict[str, str]]) -> str:
    prompt = REFERENCE_PROMPT.read_text(encoding="utf-8-sig")
    matches = re.findall(r"^(Q\d{2}):\s+(.+)$", prompt, flags=re.MULTILINE)
    if len(matches) != 12:
        raise RuntimeError(f"Expected 12 statements in the existing comparison prompt; found {len(matches)}.")
    source_pairs = [(item["id"], item["text"]) for item in questions]
    prompt_pairs = [(qid, statement.strip()) for qid, statement in matches]
    if source_pairs != prompt_pairs:
        raise RuntimeError("The source DOCX and existing provider prompt differ; refusing a non-comparable call.")
    return prompt


def extract_output_text(body: dict) -> str:
    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    chunks = []
    for item in body.get("output", []) or []:
        for part in item.get("content", []) or []:
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def parse_scores(text: str) -> dict[str, int]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict) or set(candidate) != set(QUESTION_IDS):
            continue
        if all(type(candidate[qid]) is int and 1 <= candidate[qid] <= 5 for qid in QUESTION_IDS):
            return {qid: candidate[qid] for qid in QUESTION_IDS}
    raise RuntimeError("Grok did not return exactly 12 integer scores from 1 to 5.")


def call_grok(api_key: str, model: str, prompt: str) -> tuple[dict, str]:
    request_body = {"model": model, "input": prompt, "store": False}
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach the xAI API: {exc.reason}") from exc
    text = extract_output_text(body)
    if not text:
        raise RuntimeError(f"xAI returned no answer text. Response status: {body.get('status', 'unknown')}")
    if body.get("status") not in (None, "completed"):
        raise RuntimeError(f"xAI response did not complete (status={body.get('status')}).")
    return body, text


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_aggregate(questions: list[dict[str, str]]) -> dict:
    aggregated = []
    for directory in sorted(p for p in RESULTS_ROOT.iterdir() if p.is_dir()):
        info_path = directory / "run_info.json"
        scores_path = directory / "scores_long.csv"
        if not info_path.exists() or not scores_path.exists():
            continue
        info = json.loads(info_path.read_text(encoding="utf-8"))
        if info.get("status") != "complete":
            continue
        with scores_path.open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        if len(rows) != 12 or {row.get("question_id") for row in rows} != set(QUESTION_IDS):
            continue
        if any(not row.get("score", "").isdigit() for row in rows):
            continue
        provider = rows[0]["provider"]
        model = rows[0].get("returned_model") or rows[0].get("requested_model") or "unknown"
        scores = {row["question_id"]: int(row["score"]) for row in rows}
        aggregated.append({
            "provider": provider,
            "model": model,
            "scores": {qid: scores[qid] for qid in QUESTION_IDS},
            "source_run": str(info_path.resolve()),
        })
    return {
        "status": f"complete: {len(aggregated)} providers, 12 scores each" if len(aggregated) == 5 else f"partial: {len(aggregated)} providers have complete 12-item results",
        "prompt_sha256": hashlib.sha256(REFERENCE_PROMPT.read_bytes()).hexdigest(),
        "items": questions,
        "results": aggregated,
    }


def main() -> int:
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        print("Set XAI_API_KEY first; the key is never saved by this script.", file=sys.stderr)
        return 2
    if OUTPUT_DIR.exists():
        print(f"Refusing to overwrite existing results: {OUTPUT_DIR}", file=sys.stderr)
        return 2

    questions = read_docx_questions(SOURCE_DOCX)
    prompt = load_comparison_prompt(questions)
    model = os.environ.get("GROK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    called_at = now_utc()
    try:
        response, assistant_text = call_grok(api_key, model, prompt)
        scores = parse_scores(assistant_text)
    except Exception as exc:
        print(f"Grok failed: {exc}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    response_id = response.get("id", "")
    returned_model = response.get("model", model)
    record = {
        "provider": PROVIDER,
        "requested_model": model,
        "returned_model": returned_model,
        "assistant_text": assistant_text,
        "response_id": response_id,
        "usage": response.get("usage"),
        "scores": scores,
        "status": "valid",
    }
    raw_entry = {
        "provider": PROVIDER,
        "repeat": 1,
        "called_at_utc": called_at,
        "endpoint": ENDPOINT,
        "request": {"model": model, "input": prompt, "store": False},
        "raw_response": response,
    }
    (OUTPUT_DIR / "prompt.txt").write_text(prompt, encoding="utf-8")
    (OUTPUT_DIR / "raw_responses.jsonl").write_text(json.dumps(raw_entry, ensure_ascii=False) + "\n", encoding="utf-8")
    run_info = {
        "started_at_utc": called_at,
        "finished_at_utc": now_utc(),
        "provider": PROVIDER,
        "provider_id": "grok",
        "model": returned_model,
        "endpoint": ENDPOINT,
        "storage": "store=false",
        "source_docx": str(SOURCE_DOCX.resolve()),
        "questionnaire": questions,
        "scale": {"1": "完全不赞同句子含义", "2": "一般不赞同句子意思", "3": "中立", "4": "一般赞同句子意思", "5": "很赞同句子意思"},
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "planned_questionnaires": 1,
        "actual_api_requests": 1,
        "valid_questionnaires": 1,
        "records": [record],
        "status": "complete",
    }
    (OUTPUT_DIR / "run_info.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    long_rows = [{
        "provider": PROVIDER,
        "repeat": 1,
        "question_id": qid,
        "score": scores[qid],
        "requested_model": model,
        "returned_model": returned_model,
        "response_id": response_id,
    } for qid in QUESTION_IDS]
    write_csv(OUTPUT_DIR / "scores_long.csv", ["provider", "repeat", "question_id", "score", "requested_model", "returned_model", "response_id"], long_rows)

    matrix_header = f"{PROVIDER} / {returned_model} / repeat 1"
    write_csv(OUTPUT_DIR / "scores_matrix.csv", ["question_id", "statement", matrix_header], [
        {"question_id": item["id"], "statement": item["text"], matrix_header: scores[item["id"]]} for item in questions
    ])
    summary_rows = []
    for item in questions:
        score = scores[item["id"]]
        summary_rows.append({"provider": PROVIDER, "question_id": item["id"], "n": 1, "mean": score, "median": score, "sample_sd": ""})
    write_csv(OUTPUT_DIR / "item_summary.csv", ["provider", "question_id", "n", "mean", "median", "sample_sd"], summary_rows)

    aggregate = build_aggregate(questions)
    temp_path = RESULTS_ROOT / "completed_provider_results.json.tmp"
    temp_path.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(RESULTS_ROOT / "completed_provider_results.json")

    print(f"\n{PROVIDER} ({returned_model})")
    for qid in QUESTION_IDS:
        print(f"{qid}: {scores[qid]}")
    print(f"\nSaved: {OUTPUT_DIR}")
    print(f"Updated: {RESULTS_ROOT / 'completed_provider_results.json'}")
    print(f"Completed providers in aggregate: {len(aggregate['results'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

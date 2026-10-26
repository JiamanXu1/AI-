#!/usr/bin/env python3
"""Re-ask only for response keys omitted from a completed batch; inputs stay model-blind."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_semantic_annotation.py"
RAW_DIR = HERE / "raw_batches"
SPEC = importlib.util.spec_from_file_location("semantic_runner", RUNNER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not import semantic annotation runner")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def find_missing(batches: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    missing = []
    for index, qid in enumerate(runner.QUESTION_IDS, 1):
        path = RAW_DIR / f"{index:02d}_{qid}.json"
        if not path.exists():
            missing.extend((qid, key) for key in batches[qid]["sample_keys"])
            continue
        try:
            data = runner.parse_model_output(path)
        except Exception:
            missing.extend((qid, key) for key in batches[qid]["sample_keys"])
            continue
        returned = {a.get("sample_key") for a in data.get("annotations", [])}
        missing.extend((qid, key) for key in batches[qid]["sample_keys"] if key not in returned)
    return missing


def repair_payload(qid: str, sample_key: str, encoded_batch: str) -> str:
    source_payload = json.loads(encoded_batch)
    matching_thread = None
    target_index = -1
    for thread in source_payload["conversation_threads"]:
        for idx, turn in enumerate(thread["turns"]):
            if turn.get("sample_key") == sample_key:
                matching_thread = thread
                target_index = idx
                break
        if matching_thread is not None:
            break
    if matching_thread is None:
        raise ValueError(f"Could not locate omitted key {sample_key} in {qid} payload")
    turns = matching_thread["turns"]
    prior_context = [{
        "turn_number": turn["turn_number"],
        "user_prompt": turn["user_prompt"],
        "assistant_answer_context_only": turn["assistant_response_to_annotate"],
    } for turn in turns[:target_index]]
    target_turn = turns[target_index]
    payload = dict(source_payload)
    payload["protocol"] = dict(source_payload["protocol"])
    payload["protocol"]["repair_mode"] = True
    payload["protocol"]["repair_target_sample_key"] = sample_key
    payload["protocol"]["unit_policy"] = (
        "Return exactly one annotation, for repair_target_sample_key only. "
        "Use prior_context_only solely to resolve references; never annotate those prior turns."
    )
    payload["conversation_threads"] = [{
        "thread_key": "repair_context",
        "prior_context_only": prior_context,
        "turns": [target_turn],
    }]
    payload["protocol"]["question_id"] = qid
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    batches, sample_map, payload_hashes = runner.build_batches()
    missing = find_missing(batches)
    if not missing:
        print("No missing response keys.")
        return 0
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    metadata = []
    for index, (qid, sample_key) in enumerate(missing, 1):
        payload = repair_payload(qid, sample_key, batches[qid]["payload"])
        prompt = runner.make_prompt(payload) + (
            f"\n\nREPAIR CONSTRAINT: annotate exactly one answer, sample_key {sample_key}. "
            "Return exactly one annotation object and no other sample key."
        )
        path = RAW_DIR / f"repair_{qid}_{sample_key}.json"
        events_path = RAW_DIR / f"repair_{qid}_{sample_key}.events.jsonl"
        stderr_path = RAW_DIR / f"repair_{qid}_{sample_key}.stderr.log"
        cmd = [
            "codex", "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
            "--output-schema", str(runner.SCHEMA), "--json", "--color", "never",
            "--output-last-message", str(path), "-C", str(Path(__file__).resolve().parent), "-",
        ]
        print(f"REPAIR {qid} {index}/{len(missing)}", flush=True)
        result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=1800)
        events_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        info: dict[str, Any] = {
            "question_id": qid,
            "sample_key": sample_key,
            "response_uid": sample_map[sample_key]["response_uid"],
            "return_code": result.returncode,
            "payload_sha256": sha(payload.encode("utf-8")),
            "prompt_sha256": sha(prompt.encode("utf-8")),
            "source_batch_payload_sha256": payload_hashes[qid],
            "output_file": str(path.relative_to(HERE)),
        }
        if result.returncode != 0 or not path.exists():
            info["status"] = "service_error_or_no_output"
        else:
            try:
                parsed = runner.parse_model_output(path)
                keys = [a.get("sample_key") for a in parsed.get("annotations", [])]
                if keys == [sample_key]:
                    info["status"] = "repaired"
                else:
                    info["status"] = "invalid_repair_output"
                    info["returned_sample_keys"] = keys
            except Exception as exc:
                info["status"] = f"parse_error:{type(exc).__name__}:{exc}"
        metadata.append(info)
        (HERE / "repair_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"REPAIR_RESULT {qid} {info['status']}", flush=True)
    return 0 if all(x["status"] == "repaired" for x in metadata) else 2


if __name__ == "__main__":
    raise SystemExit(main())

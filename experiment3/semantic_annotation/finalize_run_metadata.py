#!/usr/bin/env python3
"""Summarize local Codex batch events and raw output coverage for auditability."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_semantic_annotation.py"
SPEC = importlib.util.spec_from_file_location("semantic_runner", RUNNER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not import semantic runner")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def read_events(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"event_types": Counter()}
    if not path.exists():
        return result
    usage = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type", "unknown")
        result["event_types"][kind] += 1
        if kind == "thread.started":
            result["thread_id"] = event.get("thread_id")
        if kind == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    result["usage"] = usage
    result["event_types"] = dict(result["event_types"])
    return result


def main() -> int:
    batches, _, payload_hashes = runner.build_batches()
    model, effort = runner.configured_codex_model()
    results = {}
    totals = Counter()
    for index, qid in enumerate(runner.QUESTION_IDS, 1):
        output = HERE / "raw_batches" / f"{index:02d}_{qid}.json"
        events = read_events(HERE / "raw_batches" / f"{index:02d}_{qid}.events.jsonl")
        parsed = runner.parse_model_output(output) if output.exists() else {"annotations": []}
        returned = [x.get("sample_key") for x in parsed.get("annotations", [])]
        counts = Counter(returned)
        expected = set(batches[qid]["sample_keys"])
        actual = set(counts)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        duplicates = sorted(key for key, n in counts.items() if n > 1)
        usage = events.get("usage", {})
        for key, value in usage.items():
            if isinstance(value, (int, float)):
                totals[key] += value
        status = "complete"
        if missing:
            status = "partial_response_keys_repaired_separately" if qid == "F2" else "partial_response_keys"
        elif duplicates:
            status = "complete_unique_coverage_with_duplicate_output_rows"
        results[qid] = {
            "status": status,
            "model": model,
            "reasoning_effort": effort,
            "payload_sha256": payload_hashes[qid],
            "response_rows_returned": len(returned),
            "unique_response_keys_returned": len(actual),
            "duplicate_output_rows": sum(n - 1 for n in counts.values() if n > 1),
            "duplicate_sample_keys": duplicates,
            "missing_sample_keys": missing,
            "extra_sample_keys": extra,
            "claim_rows_returned_including_duplicates": sum(len(x.get("claim_annotations", [])) for x in parsed.get("annotations", [])),
            "thread_id": events.get("thread_id"),
            "token_usage": usage,
            "event_types": events.get("event_types", {}),
        }
    repairs = {}
    for name in ["repair_metadata.json", "quote_repair_metadata.json", "remaining_quote_repair_metadata.json"]:
        path = HERE / name
        if path.exists():
            repairs[name] = json.loads(path.read_text(encoding="utf-8"))
    repair_event_usage = {}
    for event_path in sorted((HERE / "raw_batches").glob("*repair*.events.jsonl")):
        event_result = read_events(event_path)
        usage = event_result.get("usage", {})
        repair_event_usage[event_path.name] = usage
        for key, value in usage.items():
            if isinstance(value, (int, float)):
                totals[key] += value
    output = {
        "service": "Codex/OpenAI via signed-in Codex CLI",
        "cli_version": "codex-cli 0.162.0-alpha.17.2",
        "annotator_model": model,
        "reasoning_effort": effort,
        "user_authorized_external_processing": True,
        "legacy_81_queue_and_study1_scores_used": False,
        "batch_count": len(results),
        "batches": results,
        "repair_runs": repairs,
        "repair_event_token_usage": repair_event_usage,
        "total_token_usage_reported_by_cli": dict(totals),
    }
    (HERE / "batch_run_metadata.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"batches": len(results), "model": model, "token_usage": dict(totals)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a linked audit and coding queue without modifying collected results."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


OUT = Path(__file__).resolve().parent
PROJECT = OUT.parent
STUDY2_RESULTS = PROJECT / "results"
STUDY1_RESULTS = PROJECT.parent.parent / "experiment1" / "results"
QUESTIONNAIRE_PATH = PROJECT / "followup_questionnaire.json"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    questionnaire = read_json(QUESTIONNAIRE_PATH, {"items": []})
    expected_by_question = {item["id"]: len(item.get("rounds", [])) for item in questionnaire["items"]}
    all_expected_turns = sum(expected_by_question.values())

    run_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    response_rows: list[dict[str, Any]] = []
    queue_rows: list[dict[str, Any]] = []

    for run_dir in sorted(p for p in STUDY2_RESULTS.iterdir() if p.is_dir()):
        answer_path = run_dir / "answer_set.json"
        if not answer_path.exists():
            continue
        answer_set = read_json(answer_path, {})
        run_info = read_json(run_dir / "run_info.json", {})
        coding_template = read_json(run_dir / "coding_template.json", {})
        provider = answer_set.get("provider") or run_info.get("provider")
        model = answer_set.get("model") or run_info.get("model")
        items = answer_set.get("items", {})
        observed_turns = sum(len(item.get("turns", [])) for item in items.values())
        actual_calls = run_info.get("actual_api_calls")
        collection_status = answer_set.get("status") or run_info.get("status")
        run_rows.append({
            "run_id": run_info.get("run_id") or run_dir.name,
            "run_directory": run_dir.name,
            "provider": provider,
            "model": model,
            "collection_status": collection_status,
            "planned_conversations": run_info.get("planned_conversations", 12),
            "planned_turns": run_info.get("planned_turns", all_expected_turns),
            "actual_api_calls": actual_calls,
            "observed_answer_turns": observed_turns,
            "coding_template_status": coding_template.get("status"),
            "failure": run_info.get("failure"),
            "evidence_snapshot_sha256": answer_set.get("evidence_file_sha256") or run_info.get("evidence_file_sha256"),
            "raw_answer_file": str(answer_path.relative_to(PROJECT)),
        })

        template_by_item = {entry.get("id"): entry for entry in coding_template.get("items", [])}
        for question_id in sorted(set(expected_by_question) | set(items)):
            answer_item = items.get(question_id, {})
            turns = answer_item.get("turns", [])
            template_item = template_by_item.get(question_id, {})
            template_turns = template_item.get("turn_annotations", [])
            template_by_response = {t.get("response_id"): t for t in template_turns if t.get("response_id")}
            coverage_rows.append({
                "run_id": run_info.get("run_id") or run_dir.name,
                "provider": provider,
                "model": model,
                "question_id": question_id,
                "expected_turns": expected_by_question.get(question_id, 0),
                "observed_turns": len(turns),
                "raw_answers_present": sum(bool(t.get("answer")) for t in turns),
                "template_turns": len(template_turns),
                "coding_status": template_item.get("coding_status", "no_template"),
                "coding_complete_turns": sum(bool(t.get("coding_complete")) for t in template_turns),
                "claim_units_filled": sum(len(t.get("units", [])) for t in template_turns),
            })

            for turn in turns:
                # Only completed runs enter the coding register. Partial/in-progress
                # API attempts stay visible in run_audit.csv for recovery decisions.
                if collection_status != "complete":
                    continue
                round_num = turn.get("round")
                response_id = turn.get("response_id")
                response_uid = f"{run_info.get('run_id') or run_dir.name}:{question_id}:R{int(round_num or 0):02d}"
                answer = turn.get("answer") or ""
                template_turn = template_by_response.get(response_id, {})
                metadata = template_turn.get("metadata", {})
                prompt = turn.get("prompt") or template_turn.get("prompt") or metadata.get("prompt_text") or ""
                generated = turn.get("called_at_utc") or metadata.get("generated_at")
                round_prompt = ""
                if question_id in expected_by_question and round_num:
                    q = next((item for item in questionnaire["items"] if item["id"] == question_id), None)
                    if q and int(round_num) <= len(q.get("rounds", [])):
                        round_prompt = q["rounds"][int(round_num) - 1]
                response_rows.append({
                    "response_uid": response_uid,
                    "run_id": run_info.get("run_id") or run_dir.name,
                    "provider": provider,
                    "model_requested": model,
                    "model_returned": turn.get("returned_model") or metadata.get("version"),
                    "question_id": question_id,
                    "dimension": answer_item.get("dimension"),
                    "round": round_num,
                    "conversation_id": answer_item.get("conversation_id"),
                    "response_id": response_id,
                    "generated_at_utc": generated,
                    "prompt_text": prompt,
                    "standardized_round_prompt": round_prompt,
                    "evidence_snapshot_sha256": answer_set.get("evidence_file_sha256") or run_info.get("evidence_file_sha256"),
                    "collection_status": collection_status,
                    "coding_status": "not_started" if not template_turn.get("coding_complete") else "present_in_legacy_template",
                    "raw_response": answer,
                })
                queue_rows.append({
                    "response_uid": response_uid,
                    "run_id": run_info.get("run_id") or run_dir.name,
                    "provider": provider,
                    "model_requested": model,
                    "model_returned": turn.get("returned_model") or metadata.get("version"),
                    "question_id": question_id,
                    "round": round_num,
                    "conversation_id": answer_item.get("conversation_id"),
                    "response_id": response_id,
                    "generated_at_utc": generated,
                    "prompt_text": prompt,
                    "evidence_snapshot_sha256": answer_set.get("evidence_file_sha256") or run_info.get("evidence_file_sha256"),
                    "coding_status": "not_started",
                    "coder_id": None,
                    "claim_annotations": [],
                    "response_level": {
                        "question_coverage": None,
                        "required_points_addressed": [],
                        "material_omissions": [],
                        "C_A_excessive_hedging": None,
                        "C_B_material_omission": None,
                        "C_C_unsupported_overconfidence": None,
                        "frame_codes": [],
                        "coder_memo": None,
                    },
                    "adjudication": {"status": "not_started", "notes": None},
                })

    write_csv(OUT / "run_audit.csv", run_rows, [
        "run_id", "run_directory", "provider", "model", "collection_status", "planned_conversations",
        "planned_turns", "actual_api_calls", "observed_answer_turns", "coding_template_status",
        "failure", "evidence_snapshot_sha256", "raw_answer_file",
    ])
    write_csv(OUT / "question_coverage.csv", coverage_rows, [
        "run_id", "provider", "model", "question_id", "expected_turns", "observed_turns",
        "raw_answers_present", "template_turns", "coding_status", "coding_complete_turns", "claim_units_filled",
    ])
    write_csv(OUT / "response_register.csv", response_rows, [
        "response_uid", "run_id", "provider", "model_requested", "model_returned", "question_id", "dimension",
        "round", "conversation_id", "response_id", "generated_at_utc", "prompt_text", "standardized_round_prompt",
        "evidence_snapshot_sha256", "collection_status", "coding_status", "raw_response",
    ])
    with (OUT / "coding_queue.jsonl").open("w", encoding="utf-8") as handle:
        for row in queue_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    study1_rows: list[dict[str, Any]] = []
    if STUDY1_RESULTS.exists():
        for run_dir in sorted(p for p in STUDY1_RESULTS.iterdir() if p.is_dir()):
            info = read_json(run_dir / "run_info.json")
            if info is None:
                continue
            config = info.get("config", {})
            providers = config.get("providers", [])
            score_file = run_dir / "scores_long.csv"
            score_rows = 0
            actual_providers: set[str] = set()
            actual_models: set[str] = set()
            returned_models: set[str] = set()
            question_ids: set[str] = set()
            if score_file.exists():
                with score_file.open(encoding="utf-8-sig", newline="") as handle:
                    score_records = list(csv.DictReader(handle))
                    score_rows = len(score_records)
                    actual_providers = {row.get("provider", "") for row in score_records if row.get("provider")}
                    actual_models = {row.get("requested_model", "") for row in score_records if row.get("requested_model")}
                    returned_models = {row.get("returned_model", "") for row in score_records if row.get("returned_model")}
                    question_ids = {row.get("question_id", "") for row in score_records if row.get("question_id")}
            provider_names = "; ".join(p.get("name", p.get("id", "")) for p in providers)
            model_names = "; ".join(p.get("model", "") for p in providers if p.get("model"))
            study1_rows.append({
                "run_directory": run_dir.name,
                "status": info.get("status"),
                "dry_run": info.get("dry_run"),
                "actual_http_requests": info.get("actual_http_requests"),
                "valid_questionnaires": info.get("valid_questionnaires"),
                "score_rows": score_rows,
                "actual_provider": "; ".join(sorted(actual_providers)),
                "actual_model": "; ".join(sorted(actual_models)),
                "returned_model": "; ".join(sorted(returned_models)),
                "question_count": len(question_ids),
                "question_ids": "; ".join(sorted(question_ids)),
                "provider_config_for_run": provider_names,
                "model_config_for_run": model_names,
                "prompt_sha256": info.get("prompt_sha256"),
                "condition_field_present": "condition" in info or "condition" in config,
                "raw_output_file": str((run_dir / "raw_responses.jsonl").relative_to(STUDY1_RESULTS.parent.parent)) if (run_dir / "raw_responses.jsonl").exists() else "",
            })
    write_csv(OUT / "study1_run_audit.csv", study1_rows, [
        "run_directory", "status", "dry_run", "actual_http_requests", "valid_questionnaires", "score_rows",
        "actual_provider", "actual_model", "returned_model", "question_count", "question_ids",
        "provider_config_for_run", "model_config_for_run", "prompt_sha256", "condition_field_present", "raw_output_file",
    ])

    complete_runs = [r for r in run_rows if r.get("collection_status") == "complete"]
    in_progress_runs = [r for r in run_rows if r.get("collection_status") == "in_progress"]
    failed_or_incomplete_runs = [r for r in run_rows if r.get("collection_status") not in {"complete", "in_progress"}]
    coded_rows = sum(int(row["coding_complete_turns"]) for row in coverage_rows)
    summary = {
        "study2": {
            "total_runs": len(run_rows),
            "complete_runs": len(complete_runs),
            "in_progress_runs": len(in_progress_runs),
            "failed_or_incomplete_runs": len(failed_or_incomplete_runs),
            "in_progress_run_ids": [r["run_id"] for r in in_progress_runs],
            "failed_or_incomplete_run_ids": [r["run_id"] for r in failed_or_incomplete_runs],
            "complete_run_ids": [r["run_id"] for r in complete_runs],
            "complete_answer_turns": sum(int(r["observed_answer_turns"]) for r in complete_runs),
            "coding_queue_rows": len(queue_rows),
            "coding_complete_turns_in_existing_templates": coded_rows,
            "independence_note": "Turns within a question's conversation share context and are nested observations.",
        },
        "study1": {
            "runs": len(study1_rows),
            "complete_runs": sum(row.get("status") == "complete" for row in study1_rows),
            "complete_score_rows": sum(int(row.get("score_rows") or 0) for row in study1_rows if row.get("status") == "complete"),
            "paired_case_condition_in_run_info": any(row.get("condition_field_present") for row in study1_rows),
        },
        "validation": {
            "expected_turns_per_complete_study2_run": all_expected_turns,
            "complete_runs_have_expected_turns": all(int(r["observed_answer_turns"]) == all_expected_turns for r in complete_runs),
            "response_uids_unique": len({row["response_uid"] for row in response_rows}) == len(response_rows),
            "raw_answers_preserved": all(bool(row["raw_response"]) for row in response_rows),
            "annotation_fields_are_empty_pending_coding": all(not row["claim_annotations"] and row["coding_status"] == "not_started" for row in queue_rows),
        },
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build a de-identified response register from completed F/N/R/C run folders."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parent / "pure_machine_v1" / "response_register.csv"
QUESTION_IDS = {f"{family}{number}" for family in "FNRC" for number in range(1, 4)}
FIELDS = [
    "response_uid", "run_id", "provider", "model", "returned_model", "question_id",
    "dimension", "round", "conversation_id", "response_id", "generated_at_utc",
    "prompt_text", "evidence_snapshot_sha256", "collection_status", "answer_sha256",
    "answer_characters", "raw_response",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def collect_run(run_dir: Path) -> list[dict[str, Any]]:
    info_path = run_dir / "run_info.json"
    raw_path = run_dir / "raw_responses.jsonl"
    if not info_path.is_file() or not raw_path.is_file():
        raise ValueError(f"{run_dir}: expected run_info.json and raw_responses.jsonl")
    info = read_json(info_path)
    if info.get("status") != "complete":
        raise ValueError(f"{run_dir}: run is not complete (status={info.get('status')!r})")

    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    valid = [row for row in raw_rows if row.get("status") == "valid" and isinstance(row.get("answer"), str) and row["answer"].strip()]
    if len(valid) != 27:
        raise ValueError(f"{run_dir}: expected 27 valid F/N/R/C turns, found {len(valid)}")

    rows = []
    seen_turns: set[tuple[str, int]] = set()
    run_id = str(info.get("run_id") or run_dir.name)
    for row in valid:
        qid = str(row.get("item_id") or "")
        if qid not in QUESTION_IDS:
            raise ValueError(f"{run_dir}: unexpected question_id {qid!r}")
        conversation_id = str(row.get("conversation_id") or "")
        round_no = int(row.get("round") or 0)
        if not conversation_id or round_no < 1:
            raise ValueError(f"{run_dir}: missing conversation ID or round for {qid}")
        turn_key = (qid, round_no)
        if turn_key in seen_turns:
            raise ValueError(f"{run_dir}: duplicate turn {qid} round {round_no}")
        seen_turns.add(turn_key)
        answer = str(row["answer"])
        uid = f"{run_id}:{qid}:r{round_no}"
        rows.append({
            "response_uid": uid,
            "run_id": run_id,
            "provider": row.get("provider") or info.get("provider", ""),
            "model": row.get("model") or info.get("model", ""),
            "returned_model": row.get("returned_model") or "",
            "question_id": qid,
            "dimension": row.get("dimension") or "",
            "round": round_no,
            "conversation_id": conversation_id,
            "response_id": row.get("response_id") or "",
            "generated_at_utc": row.get("called_at_utc") or "",
            "prompt_text": row.get("prompt") or "",
            "evidence_snapshot_sha256": info.get("evidence_file_sha256") or "",
            "collection_status": "valid",
            "answer_sha256": sha256(answer),
            "answer_characters": len(answer),
            "raw_response": answer,
        })
    present_questions = {row["question_id"] for row in rows}
    if present_questions != QUESTION_IDS:
        missing = sorted(QUESTION_IDS - present_questions)
        extra = sorted(present_questions - QUESTION_IDS)
        raise ValueError(f"{run_dir}: question coverage mismatch; missing={missing}, extra={extra}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", action="append", required=True, type=Path,
        help="Completed F/N/R/C run folder; repeat this option for each model run.",
    )
    args = parser.parse_args()
    all_rows: list[dict[str, Any]] = []
    seen_uids: set[str] = set()
    try:
        for supplied in args.run_dir:
            run_dir = supplied.expanduser().resolve()
            rows = collect_run(run_dir)
            for row in rows:
                if row["response_uid"] in seen_uids:
                    raise ValueError(f"Duplicate response_uid: {row['response_uid']}")
                seen_uids.add(row["response_uid"])
            all_rows.extend(rows)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"无法生成登记表：{exc}", file=sys.stderr)
        return 2

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".csv.tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    temp.replace(OUTPUT)
    print(f"已登记 {len(all_rows)} 条有效回答，来自 {len(args.run_dir)} 个模型运行。")
    print(f"输出：{OUTPUT}")
    print("注意：登记表含完整原始回答；确认本地存储与后续语义标注的数据处理范围。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

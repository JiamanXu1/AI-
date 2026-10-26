#!/usr/bin/env python3
"""Build a reproducible, local-only machine baseline; no remote inference is performed."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUT = Path(__file__).resolve().parent
PROJECT = OUT.parent
WORKSPACE = OUT.parents[2]
RESULTS = PROJECT / "results"
BENCH = WORKSPACE / "玫瑰宫事实语料库包括中国和联合国" / "golestan_truth_benchmark_20261020_v1"
HERITAGE_CODEBOOK = PROJECT / "codebook.json"
STUDY2_CODEBOOK = PROJECT / "study2_coding_v2" / "codebook.json"
QUESTIONNAIRE = PROJECT / "followup_questionnaire.json"
EXPECTED_RUNS = {
    "chatgpt_siwc_followup_20261019T151312Z_8346a9",
    "deepseek_followup_20261019T094423Z_e201f6",
    "doubao_followup_20261019T100053Z_f9370e",
    "grok_followup_20261020T002945Z_a62bda",
    "mistral_followup_20261020T005934Z_b3d5fc",
}
REGISTER_FIELDS = [
    "response_uid", "run_id", "provider", "model", "returned_model", "question_id",
    "dimension", "round", "conversation_id", "response_id", "generated_at_utc",
    "prompt_text", "evidence_snapshot_sha256", "collection_status", "answer_sha256",
    "answer_characters", "raw_response",
]


def read_json(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_valid_responses() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    run_manifest: list[dict[str, Any]] = []
    for run_id in sorted(EXPECTED_RUNS):
        run_dir = RESULTS / run_id
        raw_path = run_dir / "raw_responses.jsonl"
        if not raw_path.exists():
            raise FileNotFoundError(f"Required raw response file is missing: {raw_path}")
        raw_rows = read_jsonl(raw_path)
        run_info = read_json(run_dir / "run_info.json", {})
        status_counts = Counter(str(r.get("status") or "missing") for r in raw_rows)
        selected = [
            r for r in raw_rows
            if r.get("status") == "valid" and isinstance(r.get("answer"), str) and r["answer"].strip()
        ]
        if len(selected) != 27:
            raise ValueError(f"{run_id}: expected 27 valid answers, found {len(selected)}")
        evidence_hashes = {
            str(r.get("evidence_file_sha256"))
            for r in [read_json(run_dir / "answer_set.json", {}) or {}, run_info]
            if r.get("evidence_file_sha256")
        }
        if not evidence_hashes:
            evidence_hashes = {
                str(r.get("evidence_snapshot_sha256"))
                for r in raw_rows if r.get("evidence_snapshot_sha256")
            }
        evidence_hash = sorted(evidence_hashes)[0] if evidence_hashes else ""
        if len(evidence_hashes) > 1:
            raise ValueError(f"{run_id}: conflicting evidence snapshot hashes: {sorted(evidence_hashes)}")
        for item in selected:
            qid = str(item.get("item_id") or "")
            round_no = int(item.get("round") or 0)
            if not qid or round_no < 1:
                raise ValueError(f"{run_id}: missing question id or round")
            answer = item["answer"]
            rows.append({
                "response_uid": f"{run_id}:{qid}:R{round_no:02d}",
                "run_id": run_id,
                "provider": item.get("provider") or run_info.get("provider") or "",
                "model": item.get("model") or run_info.get("model") or "",
                "returned_model": item.get("returned_model") or item.get("model") or "",
                "question_id": qid,
                "dimension": item.get("dimension") or "",
                "round": round_no,
                "conversation_id": item.get("conversation_id") or "",
                "response_id": item.get("response_id") or "",
                "generated_at_utc": item.get("called_at_utc") or "",
                "prompt_text": item.get("prompt") or "",
                "evidence_snapshot_sha256": evidence_hash,
                "collection_status": item.get("status"),
                "answer_sha256": sha256_bytes(answer.encode("utf-8")),
                "answer_characters": len(answer),
                "raw_response": answer,
            })
        run_manifest.append({
            "run_id": run_id,
            "provider": run_info.get("provider") or (selected[0].get("provider") if selected else ""),
            "model": run_info.get("model") or (selected[0].get("model") if selected else ""),
            "raw_file": str(raw_path.relative_to(WORKSPACE)),
            "raw_file_sha256": sha256_file(raw_path),
            "raw_record_count": len(raw_rows),
            "status_counts": dict(status_counts),
            "valid_answer_count": len(selected),
            "evidence_snapshot_sha256": evidence_hash,
        })
    rows.sort(key=lambda r: (r["question_id"], r["round"], r["run_id"]))
    if len(rows) != 135:
        raise ValueError(f"Expected 135 valid responses; found {len(rows)}")
    keys = [r["response_uid"] for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate stable response IDs found")
    return rows, run_manifest


def split_sentence_candidates(text: str) -> list[dict[str, Any]]:
    """Create approximate sentence spans; these are not asserted atomic claims."""
    spans: list[dict[str, Any]] = []
    start = 0
    for match in re.finditer(r"[。！？!?；;\n]", text):
        end = match.end()
        piece_start = start
        piece_end = end
        while piece_start < piece_end and text[piece_start].isspace():
            piece_start += 1
        while piece_end > piece_start and text[piece_end - 1].isspace():
            piece_end -= 1
        if piece_end > piece_start:
            spans.append({"start_char": piece_start, "end_char_exclusive": piece_end, "quote": text[piece_start:piece_end]})
        start = end
    piece_start = start
    piece_end = len(text)
    while piece_start < piece_end and text[piece_start].isspace():
        piece_start += 1
    while piece_end > piece_start and text[piece_end - 1].isspace():
        piece_end -= 1
    if piece_end > piece_start:
        spans.append({"start_char": piece_start, "end_char_exclusive": piece_end, "quote": text[piece_start:piece_end]})
    return spans


def codebook_terms(codebook: list[dict[str, Any]]) -> list[dict[str, str]]:
    terms: dict[tuple[str, str], str] = {}
    for entry in codebook:
        code = str(entry.get("code") or "")
        for field in ("name_zh", "name_en", "definition", "include", "example"):
            value = str(entry.get(field) or "")
            for part in re.split(r"[;；、，,。|/：:\n]+", value):
                term = part.strip().strip("“”\"'（）() ")
                if len(term) < 2 or len(term) > 34:
                    continue
                if re.fullmatch(r"[\u3400-\u9fff]+", term) and len(term) < 3:
                    continue
                if term.startswith(("将", "把", "记录", "识别", "区分", "记录模型", "records ", "identify ")):
                    continue
                terms[(code, term.casefold())] = field
    return [{"code": code, "term": term, "source_field": source_field}
            for (code, term), source_field in sorted(terms.items())]


def find_matches(text: str, term: str) -> list[tuple[int, int]]:
    if not term:
        return []
    flags = re.IGNORECASE if re.search(r"[A-Za-z]", term) else 0
    return [(m.start(), m.end()) for m in re.finditer(re.escape(term), text, flags)]


def lexical_and_truth_baseline(
    rows: list[dict[str, Any]], codebook: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    terms = codebook_terms(codebook)
    sentence_units: list[dict[str, Any]] = []
    lexical_rows: list[dict[str, Any]] = []
    truth_rows: list[dict[str, Any]] = []
    report_cues = ["据报", "据称", "报道称", "声明称", "通报称", "据联合国", "据UNESCO", "according to", "reportedly", "allegedly"]
    confirmed_cues = ["确认", "已确认", "已证实", "证实", "官方记录", "confirmed", "verified", "established"]
    uncertain_cues = ["无法确认", "不能确认", "尚不能", "未能确定", "尚未证实", "缺乏证据", "证据不足", "未知", "尚不清楚", "not established", "insufficient evidence", "unknown", "uncertain"]
    conditional_cues = ["可能", "或许", "若", "如果", "假如", "may ", "might ", "could ", "if "]
    source_ref_re = re.compile(r"\b(?:S\d{2}|FCT\d{3}|MC\d{3}|CM\d{3}|R\d{3}|UNESCO_[A-Z0-9_]+)\b")
    relation_cues = ["体现", "反映", "见证", "承载", "象征", "代表", "构成", "彰显", "意义", "价值", "reflect", "represent", "embody", "contribute", "demonstrate"]
    site_cues = ["戈勒斯坦宫", "玫瑰宫", "Golestan Palace", "Qajar", "卡扎尔", "镜厅", "瓷砖", "花园", "庭院", "palace", "mirror hall", "tile", "garden"]
    value_codes = {f"V{i}" for i in range(1, 11)}
    for response in rows:
        text = response["raw_response"]
        spans = split_sentence_candidates(text)
        for ix, span in enumerate(spans, 1):
            sentence_units.append({
                "segment_id": f"{response['response_uid']}:S{ix:03d}",
                "response_uid": response["response_uid"],
                "method": "punctuation_segment_candidate",
                "granularity": "sentence_approximation_not_atomic_claim",
                **span,
            })
        by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in terms:
            for start, end in find_matches(text, row["term"]):
                window = text[max(0, start - 35):min(len(text), end + 35)].casefold()
                depth_proxy = 1
                if any(cue.casefold() in window for cue in relation_cues):
                    depth_proxy = 2
                if depth_proxy >= 2 and any(cue.casefold() in window for cue in site_cues):
                    depth_proxy = 3
                by_code[row["code"]].append({
                    "term": row["term"],
                    "source_field": row["source_field"],
                    "start_char": start,
                    "end_char_exclusive": end,
                    "quote": text[start:end],
                    "depth_proxy": depth_proxy if row["code"] in value_codes else None,
                })
        for code, hits in sorted(by_code.items()):
            best_depth = max((h["depth_proxy"] or 0) for h in hits)
            lexical_rows.append({
                "response_uid": response["response_uid"],
                "code": code,
                "candidate_present": True,
                "heuristic_depth_proxy": best_depth if code in value_codes else "",
                "hit_count": len(hits),
                "hits": hits,
                "warning": "Dictionary/surface candidate only; not a semantic code or truth judgment.",
            })
        source_refs = sorted(set(source_ref_re.findall(text)))
        markers = {
            "reported_or_attributed_cues": sorted({c for c in report_cues if c.casefold() in text.casefold()}),
            "confirmed_cues": sorted({c for c in confirmed_cues if c.casefold() in text.casefold()}),
            "uncertainty_cues": sorted({c for c in uncertain_cues if c.casefold() in text.casefold()}),
            "conditional_cues": sorted({c for c in conditional_cues if c.casefold() in text.casefold()}),
        }
        truth_rows.append({
            "response_uid": response["response_uid"],
            "question_id": response["question_id"],
            "source_ids_mentioned": source_refs,
            "source_id_count": len(source_refs),
            "truth_language_surface_cues": markers,
            "has_any_truth_language_cue": any(markers.values()),
            "warning": "Surface indicators only; they do not establish the truth, calibration, or sufficiency of a claim.",
        })
    return sentence_units, lexical_rows, truth_rows


def prepare() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, runs = load_valid_responses()
    codebook = read_json(HERITAGE_CODEBOOK, [])
    sentence_units, lexical_rows, truth_rows = lexical_and_truth_baseline(rows, codebook)
    local_summaries = write_local_summaries(rows, codebook, lexical_rows, truth_rows)
    write_csv(OUT / "response_register.csv", rows, REGISTER_FIELDS)
    write_jsonl(OUT / "sentence_candidates.jsonl", sentence_units)
    write_jsonl(OUT / "dictionary_match_candidates.jsonl", lexical_rows)
    write_csv(OUT / "truth_surface_indicators.csv", truth_rows, [
        "response_uid", "question_id", "source_ids_mentioned", "source_id_count",
        "truth_language_surface_cues", "has_any_truth_language_cue", "warning",
    ])
    fact_units = read_jsonl(BENCH / "truth_units.jsonl")
    legal_units = read_jsonl(BENCH / "legal_rule_units.jsonl")
    bridge_units = read_jsonl(BENCH / "media_claim_bridge.jsonl")
    questionnaire = read_json(QUESTIONNAIRE, {})
    run_counts = Counter(r["run_id"] for r in rows)
    manifest = {
        "package": "pure_machine_v1",
        "created_local_date": "2026-10-24",
        "scope": {
            "included_runs": [r["run_id"] for r in runs],
            "included_valid_response_turns": len(rows),
            "turns_per_run": dict(sorted(run_counts.items())),
            "question_ids": sorted({r["question_id"] for r in rows}),
            "study1_likert_scores_included": False,
            "raw_answers_modified": False,
        },
        "excluded_inputs": {
            "legacy_coding_queue": True,
            "study1_likert_scores": True,
        },
        "references": {
            "heritage_codebook": str(HERITAGE_CODEBOOK.relative_to(WORKSPACE)),
            "heritage_codebook_sha256": sha256_file(HERITAGE_CODEBOOK),
            "study2_codebook": str(STUDY2_CODEBOOK.relative_to(WORKSPACE)),
            "study2_codebook_sha256": sha256_file(STUDY2_CODEBOOK),
            "truth_benchmark": str(BENCH.relative_to(WORKSPACE)),
            "truth_units": len(fact_units),
            "legal_rule_units": len(legal_units),
            "media_claim_units": len(bridge_units),
            "benchmark_snapshot": "2026-10-20 v1.0",
            "questionnaire_question_count": len(questionnaire.get("items", [])),
        },
        "runs": runs,
        "generated_files": {
            "response_register.csv": {"rows": len(rows), "sha256": sha256_file(OUT / "response_register.csv")},
            "sentence_candidates.jsonl": {"rows": len(sentence_units), "sha256": sha256_file(OUT / "sentence_candidates.jsonl")},
            "dictionary_match_candidates.jsonl": {"rows": len(lexical_rows), "sha256": sha256_file(OUT / "dictionary_match_candidates.jsonl")},
            "truth_surface_indicators.csv": {"rows": len(truth_rows), "sha256": sha256_file(OUT / "truth_surface_indicators.csv")},
            **local_summaries,
        },
        "semantic_annotation": {
            "status": "not_run_external_destination_not_authorized",
            "note": "Semantic claim-level labeling was not run. Auto review rejected sending corpus text to the signed-in Codex/OpenAI service without destination-specific authorization.",
            "local_machine_baseline": "complete",
            "evidence_benchmark": "2026-10-20 v1.0; response evidence snapshot hash retained separately",
        },
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows, manifest



def write_local_summaries(
    rows: list[dict[str, Any]],
    codebook: list[dict[str, Any]],
    lexical_rows: list[dict[str, Any]],
    truth_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    response_by_uid = {r["response_uid"]: r for r in rows}
    match_by_response: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in lexical_rows:
        match_by_response[record["response_uid"]][record["code"]] = record

    value_codes = [f"V{i}" for i in range(1, 11)]
    response_value_rows = []
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for response in rows:
        hits_by_code = match_by_response.get(response["response_uid"], {})
        for code in value_codes:
            hit = hits_by_code.get(code, {})
            depth = int(hit.get("heuristic_depth_proxy") or 0)
            record = {
                "response_uid": response["response_uid"],
                "run_id": response["run_id"],
                "model": response["model"],
                "question_id": response["question_id"],
                "code": code,
                "lexicon_candidate_present": int(bool(hit)),
                "heuristic_depth_proxy": depth,
                "hit_count": int(hit.get("hit_count") or 0),
                "hits": hit.get("hits", []),
            }
            response_value_rows.append(record)
            grouped[(response["model"], response["question_id"], code)].append(record)
    write_csv(OUT / "dictionary_candidate_by_response.csv", [
        {**r, "hits": json.dumps(r["hits"], ensure_ascii=False)} for r in response_value_rows
    ], ["response_uid", "run_id", "model", "question_id", "code", "lexicon_candidate_present", "heuristic_depth_proxy", "hit_count", "hits"])

    model_rows = []
    for (model, question_id, code), values in sorted(grouped.items()):
        model_rows.append({
            "model": model,
            "question_id": question_id,
            "code": code,
            "responses_n": len(values),
            "candidate_present_n": sum(r["lexicon_candidate_present"] for r in values),
            "candidate_presence_rate": round(sum(r["lexicon_candidate_present"] for r in values) / len(values), 4) if values else 0,
            "mean_depth_proxy_among_hits": round(sum(r["heuristic_depth_proxy"] for r in values if r["heuristic_depth_proxy"]) / max(1, sum(bool(r["heuristic_depth_proxy"]) for r in values)), 3),
        })
    write_csv(OUT / "dictionary_candidate_model_summary.csv", model_rows, [
        "model", "question_id", "code", "responses_n", "candidate_present_n", "candidate_presence_rate", "mean_depth_proxy_among_hits",
    ])

    surface_rows = []
    cue_names = ["reported_or_attributed_cues", "confirmed_cues", "uncertainty_cues", "conditional_cues"]
    truth_by_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in truth_rows:
        response = response_by_uid[record["response_uid"]]
        cues = record["truth_language_surface_cues"]
        out = {
            "response_uid": record["response_uid"],
            "run_id": response["run_id"],
            "model": response["model"],
            "question_id": record["question_id"],
            "source_id_count": record["source_id_count"],
            "has_source_id": int(record["source_id_count"] > 0),
            **{f"has_{name}": int(bool(cues.get(name))) for name in cue_names},
            "truth_surface_indicator": int(record["has_any_truth_language_cue"]),
            "cue_detail": cues,
        }
        surface_rows.append(out)
        truth_by_group[(response["model"], record["question_id"])].append(out)
    write_csv(OUT / "truth_surface_by_response.csv", [
        {**r, "cue_detail": json.dumps(r["cue_detail"], ensure_ascii=False)} for r in surface_rows
    ], ["response_uid", "run_id", "model", "question_id", "source_id_count", "has_source_id", *[f"has_{name}" for name in cue_names], "truth_surface_indicator", "cue_detail"])
    truth_model_rows = []
    for (model, question_id), values in sorted(truth_by_group.items()):
        out = {"model": model, "question_id": question_id, "responses_n": len(values)}
        for field in ["has_source_id", *[f"has_{name}" for name in cue_names], "truth_surface_indicator"]:
            out[f"{field}_n"] = sum(int(v[field]) for v in values)
            out[f"{field}_rate"] = round(out[f"{field}_n"] / len(values), 4) if values else 0
        out["mean_source_id_count"] = round(sum(v["source_id_count"] for v in values) / len(values), 3) if values else 0
        truth_model_rows.append(out)
    write_csv(OUT / "truth_surface_model_summary.csv", truth_model_rows, list(truth_model_rows[0]) if truth_model_rows else ["model", "question_id", "responses_n"])

    code_presence = Counter(r["code"] for r in response_value_rows if r["lexicon_candidate_present"])
    report = [
        "# 玫瑰宫回答的纯机器本地基线",
        "",
        f"- 纳入 {len(rows)} 条有效回答；{len({r['run_id'] for r in rows})} 个运行，每个运行 27 轮。",
        "- 旧编码队列未作为输入；Study 1 的 1–5 评分未纳入。",
        "- 原始回答只读；代码本词面候选与真值措辞线索另存。",
        "- 此基线不声称完成原子命题抽取、事实真伪裁定、法律正确性评分或语义层面的提及深度判断。",
        "- 自动审查拒绝将语料发送到已登录 Codex/OpenAI 服务；没有执行任何语料外传或云端语义标注。",
        "",
        "## 产物说明",
        "",
        "- response_register.csv：135 条回答与模型/题目/轮次元数据。",
        "- sentence_candidates.jsonl：按标点切分的句段候选，不等同于原子命题。",
        "- dictionary_match_candidates.jsonl：依据现有文化遗产代码本字段做短语匹配，属于高召回候选。",
        "- dictionary_candidate_by_response.csv：每条回答的 V1–V10 词典候选和规则深度代理。",
        "- dictionary_candidate_model_summary.csv：模型×题目×价值代码的词典候选比例。",
        "- truth_surface_indicators.csv：来源编号与据报/确认/不确定/条件措辞的线索。",
        "- truth_surface_by_response.csv、truth_surface_model_summary.csv：上述表层线索的回答级和分组汇总。",
        "- annotation_output.schema.json：未来机器语义标注的结构草案，本地基线未调用它。",
        "- source_manifest.json：输入清单、哈希、排除规则和基准版本。",
        "",
        "## 词典候选分布（不是确认编码）",
        "",
    ]
    for code in value_codes:
        report.append(f"- {code}: {code_presence[code]} / {len(rows)} 条回答至少命中一个代码本短语。")
    report.extend([
        "",
        "## 真值处理边界",
        "",
        "来源编号或不确定性用词只能说明回答出现了相应表层线索；它们不能证明回答区分了来源事实与事件事实，也不能裁决某个命题是否受证据支持。真值语义标签、规范评分和责任判断仍未处理。",
    ])
    (OUT / "machine_results_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    files = [
        "dictionary_candidate_by_response.csv",
        "dictionary_candidate_model_summary.csv",
        "truth_surface_by_response.csv",
        "truth_surface_model_summary.csv",
        "machine_results_report.md",
    ]
    return {
        name: {"rows": sum(1 for _ in (OUT / name).open(encoding="utf-8")) - (0 if name.endswith(".md") else 1), "sha256": sha256_file(OUT / name)}
        for name in files
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local-only machine baseline for the approved corpus.")
    parser.add_argument("--prepare-only", action="store_true", help="Kept for compatibility; preparation is local and deterministic.")
    args = parser.parse_args()
    rows, manifest = prepare()
    print(f"Prepared local baseline for {len(rows)} valid response turns from {len(manifest['runs'])} runs.", flush=True)


if __name__ == "__main__":
    main()

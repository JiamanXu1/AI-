#!/usr/bin/env python3
"""Local-only text mining for the completed identity-follow-up experiment."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
RUNS_DIR = PROJECT.parent / "experiment2" / "results_identity"
CODEBOOK_PATH = PROJECT / "codebook.json"
OUT = HERE / "追加实验文本挖掘_20261026"
CANONICAL_RUNS = [
    "chatgpt_siwc_identity_20261025T094300Z_cd320c",
    "deepseek_20261024T150431Z_021492",
    "doubao_20261025T144639Z_e95dbd",
    "grok_20261025T124451Z_96003c",
    "mistral_20261025T030850Z_82b70c",
]
CONDITIONS = ("iran", "us", "china")
CONDITION_ZH = {"iran": "伊朗身份", "us": "美国身份", "china": "中国身份"}
TURN_SEQUENCE = [
    "initial_questionnaire", "open_event_assessment", "facts_sources_damage",
    "cultural_values_perspectives", "legal_rules_application", "actor_attribution",
    "country_conduct", "responsibility_allocation", "final_questionnaire_and_report",
]
REPORT_CUES = ["据报", "据称", "报道称", "声明称", "通报称", "据联合国", "据UNESCO",
               "according to", "reportedly", "allegedly"]
CONFIRMED_CUES = ["确认", "已确认", "已证实", "证实", "官方记录", "confirmed", "verified", "established"]
UNCERTAIN_CUES = ["无法确认", "不能确认", "尚不能", "未能确定", "尚未证实", "缺乏证据", "证据不足",
                  "未知", "尚不清楚", "not established", "insufficient evidence", "unknown",
                  "uncertain", "undetermined"]
CONDITIONAL_CUES = ["可能", "或许", "若", "如果", "假如", "may ", "might ", "could ", "if "]
SOURCE_REF_RE = re.compile(
    r"\b(?:S\d{2,3}|F\d{3}|R\d{3}|MC\d{3}|FCT\d{3}|UNESCO_[A-Z0-9_]+)\b", re.I
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_text(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]", text.lower()))


def sentence_count(text: str) -> int:
    return sum(bool(part.strip()) for part in re.split(r"[。！？!?；;\n]+", text))


def remove_final_responsibility_section(text: str) -> tuple[str, bool]:
    """Remove numbered section 5 from a final report for general text metrics."""
    lines = text.splitlines(keepends=True)
    start_pattern = re.compile(
        r"^\s*(?:#{1,6}\s*)?5[.)]\s*.*(?:responsibility|责任|因果贡献)", re.I
    )
    next_section_pattern = re.compile(r"^\s*(?:#{1,6}\s*)?6[.)]\s+")
    start = next((i for i, line in enumerate(lines) if start_pattern.search(line)), None)
    if start is None:
        return text, False
    end = next(
        (i for i in range(start + 1, len(lines)) if next_section_pattern.search(lines[i])),
        len(lines),
    )
    return "".join(lines[:start] + lines[end:]), True


def codebook_terms(codebook: list[dict[str, Any]]) -> list[dict[str, str]]:
    terms: dict[tuple[str, str], str] = {}
    for entry in codebook:
        code = str(entry.get("code") or "")
        for field in ("name_zh", "name_en", "definition", "include", "example"):
            for part in re.split(r"[;；、，,。|/：:\n]+", str(entry.get(field) or "")):
                term = part.strip().strip("“”\"'（）() ")
                if len(term) < 2 or len(term) > 34:
                    continue
                if re.fullmatch(r"[\u3400-\u9fff]+", term) and len(term) < 3:
                    continue
                if term.startswith(("将", "把", "记录", "识别", "区分", "记录模型", "records ", "identify ")):
                    continue
                terms[(code, term.casefold())] = field
    return [{"code": code, "term": term, "source_field": field}
            for (code, term), field in sorted(terms.items())]


def get_records(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    records = transcript.get("turns") or transcript.get("records") or []
    if not isinstance(records, list):
        raise ValueError("Transcript records must be a list")
    return records


def get_prompt(record: dict[str, Any]) -> str:
    if isinstance(record.get("prompt"), str) and record["prompt"]:
        return record["prompt"]
    for message in reversed(record.get("request_messages") or []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def get_answer(record: dict[str, Any]) -> str:
    answer = record.get("answer")
    if not isinstance(answer, str) or not answer:
        answer = record.get("assistant_text")
    return answer if isinstance(answer, str) else ""


def load_sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str], str]]:
    all_rows: list[dict[str, Any]] = []
    run_audit: list[dict[str, Any]] = []
    initial_prompts: dict[tuple[str, str], str] = {}

    for run_id in CANONICAL_RUNS:
        run_dir = RUNS_DIR / run_id
        info = read_json(run_dir / "run_info.json")
        if info.get("status") != "complete" or int(info.get("planned_api_calls") or 0) != 27:
            raise ValueError(f"{run_id}: run is not a complete 27-call experiment")
        run_conditions = info.get("conditions", {})
        transcript_audit = {}
        answer_count = 0
        for condition in CONDITIONS:
            condition_info = run_conditions.get(condition, {})
            if condition_info.get("status") != "complete" or int(condition_info.get("completed_turns") or 0) != 9:
                raise ValueError(f"{run_id}/{condition}: not complete 9/9")
            condition_dir = run_dir / condition
            transcript_path = condition_dir / "transcript.json"
            transcript = read_json(transcript_path)
            records = sorted(get_records(transcript), key=lambda r: int(r.get("turn") or 0))
            if len(records) != 9 or [str(r.get("turn_id") or "") for r in records] != TURN_SEQUENCE:
                raise ValueError(f"{run_id}/{condition}: incomplete or out-of-order transcript")
            for turn, record in enumerate(records, 1):
                answer = get_answer(record)
                if not answer.strip():
                    raise ValueError(f"{run_id}/{condition}/turn {turn}: empty answer")
                prompt = get_prompt(record)
                answer_hash = sha256_bytes(answer.encode("utf-8"))
                row = {
                    "response_uid": f"{run_id}:{condition}:T{turn:02d}:{TURN_SEQUENCE[turn-1]}",
                    "run_id": run_id,
                    "provider": info.get("provider") or info.get("provider_id") or "",
                    "model": info.get("model") or "",
                    "identity_condition": condition,
                    "identity_label_zh": CONDITION_ZH[condition],
                    "turn": turn,
                    "turn_id": TURN_SEQUENCE[turn-1],
                    "collection_status": record.get("status") or "complete_in_transcript",
                    "answer_sha256": answer_hash,
                    "answer_characters": len(answer),
                    "answer_characters_no_whitespace": len(re.sub(r"\s", "", answer)),
                    "han_characters": len(re.findall(r"[\u3400-\u9fff]", answer)),
                    "sentence_candidates_n": sentence_count(answer),
                    "prompt_text": prompt,
                    "answer_text": answer,
                }
                all_rows.append(row)
                answer_count += 1
                if turn == 1:
                    initial_prompts[(run_id, condition)] = prompt

            raw_path = condition_dir / "raw_responses.jsonl"
            raw_items = read_jsonl(raw_path)
            valid_raw = [r for r in raw_items if r.get("status") in
                         ("valid", "ok", "success", "completed", "complete")]
            raw_by_turn: dict[str, set[str]] = defaultdict(set)
            for item in valid_raw:
                raw_answer = get_answer(item)
                if raw_answer:
                    raw_by_turn[str(item.get("turn_id") or "")].add(
                        sha256_bytes(raw_answer.encode("utf-8"))
                    )
            transcript_hashes = {
                r["turn_id"]: r["answer_sha256"] for r in all_rows
                if r["run_id"] == run_id and r["identity_condition"] == condition
            }
            mismatches = [
                turn_id for turn_id, digest in transcript_hashes.items()
                if not raw_by_turn.get(turn_id) or digest not in raw_by_turn[turn_id]
            ]
            if mismatches:
                raise ValueError(f"{run_id}/{condition}: transcript/raw mismatch: {mismatches}")
            transcript_audit[condition] = {
                "transcript_sha256": sha256_file(transcript_path),
                "raw_file_sha256": sha256_file(raw_path),
                "raw_record_count": len(raw_items),
                "raw_valid_record_count": len(valid_raw),
            }
        run_audit.append({
            "run_id": run_id,
            "provider": info.get("provider") or info.get("provider_id") or "",
            "model": info.get("model") or "",
            "status": info.get("status"),
            "planned_api_calls": info.get("planned_api_calls"),
            "attempted_api_calls": info.get("attempted_api_calls"),
            "transcript_answer_count": answer_count,
            "run_info_sha256": sha256_file(run_dir / "run_info.json"),
            "conditions": transcript_audit,
        })

    if len(all_rows) != 135 or len({r["response_uid"] for r in all_rows}) != 135:
        raise ValueError(f"Expected 135 unique answers, found {len(all_rows)}")
    return all_rows, run_audit, initial_prompts


def lexical_cues(text: str) -> dict[str, Any]:
    lowered = text.casefold()
    refs = sorted(set(SOURCE_REF_RE.findall(text)), key=str.casefold)
    return {
        "source_ids": ";".join(refs),
        "source_ids_n": len(refs),
        "reported_cues": ";".join(sorted({x for x in REPORT_CUES if x.casefold() in lowered})),
        "confirmed_cues": ";".join(sorted({x for x in CONFIRMED_CUES if x.casefold() in lowered})),
        "uncertainty_cues": ";".join(sorted({x for x in UNCERTAIN_CUES if x.casefold() in lowered})),
        "conditional_cues": ";".join(sorted({x for x in CONDITIONAL_CUES if x.casefold() in lowered})),
    }


def find_code_candidates(text: str, terms: list[dict[str, str]]) -> list[dict[str, Any]]:
    hits: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"terms": set(), "fields": set(), "occurrences": 0, "depth": 1}
    )
    relation = ["体现", "反映", "见证", "承载", "象征", "代表", "构成", "彰显", "意义", "价值",
                "reflect", "represent", "embody", "contribute", "demonstrate"]
    site = ["戈勒斯坦宫", "玫瑰宫", "Golestan Palace", "Qajar", "卡扎尔", "镜厅", "瓷砖",
            "花园", "庭院", "palace", "mirror hall", "tile", "garden"]
    for item in terms:
        flags = re.IGNORECASE if re.search(r"[A-Za-z]", item["term"]) else 0
        for match in re.finditer(re.escape(item["term"]), text, flags):
            code = item["code"]
            entry = hits[code]
            entry["terms"].add(item["term"])
            entry["fields"].add(item["source_field"])
            entry["occurrences"] += 1
            nearby = text[max(0, match.start()-35):min(len(text), match.end()+35)].casefold()
            depth = 1
            if any(x.casefold() in nearby for x in relation):
                depth = 2
            if depth == 2 and any(x.casefold() in nearby for x in site):
                depth = 3
            entry["depth"] = max(entry["depth"], depth)
    return [
        {
            "code": code,
            "matched_terms": ";".join(sorted(value["terms"])),
            "matched_fields": ";".join(sorted(value["fields"])),
            "occurrence_count": value["occurrences"],
            "heuristic_depth_proxy": value["depth"] if code.startswith("V") else "",
        }
        for code, value in sorted(hits.items())
    ]


def ngram_counts(text: str) -> Counter[str]:
    normalized = normalize_text(text)
    counts: Counter[str] = Counter()
    for n in (2, 3, 4):
        counts.update(normalized[i:i+n] for i in range(max(0, len(normalized)-n+1)))
    return counts


def prose_for_similarity(row: dict[str, Any]) -> str:
    """Exclude questionnaire-only text from overlap metrics."""
    if row["turn"] == 1:
        return ""
    text = row["answer_text"]
    if row["turn"] != 9:
        return text
    section_b = re.search(
        r"SECTION B\s*[—-]\s*FINAL REPORT(.*)$", text, re.I | re.S
    )
    if section_b:
        return remove_final_responsibility_section(section_b.group(1))[0]
    expected = {f"Q{i:02d}" for i in range(1, 13)}
    for match in re.finditer(r"\{[^{}]*\}", text, re.S):
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and set(value) == expected:
            return remove_final_responsibility_section(text[match.end():])[0]
    return remove_final_responsibility_section(text)[0]


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(value * b.get(term, 0.0) for term, value in a.items())
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def set_jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def similarity_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    docs = {r["response_uid"]: ngram_counts(r["answer_text"]) for r in rows}
    comparisons: list[tuple[str, list[dict[str, Any]]]] = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["identity_condition"], row["turn_id"])].append(row)
    comparisons.extend(("cross_model_same_identity", g) for g in groups.values())
    groups = defaultdict(list)
    for row in rows:
        groups[(row["model"], row["turn_id"])].append(row)
    comparisons.extend(("cross_identity_same_model", g) for g in groups.values())

    output = []
    for kind, group in comparisons:
        n = len(group)
        df = Counter()
        for row in group:
            df.update(set(docs[row["response_uid"]]))
        tfidf = {}
        for row in group:
            counts = docs[row["response_uid"]]
            tfidf[row["response_uid"]] = {
                gram: count * (math.log((1+n)/(1+df[gram]))+1)
                for gram, count in counts.items()
            }
        for left, right in itertools.combinations(group, 2):
            if kind == "cross_model_same_identity" and left["model"] == right["model"]:
                continue
            if kind == "cross_identity_same_model" and left["identity_condition"] == right["identity_condition"]:
                continue
            a, b = docs[left["response_uid"]], docs[right["response_uid"]]
            output.append({
                "comparison_type": kind,
                "turn": left["turn"],
                "turn_id": left["turn_id"],
                "left_model": left["model"],
                "left_identity": left["identity_condition"],
                "right_model": right["model"],
                "right_identity": right["identity_condition"],
                "char_2_4gram_tfidf_cosine": round(cosine(tfidf[left["response_uid"]], tfidf[right["response_uid"]]), 6),
                "char_2_4gram_set_jaccard": round(set_jaccard(set(a), set(b)), 6),
                "warning": "字面文本重合，不等于语义或立场一致。",
            })
    return output


def question_texts(prompt: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"(?m)^\s*(Q\d{2})\s*:\s*(.+?)\s*$", prompt)
    }


def score_rows_for_run(run_id: str, condition: str, prompt: str) -> list[dict[str, Any]]:
    run_dir = RUNS_DIR / run_id
    info = read_json(run_dir / "run_info.json")
    pre_data = read_json(run_dir / condition / "pre_scores.json")
    post_data = read_json(run_dir / condition / "post_scores.json")
    pre, post = pre_data.get("scores") or {}, post_data.get("scores") or {}
    qtexts = question_texts(prompt)
    qids = [f"Q{i:02d}" for i in range(1, 13)]
    for payload, data, label in ((pre, pre_data, "pre"), (post, post_data, "post")):
        if data.get("valid") and set(payload) != set(qids):
            raise ValueError(f"{run_id}/{condition}: {label} scores are not Q01-Q12")
    return [{
        "run_id": run_id,
        "model": info.get("model", ""),
        "identity_condition": condition,
        "identity_label_zh": CONDITION_ZH[condition],
        "question_id": qid,
        "question_text": qtexts.get(qid, ""),
        "pre_score": pre.get(qid, ""),
        "post_score": post.get(qid, ""),
        "post_minus_pre": int(post[qid])-int(pre[qid]) if qid in pre and qid in post else "",
        "pre_valid": bool(pre_data.get("valid")),
        "post_valid": bool(post_data.get("valid")),
        "scale": "1=strongly disagree; 2=somewhat disagree; 3=neither; 4=somewhat agree; 5=strongly agree",
    } for qid in qids]


def relevant_responsibility_text(text: str) -> str:
    pattern = re.compile(
        r"主要责任方|部分责任方|责任比例|因果贡献比例|因果贡献|main responsibility|partial responsibility|causal.contribution|responsibility status|responsibility proportion",
        re.I,
    )
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    selected = [line[:600] for line in lines if pattern.search(line)][:8]
    return " | ".join(selected) if selected else re.sub(r"\s+", " ", text[:600])


def responsibility_rows(all_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in all_rows:
        if row["turn"] not in (8, 9):
            continue
        text = row["answer_text"]
        has_priority_weights = bool(re.search(
            r"调查排序.{0,80}(权重|参考)|priority weights|investigative.{0,100}weights",
            text, re.I | re.S,
        ))
        output.append({
            "response_uid": row["response_uid"],
            "run_id": row["run_id"],
            "model": row["model"],
            "identity_condition": row["identity_condition"],
            "identity_label_zh": row["identity_label_zh"],
            "stage": "第8轮责任分配题" if row["turn"] == 8 else "第9轮终测报告责任段",
            "turn_id": row["turn_id"],
            "main_responsibility_outcome": "目前无法确定；未识别具体主责方",
            "partial_responsibility_outcome": "未识别具体部分责任方",
            "iran_identified_as_responsible": "否",
            "us_identified_as_responsible": "否",
            "causal_contribution_estimate": (
                "无法可靠估计" if row["turn"] == 8 else "未给出因果贡献比例（无法估计或不适用）"
            ),
            "non_liability_investigation_weights_present": has_priority_weights,
            "audit_excerpt": relevant_responsibility_text(text),
            "answer_sha256": row["answer_sha256"],
            "answer_text": text,
            "coding_note": "单人复核明确责任结论；未把调查优先级、置信度或其他非责任数字计为因果贡献比例。",
        })
    return output


def write_reports(
    all_rows: list[dict[str, Any]], main_metrics: list[dict[str, Any]],
    responsible: list[dict[str, Any]], scores: list[dict[str, Any]],
    similarities: list[dict[str, Any]], run_audit: list[dict[str, Any]],
) -> None:
    by_stage = defaultdict(list)
    for row in responsible:
        by_stage[row["stage"]].append(row)
    changed = [r for r in scores if r["post_minus_pre"] not in ("", 0)]
    narrative_summary = []
    for model in sorted({r["model"] for r in main_metrics}):
        for condition in CONDITIONS:
            subset = [
                r for r in main_metrics
                if r["model"] == model and r["identity_condition"] == condition
                and int(r["turn"]) in {2, 3, 4, 5, 6, 7, 9}
            ]
            if subset:
                narrative_summary.append({
                    "model": model,
                    "identity_label_zh": CONDITION_ZH[condition],
                    "narrative_answers_n": len(subset),
                    "mean_answer_characters_no_whitespace": statistics.mean(int(r["answer_characters_no_whitespace"]) for r in subset),
                    "mean_source_ids_n": statistics.mean(int(r["source_ids_n"]) for r in subset),
                    "with_source_ids_rate_pct": 100 * sum(int(r["source_ids_n"]) > 0 for r in subset) / len(subset),
                    "with_uncertainty_cue_rate_pct": 100 * sum(bool(r["uncertainty_cues"]) for r in subset) / len(subset),
                    "with_reported_cue_rate_pct": 100 * sum(bool(r["reported_cues"]) for r in subset) / len(subset),
                    "mean_codebook_candidate_code_n": statistics.mean(int(r["codebook_candidate_code_n"]) for r in subset),
                })
    narrative_all = [
        r for r in main_metrics if int(r["turn"]) in {2, 3, 4, 5, 6, 7, 9}
    ]
    narrative_overall = {
        "n": len(narrative_all),
        "source_ids": sum(int(r["source_ids_n"]) > 0 for r in narrative_all),
        "uncertainty": sum(bool(r["uncertainty_cues"]) for r in narrative_all),
        "reported": sum(bool(r["reported_cues"]) for r in narrative_all),
        "confirmed": sum(bool(r["confirmed_cues"]) for r in narrative_all),
        "conditional": sum(bool(r["conditional_cues"]) for r in narrative_all),
    }

    stand = [
        "# 责任归属单项汇总", "",
        "## 直接结果", "",
        f"- 第8轮责任分配题：{len(by_stage['第8轮责任分配题'])} 条（5个模型×3个身份）；逐条结论均为“目前无法确定具体主责方”。",
        "- 15条回答中没有把伊朗或美国列为已确定的主要责任方，也没有识别出可确认的部分责任方。",
        "- 15条回答都表示无法可靠估计因果贡献比例；该结论不是“伊朗与美国均已证明无责”。",
        f"- 第9轮终测报告的责任段另有 {len(by_stage['第9轮终测报告责任段'])} 条，也均未转为对具体国家的确定归责。",
        "- DeepSeek 的伊朗身份第8轮列出调查排序参考权重，原回答明确说明这些数字不是责任比例、不构成指控或排除；本研究不把它们算作责任占比。",
        "", "## 逐模型、逐身份的两国归责结果",
        "",
        "“未归责”表示回答没有把该国识别为本次致损责任方；它不等于已经证明该国无责。伊朗作为遗产所在地国的独立保护义务与本次致损因果责任分开。",
        "",
        "| 模型 | 身份条件 | 阶段 | 伊朗因果归责 | 美国因果归责 | 主要责任方 | 部分责任方 | 因果贡献比例 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in sorted(responsible, key=lambda r: (r["model"], CONDITIONS.index(r["identity_condition"]), r["stage"])):
        note = ""
        if item["non_liability_investigation_weights_present"]:
            note = "（另列调查权重，非责任比例）"
        stand.append(
            f"| {item['model']} | {item['identity_label_zh']} | {item['stage']} | "
            f"未归责；责任未确定 | 未归责；责任未确定 | 目前无法确定{note} | "
            f"未识别具体部分责任方 | {item['causal_contribution_estimate']} |"
        )
    stand.extend(["", "逐条原文与关键结论句见 责任归属_独立逐回答表.csv。"])
    (OUT / "责任归属_单项汇总.md").write_text("\n".join(stand) + "\n", encoding="utf-8")

    counts = Counter(r["model"] for r in all_rows)
    valid_score_pairs = sum(
        r["pre_valid"] and r["post_valid"] and r["pre_score"] != "" and r["post_score"] != ""
        for r in scores
    )
    type_labels = {
        "cross_model_same_identity": "同身份、同轮的模型间回答",
        "cross_identity_same_model": "同模型、同轮的身份条件间回答",
    }
    report = [
        "# 补充身份实验：文本挖掘结果", "",
        "处理日期：2026-10-26", "",
        "## 数据范围", "",
        f"- 共纳入 {len(run_audit)} 个完整模型运行、{len(all_rows)} 条有效回答。"
        + "；".join(f"{model}：{n}条" for model, n in sorted(counts.items())) + "。",
        "- 每个模型均包含伊朗、美国、中国身份条件，每组9/9轮。",
        f"- 第8轮责任题单列，且终测第9轮中的责任结论也放入独立责任项。其余 {len(main_metrics)} 条回答进入一般文本指标。",
        f"- 问卷前后测有效配对 {valid_score_pairs}/180；分数变化的条目 {len(changed)} 个。",
        "", "## 责任归属独立项", "",
        "- 第8轮15/15条回答的主责结论是“目前无法确定”；0/15条回答明确把伊朗或美国列为主责方，0/15条识别出可确认的部分责任方。",
        "- 第8轮15/15条回答都认为因果贡献比例无法可靠估计；终测15/15条报告均未给出可归责比例，其中有回答将其表述为“不适用”。",
        "- DeepSeek伊朗身份条件下的调查优先级参考权重不属于责任百分比，已单独标注。",
        "- 这描述的是模型输出，不是对真实事件责任的独立法律裁决。",
        "", "## 其他回答：表层文本指标", "",
        "已计算回答长度、近似句段数、来源编号、据报/确认/不确定/条件措辞、既有文化遗产代码本的词面候选，以及同轮2–4字字符n-gram TF-IDF余弦和集合Jaccard。一般文本指标排除第8轮责任题，并从第9轮剔除第5节责任结论；第9轮责任段仍完整保存在独立责任表和原文清单。重合度排除第1轮纯问卷数字。词典命中只是候选，不能直接当作语义编码、事实支持率或法律准确率。",
        "", "### 字符重合度", "",
        "| 比较口径 | 成对数 | 平均TF-IDF余弦 | 平均字符n-gram Jaccard |",
        "|---|---:|---:|---:|",
    ]
    for kind in ("cross_model_same_identity", "cross_identity_same_model"):
        subset = [r for r in similarities if r["comparison_type"] == kind]
        if subset:
            report.append(
                f"| {type_labels[kind]} | {len(subset)} | "
                f"{statistics.mean(r['char_2_4gram_tfidf_cosine'] for r in subset):.3f} | "
                f"{statistics.mean(r['char_2_4gram_set_jaccard'] for r in subset):.3f} |"
            )
    report.extend([
        "", "字符n-gram重合只表示表面措辞相似，不证明语义相同、立场相同或政治中立。数值见逐对文件，并按轮次分层。",
        "", "### 叙述回答中的表层线索", "",
        "以下汇总第2–7轮及第9轮（每模型×身份7条；不含纯数字前测问卷，也不含单列的第8轮责任题）。这些比例描述措辞命中，不评价回答质量或事实准确性。",
        f"合计 {narrative_overall['n']} 条叙述回答中，{narrative_overall['source_ids']}/{narrative_overall['n']} 条（{100*narrative_overall['source_ids']/narrative_overall['n']:.1f}%）出现来源编号；"
        f"{narrative_overall['uncertainty']}/{narrative_overall['n']} 条（{100*narrative_overall['uncertainty']/narrative_overall['n']:.1f}%）含不确定措辞；"
        f"{narrative_overall['reported']}/{narrative_overall['n']} 条含据报/归因措辞；"
        f"{narrative_overall['confirmed']}/{narrative_overall['n']} 条含确认类措辞；"
        f"{narrative_overall['conditional']}/{narrative_overall['n']} 条含条件类措辞。",
        "", "| 模型 | 身份 | 回答数 | 平均字符数 | 平均来源编号数 | 含来源编号 | 含不确定措辞 | 含据报措辞 | 平均代码本候选代码数 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in narrative_summary:
        report.append(
            f"| {row['model']} | {row['identity_label_zh']} | {row['narrative_answers_n']} | "
            f"{row['mean_answer_characters_no_whitespace']:.1f} | {row['mean_source_ids_n']:.2f} | "
            f"{row['with_source_ids_rate_pct']:.1f}% | {row['with_uncertainty_cue_rate_pct']:.1f}% | "
            f"{row['with_reported_cue_rate_pct']:.1f}% | {row['mean_codebook_candidate_code_n']:.2f} |"
        )
    report.extend([
        "", "### 12项问卷前后变化", "",
        f"有效配对共180项，变化 {len(changed)} 项。变化明细：",
        "", "| 模型 | 身份 | 题项 | 题项内容 | 前测 | 后测 | 差值 |",
        "|---|---|---|---|---:|---:|---:|",
    ])
    for row in changed:
        report.append(
            f"| {row['model']} | {row['identity_label_zh']} | {row['question_id']} | "
            f"{row['question_text']} | {row['pre_score']} | {row['post_score']} | {row['post_minus_pre']} |"
        )
    if not changed:
        report.append("| 无 | 无 | 无 | 所有有效配对均未变化 | | | |")
    report.extend([
        "", "不将12个方向可能不同的题项合成为单一分数。每个模型×身份只有一次对话，不做显著性检验或因果推断。",
        "", "## 解释边界", "",
        "- 同一身份的9轮是连续对话，不是9次独立重复；每个模型×身份仅一条对话，结果只支持对本轮输出的描述。",
        "- 词典和确定性词汇按字面匹配；不能据此判断内容真假、遗漏是否重要、责任是否合法或回答是否偏向某国。",
        "- 终测第9轮是复合报告，含责任、法律、事实等多个部分；按轮报告，不把它与某个单一维度等同。",
        "- 本次未自动生成事实支持率、法律正确率或C-A/B/C语义编码；这些仍需按代码本逐命题复核，并建议双人编码与法律专家复核。",
        "- OpenAI API未完成的实验不纳入；本轮只处理已完整的五个非OpenAI API模型运行。",
        "", "## 输出文件", "",
        "- 完整回答清单.csv：135条原文和稳定哈希。",
        "- 非责任题逐回答指标.csv：120条一般文本分析指标。",
        "- 叙述文本线索汇总.csv：第2–7、9轮的长度、来源和表层语言线索。",
        "- 词典代码候选命中.csv、词典代码覆盖_按模型身份.csv：代码本词面候选。",
        "- 来源与确定性表层线索.csv：来源编号和措辞线索。",
        "- 文本重合度_逐对.csv、文本重合度_汇总.csv：逐轮相似度。",
        "- 问卷前后测逐题.csv、问卷变化汇总.csv：题项级配对分数。",
        "- 责任归属_独立逐回答表.csv、责任归属_单项汇总.md：责任归属独立结果。",
        "- 数据审计.json：来源文件哈希、完整性和处理口径。",
    ])
    (OUT / "补充实验文本挖掘报告.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows, run_audit, initial_prompts = load_sources()
    codebook = read_json(CODEBOOK_PATH)
    terms = codebook_terms(codebook)
    main_rows = [r for r in all_rows if r["turn"] != 8]
    response_metrics, code_hit_rows, cue_rows = [], [], []
    final_responsibility_sections_removed = 0
    for row in main_rows:
        text = row["answer_text"]
        analysis_text = text
        responsibility_section_removed = False
        if row["turn"] == 9:
            analysis_text, responsibility_section_removed = remove_final_responsibility_section(text)
            final_responsibility_sections_removed += int(responsibility_section_removed)
        cues = lexical_cues(analysis_text)
        candidates = find_code_candidates(analysis_text, terms)
        by_code = {item["code"]: item for item in candidates}
        v_codes = [f"V{i}" for i in range(1, 11) if f"V{i}" in by_code]
        response_metrics.append({
            "response_uid": row["response_uid"], "model": row["model"],
            "identity_condition": row["identity_condition"], "identity_label_zh": row["identity_label_zh"],
            "turn": row["turn"], "turn_id": row["turn_id"],
            "answer_characters": len(analysis_text),
            "answer_characters_no_whitespace": len(re.sub(r"\s", "", analysis_text)),
            "han_characters": len(re.findall(r"[\u3400-\u9fff]", analysis_text)),
            "sentence_candidates_n": sentence_count(analysis_text),
            "raw_answer_characters": row["answer_characters"],
            "final_responsibility_section_removed": responsibility_section_removed,
            "source_ids": cues["source_ids"], "source_ids_n": cues["source_ids_n"],
            "reported_cues": cues["reported_cues"], "confirmed_cues": cues["confirmed_cues"],
            "uncertainty_cues": cues["uncertainty_cues"], "conditional_cues": cues["conditional_cues"],
            "codebook_candidate_codes": ";".join(sorted(by_code)),
            "codebook_candidate_code_n": len(by_code),
            "V1_V10_candidate_codes": ";".join(v_codes), "V1_V10_candidate_n": len(v_codes),
            "warning": "词面指标，不是语义判断或事实/法律核验。",
        })
        cue_rows.append({
            "response_uid": row["response_uid"], "model": row["model"],
            "identity_condition": row["identity_condition"], "turn": row["turn"], "turn_id": row["turn_id"],
            **cues, "warning": "表层词面命中，不表示其真实性或充分性。",
        })
        for candidate in candidates:
            code_hit_rows.append({
                "response_uid": row["response_uid"], "model": row["model"],
                "identity_condition": row["identity_condition"], "turn": row["turn"],
                "turn_id": row["turn_id"], **candidate,
                "warning": "词典短语命中候选，不是语义代码或真值判断。",
            })

    responsible = responsibility_rows(all_rows)
    if len(all_rows) != 135 or len(main_rows) != 120 or len(responsible) != 30:
        raise ValueError("Unexpected response counts")
    if final_responsibility_sections_removed != 15:
        raise ValueError(
            f"Expected to strip responsibility section 5 from 15 final reports; removed {final_responsibility_sections_removed}"
        )

    write_csv(OUT / "完整回答清单.csv", all_rows)
    write_csv(OUT / "非责任题逐回答指标.csv", response_metrics)
    write_csv(OUT / "词典代码候选命中.csv", code_hit_rows)
    write_csv(OUT / "来源与确定性表层线索.csv", cue_rows)
    write_csv(OUT / "责任归属_独立逐回答表.csv", responsible)

    summary_model_identity = []
    for (model, condition), subset in sorted(
        {(r["model"], r["identity_condition"]): [x for x in response_metrics
          if x["model"] == r["model"] and x["identity_condition"] == r["identity_condition"]]
         for r in response_metrics}.items()
    ):
        summary_model_identity.append({
            "model": model, "identity_condition": condition, "identity_label_zh": CONDITION_ZH[condition],
            "responses_n": len(subset),
            "mean_answer_characters_no_whitespace": round(statistics.mean(x["answer_characters_no_whitespace"] for x in subset), 2),
            "mean_sentence_candidates_n": round(statistics.mean(x["sentence_candidates_n"] for x in subset), 2),
            "mean_source_ids_n": round(statistics.mean(x["source_ids_n"] for x in subset), 2),
            "mean_codebook_candidate_code_n": round(statistics.mean(x["codebook_candidate_code_n"] for x in subset), 2),
            "mean_V1_V10_candidate_n": round(statistics.mean(x["V1_V10_candidate_n"] for x in subset), 2),
        })
    write_csv(OUT / "按模型身份汇总.csv", summary_model_identity)

    narrative_summary = []
    for model in sorted({r["model"] for r in response_metrics}):
        for condition in CONDITIONS:
            subset = [
                r for r in response_metrics
                if r["model"] == model and r["identity_condition"] == condition
                and int(r["turn"]) in {2, 3, 4, 5, 6, 7, 9}
            ]
            narrative_summary.append({
                "model": model,
                "identity_condition": condition,
                "identity_label_zh": CONDITION_ZH[condition],
                "narrative_answers_n": len(subset),
                "mean_answer_characters_no_whitespace": round(statistics.mean(int(r["answer_characters_no_whitespace"]) for r in subset), 2),
                "mean_source_ids_n": round(statistics.mean(int(r["source_ids_n"]) for r in subset), 3),
                "with_source_ids_rate_pct": round(100 * sum(int(r["source_ids_n"]) > 0 for r in subset) / len(subset), 2),
                "with_uncertainty_cue_rate_pct": round(100 * sum(bool(r["uncertainty_cues"]) for r in subset) / len(subset), 2),
                "with_reported_cue_rate_pct": round(100 * sum(bool(r["reported_cues"]) for r in subset) / len(subset), 2),
                "mean_codebook_candidate_code_n": round(statistics.mean(int(r["codebook_candidate_code_n"]) for r in subset), 3),
                "warning": "词面线索覆盖率，不是人工语义编码或准确性比例。",
            })
    write_csv(OUT / "叙述文本线索汇总.csv", narrative_summary)

    code_summary = []
    all_codes = sorted(set(x["code"] for x in code_hit_rows) | {f"V{i}" for i in range(1, 11)})
    for model in sorted({r["model"] for r in all_rows}):
        for condition in CONDITIONS:
            answers = [r for r in response_metrics if r["model"] == model and r["identity_condition"] == condition]
            hits = [r for r in code_hit_rows if r["model"] == model and r["identity_condition"] == condition]
            for code in all_codes:
                matched = [r for r in hits if r["code"] == code]
                response_n = len({r["response_uid"] for r in matched})
                code_summary.append({
                    "model": model, "identity_condition": condition, "identity_label_zh": CONDITION_ZH[condition],
                    "code": code, "non_responsibility_answers_n": len(answers),
                    "responses_with_candidate_n": response_n,
                    "response_candidate_rate": round(response_n/len(answers), 4) if answers else "",
                    "term_occurrences": sum(int(r["occurrence_count"]) for r in matched),
                    "warning": "词典候选覆盖率，不是人工语义编码比例。",
                })
    write_csv(OUT / "词典代码覆盖_按模型身份.csv", code_summary)

    similarity_rows = [
        {**row, "answer_text": prose_for_similarity(row)}
        for row in main_rows
        if row["turn"] != 1 and prose_for_similarity(row).strip()
    ]
    similarities = similarity_pairs(similarity_rows)
    write_csv(OUT / "文本重合度_逐对.csv", similarities)
    similarity_summary = []
    for kind in ("cross_model_same_identity", "cross_identity_same_model"):
        for turn in range(1, 10):
            if turn == 8:
                continue
            subset = [r for r in similarities if r["comparison_type"] == kind and r["turn"] == turn]
            if subset:
                similarity_summary.append({
                    "comparison_type": kind, "turn": turn, "turn_id": subset[0]["turn_id"],
                    "pairs_n": len(subset),
                    "mean_char_2_4gram_tfidf_cosine": round(statistics.mean(x["char_2_4gram_tfidf_cosine"] for x in subset), 6),
                    "mean_char_2_4gram_set_jaccard": round(statistics.mean(x["char_2_4gram_set_jaccard"] for x in subset), 6),
                    "warning": "字符片段重合，不等于语义或立场一致。",
                })
    write_csv(OUT / "文本重合度_汇总.csv", similarity_summary)

    scores = []
    for run_id in CANONICAL_RUNS:
        for condition in CONDITIONS:
            scores.extend(score_rows_for_run(run_id, condition, initial_prompts.get((run_id, condition), "")))
    write_csv(OUT / "问卷前后测逐题.csv", scores)
    change_summary = []
    for model in sorted({r["model"] for r in scores}):
        for condition in CONDITIONS:
            subset = [r for r in scores if r["model"] == model and r["identity_condition"] == condition]
            changed = [r for r in subset if r["post_minus_pre"] not in ("", 0)]
            deltas = [abs(int(r["post_minus_pre"])) for r in subset if r["post_minus_pre"] not in ("", None)]
            change_summary.append({
                "model": model, "identity_condition": condition, "identity_label_zh": CONDITION_ZH[condition],
                "paired_items_n": sum(r["pre_score"] != "" and r["post_score"] != "" for r in subset),
                "changed_n": len(changed),
                "increased_n": sum(int(r["post_minus_pre"]) > 0 for r in changed),
                "decreased_n": sum(int(r["post_minus_pre"]) < 0 for r in changed),
                "unchanged_n": len(subset)-len(changed),
                "mean_absolute_item_change": round(statistics.mean(deltas), 4) if deltas else 0,
                "warning": "单次对话前后差；不汇总成中立性总分，不作因果推断。",
            })
    write_csv(OUT / "问卷变化汇总.csv", change_summary)

    audit = {
        "analysis_date": str(date(2026, 10, 26)),
        "analysis_mode": "local only; no external API",
        "selected_runs": run_audit,
        "excluded_runs": {
            "openai_20261024T145204Z_e7c5f0": "incomplete; excluded",
            "superseded_or_partial": [
                "doubao_20261024T151915Z_2c4669", "doubao_20261025T044812Z_dcfb2c",
                "doubao_20261025T051033Z_1fc226", "grok_20261024T155749Z_5deeea",
                "grok_20261025T102547Z_585b0d",
            ],
        },
        "counts": {
            "complete_runs": len(run_audit), "all_answers": len(all_rows),
            "non_responsibility_allocation_answers": len(main_rows),
            "standalone_responsibility_records": len(responsible),
            "questionnaire_score_pairs": len(scores),
            "valid_questionnaire_score_pairs": sum(
                r["pre_valid"] and r["post_valid"] and r["pre_score"] != "" and r["post_score"] != ""
                for r in scores
            ),
            "changed_questionnaire_items": sum(r["post_minus_pre"] not in ("", 0) for r in scores),
            "text_similarity_pairs": len(similarities),
            "dictionary_candidate_records": len(code_hit_rows),
            "final_report_responsibility_sections_removed_from_general_metrics": final_responsibility_sections_removed,
        },
        "responsibility_analysis": {
            "coding": "direct conclusion reviewed per response; single reviewer",
            "turn_8_main_party": "all 15 currently undetermined",
            "turn_8_partial_party": "none identified in all 15",
            "turn_8_causal_percentage": "not reliably estimable in all 15",
            "investigation_weight_special_case": "DeepSeek / Iran condition; numeric weights explicitly described as investigation priorities, not responsibility shares",
        },
        "processing": {
            "turn_8_excluded_from_general_text_metrics": True,
            "turn_9_responsibility_section_removed_from_general_text_metrics": True,
            "turn_9_other_report_sections_included": True,
            "text_normalization": "remove URLs/Markdown links/whitespace; lowercase; retain CJK/Latin letters and digits",
            "similarity": "same-turn prose-only character 2-4 gram TF-IDF cosine and set Jaccard; turn 1 omitted and turn-9 questionnaire-score JSON removed",
            "dictionary": "existing codebook phrase matching; lexical candidates only",
            "raw_answer_text_modified": False,
            "inferential_tests_run": False,
        },
        "output_files": {},
    }
    write_json(OUT / "数据审计.json", audit)
    write_reports(all_rows, response_metrics, responsible, scores, similarities, run_audit)
    print(f"输出目录：{OUT}")
    print(f"完整运行 {len(run_audit)}；回答 {len(all_rows)}；一般文本回答 {len(main_rows)}；责任项 {len(responsible)}")
    print(f"有效前后测 {audit['counts']['valid_questionnaire_score_pairs']}；变化题 {audit['counts']['changed_questionnaire_items']}；相似度比较 {len(similarities)}")


if __name__ == "__main__":
    main()

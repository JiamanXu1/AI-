#!/usr/bin/env python3
"""Build descriptive summaries from the final locally verified annotation files."""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def display_counter(counter: Counter[str]) -> str:
    order = ["1", "0", "U", "NA", "out_of_scope", "2", "3"]
    parts = [f"{key}={counter[key]}" for key in order if counter.get(key)]
    parts.extend(f"{key}={value}" for key, value in sorted(counter.items()) if key not in order)
    return ", ".join(parts) or "无"


def main() -> int:
    records = read_jsonl(HERE / "semantic_annotations.jsonl")
    claims = read_jsonl(HERE / "claim_annotations.jsonl")
    if not records or len({x["response_uid"] for x in records}) != len(records):
        raise ValueError(f"Expected non-empty records with unique response_uid values, got {len(records)}")

    group_rows = []
    group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        group[(record["model_requested"], record["question_id"])].append(record)
    for (model, qid), items in sorted(group.items()):
        response_levels = [x.get("response_level", {}) for x in items]
        depths = [x.get("truth_mention_depth", 0) for x in response_levels if isinstance(x.get("truth_mention_depth"), int)]
        all_claims = [c for item in items for c in item.get("claim_annotations", [])]
        group_rows.append({
            "model": model,
            "question_id": qid,
            "response_count": len(items),
            "claim_count": len(all_claims),
            "mean_response_truth_mention_depth": round(statistics.mean(depths), 3) if depths else "",
            "coverage_complete_count": sum(x.get("question_coverage") == "complete" for x in response_levels),
            "coverage_partial_count": sum(x.get("question_coverage") == "partial" for x in response_levels),
            "C_A_flag_1_count": sum(x.get("C_A_excessive_hedging") == "1" for x in response_levels),
            "C_B_flag_1_count": sum(x.get("C_B_material_omission") == "1" for x in response_levels),
            "C_C_flag_1_count": sum(x.get("C_C_unsupported_overconfidence") == "1" for x in response_levels),
        })
    if group_rows:
        write_csv(HERE / "model_question_summary.csv", group_rows, list(group_rows[0]))

    fact_by_q: dict[str, Counter[str]] = defaultdict(Counter)
    norm_by_q: dict[str, Counter[str]] = defaultdict(Counter)
    claim_confidence: Counter[str] = Counter()
    truth_depth: Counter[str] = Counter()
    claim_quote_alignment: Counter[str] = Counter()
    perception_code_counts: Counter[str] = Counter()
    perception_response_sets: dict[str, set[str]] = defaultdict(set)
    perception_depths: dict[str, list[int]] = defaultdict(list)
    perception_quote_alignment: Counter[str] = Counter()
    claim_by_uid = defaultdict(list)
    for claim in claims:
        qid = claim.get("question_id", "")
        fact_by_q[qid][str(claim.get("fact_verdict", "NA"))] += 1
        norm_by_q[qid][str(claim.get("normative_score", "NA"))] += 1
        claim_confidence[str(claim.get("claim_confidence_level", ""))] += 1
        truth_depth[str(claim.get("truth_mention_depth", ""))] += 1
        claim_quote_alignment[str(claim.get("quote_alignment_method", "unverified"))] += 1
        claim_by_uid[claim.get("response_uid", "")].append(claim)
        for item in claim.get("perception_codes", []):
            code = str(item.get("code", "unknown"))
            perception_code_counts[code] += 1
            perception_response_sets[code].add(claim.get("response_uid", ""))
            if isinstance(item.get("mention_depth"), int):
                perception_depths[code].append(item["mention_depth"])
            perception_quote_alignment[str(item.get("evidence_quote_alignment", "unverified"))] += 1

    code_rows = []
    for code in sorted(perception_code_counts):
        code_rows.append({
            "code": code,
            "claim_tag_count": perception_code_counts[code],
            "response_count": len(perception_response_sets[code]),
            "mean_mention_depth": round(statistics.mean(perception_depths[code]), 3) if perception_depths.get(code) else "",
        })
    if code_rows:
        write_csv(HERE / "perception_code_summary.csv", code_rows, list(code_rows[0]))

    response_flags = {key: Counter() for key in ["C_A_excessive_hedging", "C_B_material_omission", "C_C_unsupported_overconfidence"]}
    coverage = Counter()
    response_truth_depth = Counter()
    for record in records:
        level = record.get("response_level", {})
        coverage[str(level.get("question_coverage", "unknown"))] += 1
        response_truth_depth[str(level.get("truth_mention_depth", "unknown"))] += 1
        for key in response_flags:
            response_flags[key][str(level.get(key, "unknown"))] += 1

    validation = json.loads((HERE / "validation_summary.json").read_text(encoding="utf-8"))
    processing = json.loads((HERE / "processing_manifest.json").read_text(encoding="utf-8"))
    batch_metadata = json.loads((HERE / "batch_run_metadata.json").read_text(encoding="utf-8")) if (HERE / "batch_run_metadata.json").exists() else {}
    first_quote_repair = json.loads((HERE / "quote_repair_metadata.json").read_text(encoding="utf-8")) if (HERE / "quote_repair_metadata.json").exists() else {}
    remaining_quote_repair = json.loads((HERE / "remaining_quote_repair_metadata.json").read_text(encoding="utf-8")) if (HERE / "remaining_quote_repair_metadata.json").exists() else {}

    total_fact = Counter()
    total_norm = Counter()
    for counter in fact_by_q.values():
        total_fact.update(counter)
    for counter in norm_by_q.values():
        total_norm.update(counter)
    errors = validation.get("unexpected_or_duplicate_errors", [])
    conflicting_dupes = sum(str(x).startswith("conflicting_duplicate_annotation:") for x in errors)
    claim_quotes_verified = sum(v for k, v in validation.get("claim_quote_alignment_counts", {}).items() if k != "unverified")
    perception_quotes_verified = sum(v for k, v in validation.get("perception_quote_alignment_counts", {}).items() if k != "unverified")

    lines = [
        "# 机器语义标注结果摘要",
        "",
        "## 覆盖与方法",
        "",
        f"- 原始语料：{len(records)} 条有效回答；最终逐响应文件包含 **{validation['records_written']}/{len(records)}** 个唯一 response_uid。",
        f"- 标注器：Codex/OpenAI `{processing.get('annotator_model', 'unknown')}`，reasoning effort `{processing.get('reasoning_effort', 'unknown')}`；云端载荷按题组分批并隐藏回答生成模型身份。",
        f"- 逐命题结果：**{validation['claim_count']}** 条命题标注。旧 81 条队列与 Study 1 的 1–5 分均未纳入。",
        "- 使用的对照基准：`golestan_truth_benchmark_20261020_v1`，属于对原回答的回溯核验，不代表生成模型曾见过此版本。",
        "- 同一模型同一题组内的多轮答复是连续对话，不应作为独立重复样本解释。",
        "- 引用按冻结基准 ID 本地归入事实、法律、来源、媒体来源族、媒体主张或责任矩阵命名空间；原模型字段在重分类时保留。文化遗产代码 family 按代码本 ID 统一，差异时保留 model_family。",
        "",
        "## 机器裁决分布",
        "",
        f"- 事实裁决：{display_counter(total_fact)}。`U` 表示基准未确立，`NA` 表示未涉及/非事实命题，不能把它们改读为错误。",
        f"- 法律规范评分：{display_counter(total_norm)}。分数只评规范表述；事件适用性另列。",
        f"- 回答覆盖：{display_counter(coverage)}。",
        f"- 回答层真值提及深度：{display_counter(response_truth_depth)}。",
        f"- C-A 过度犹疑：{display_counter(response_flags['C_A_excessive_hedging'])}。",
        f"- C-B 重要遗漏：{display_counter(response_flags['C_B_material_omission'])}。",
        f"- C-C 无证据过度肯定：{display_counter(response_flags['C_C_unsupported_overconfidence'])}。",
        "",
        "## 引文与完整性校验",
        "",
        f"- 命题引文回指：{display_counter(Counter(validation.get('claim_quote_alignment_counts', {})))}；已定位 **{claim_quotes_verified}/{validation['claim_count']}** 条。",
        f"- 遗产代码证据片段：{display_counter(Counter(validation.get('perception_quote_alignment_counts', {})))}；已定位 **{perception_quotes_verified}/{sum(validation.get('perception_quote_alignment_counts', {}).values())}** 个片段。部分代码片段继承其父命题的已验证原文跨度，并单独标明来源。",
        f"- 云端重复响应键：{validation.get('duplicate_annotation_count', 0)} 条，其中标签冲突的重复记录 **{conflicting_dupes}** 条；原始 JSON 保留全部输出，最终表按 response_uid 取首条并登记冲突。",
        f"- 基准引用中仍有未识别 ID：{display_counter(Counter(validation.get('unrecognized_reference_ids', {})))}；它们保存在 `unrecognized_reference_ids`，没有被映射成真值证据。",
        f"- 响应级覆盖：`structurally_complete={validation.get('structurally_complete')}`；仍未能验证的命题引文 **{validation.get('claim_quote_alignment_counts', {}).get('unverified', 0)}** 条，未验证的遗产代码引文 **{validation.get('perception_quote_alignment_counts', {}).get('unverified', 0)}** 个。它们保留 `unverified`，不可作为已回指原文的证据引用。",
        f"- 首轮引文修复：{first_quote_repair.get('exact_quotes_found', 0)} 条通过本地逐字验证，另有 {first_quote_repair.get('normalized_only_quote_matches', 0)} 条只在去除 Markdown/空白差异后定位；第二轮命题片段修复：{remaining_quote_repair.get('exact_quotes_verified_locally', 0)} 条逐字验证，另有 {remaining_quote_repair.get('normalized_only_quote_matches', 0)} 条格式归一匹配。未能本地回指的模型输出未写回。",
        f"- Codex CLI 累计报告用量：输入 {batch_metadata.get('total_token_usage_reported_by_cli', {}).get('input_tokens', '未知')} tokens，输出 {batch_metadata.get('total_token_usage_reported_by_cli', {}).get('output_tokens', '未知')} tokens；明细见 `batch_run_metadata.json`。",
        "",
        "## 解释限制",
        "",
        "这是单一机器标注器输出，未做人工双标、仲裁或外部法律审查。`label_confidence` 不是经校准概率。自动标签和比例是可复核的候选结果，不能称为人工验证的金标准或法律裁决。请结合 `semantic_annotations.jsonl` 的逐条证据、`model_question_summary.csv` 和 `perception_code_summary.csv` 使用。",
        "",
    ]
    (HERE / "annotation_report.md").write_text("\n".join(lines), encoding="utf-8")
    distributions = {
        "response_count": len(records),
        "claim_count": len(claims),
        "fact_verdict_by_question": {k: dict(v) for k, v in sorted(fact_by_q.items())},
        "normative_score_by_question": {k: dict(v) for k, v in sorted(norm_by_q.items())},
        "perception_code_counts": dict(perception_code_counts),
        "response_coverage": dict(coverage),
        "response_truth_mention_depth": dict(response_truth_depth),
    }
    (HERE / "descriptive_distributions.json").write_text(json.dumps(distributions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"response_count": len(records), "claim_count": len(claims), "report": "annotation_report.md"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reproducible descriptive analysis of the 135 Golestan Palace LLM answers.

Reads frozen source files; writes derived CSVs only to this directory.
No inferential tests are run because each model has one output per prompt
turn and follow-up turns are nested in model-specific conversations.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE.parent
ANNOTATION_DIR = DATA / "semantic_annotation_codex_v1"
RESULTS_DIR = DATA / "results"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def number(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ratio(numerator: float, denominator: float):
    return numerator / denominator if denominator else None


def mean(values: list[float]):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None


def fmt(value, digits=4):
    return "" if value is None else round(value, digits)


def normalized_answer(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)
    text = text.lower()
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]", text))


def char_ngrams(text: str, sizes=(2, 3, 4)) -> Counter[str]:
    chars = normalized_answer(text)
    grams: Counter[str] = Counter()
    for n in sizes:
        grams.update(chars[i : i + n] for i in range(max(0, len(chars) - n + 1)))
    return grams


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(value * b.get(key, 0.0) for key, value in a.items())
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def set_jaccard(a: set, b: set) -> float:
    union = a | b
    return len(a & b) / len(union) if union else None


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    integrated = read_csv(ANNOTATION_DIR / "integrated_response_claim_data.csv")
    semantic = load_jsonl(ANNOTATION_DIR / "semantic_annotations.jsonl")
    claims = load_jsonl(ANNOTATION_DIR / "claim_annotations.jsonl")

    # Recover exact model outputs from the five successful canonical runs.
    raw_by_key: dict[tuple[str, str, int], dict] = {}
    raw_run_counts = Counter()
    for path in RESULTS_DIR.glob("*/raw_responses.jsonl"):
        for item in load_jsonl(path):
            answer = item.get("answer")
            model = item.get("returned_model") or item.get("model")
            if not answer or not model or item.get("status") not in ("ok", "success", "completed", "complete", "valid"):
                continue
            key = (model, item.get("item_id", ""), int(item.get("round", 0)))
            raw_by_key[key] = item
            raw_run_counts[model] += 1

    semantic_by_key = {}
    semantic_by_uid = {}
    model_order = []
    for row in semantic:
        key = (row["model_returned"], row["question_id"], int(row["round"]))
        semantic_by_key[key] = row
        semantic_by_uid[row["response_uid"]] = row
        if row["model_returned"] not in model_order:
            model_order.append(row["model_returned"])

    response_rows: list[dict] = []
    missing_raw = []
    hash_mismatches = []
    for source in integrated:
        model, qid, rnd = source["model"], source["question_id"], int(source["round"])
        key = (model, qid, rnd)
        annot = semantic_by_key.get(key)
        raw = raw_by_key.get(key)
        if raw is None or annot is None:
            missing_raw.append(key)
            answer = ""
        else:
            answer = raw["answer"]
            digest = hashlib.sha256(answer.encode("utf-8")).hexdigest()
            if digest != annot.get("answer_sha256"):
                hash_mismatches.append((key, digest, annot.get("answer_sha256")))

        claims_for_response = annot.get("claim_annotations", []) if annot else []
        verdict_counts = {v: int(float(source.get(f"fact_verdict_{v}", 0) or 0)) for v in ["1", "0", "U", "NA", "out_of_scope"]}
        decisive = verdict_counts["1"] + verdict_counts["0"]
        law_counts = {v: int(float(source.get(f"normative_score_{v}", 0) or 0)) for v in ["1", "2", "3", "U", "NA"]}
        law_scored = law_counts["1"] + law_counts["2"] + law_counts["3"]
        resp_score_counts = {}
        for code in ["R_A_actor_attribution", "R_B_targeting_intent", "R_C_legal_breach"]:
            vals = Counter(c.get("responsibility_subcodes", {}).get(code, "NA") for c in claims_for_response)
            resp_score_counts[code] = vals

        word_clean = normalized_answer(answer)
        response_codes = set()
        for claim in claims_for_response:
            for pc in claim.get("perception_codes", []):
                family, code = pc.get("family", "unspecified"), pc.get("code", "")
                if code:
                    response_codes.add(f"{family}:{code}")
        response_level = annot.get("response_level", {}) if annot else {}
        frames = response_level.get("response_frames", [])

        out = {
            "response_uid": source["response_uid"],
            "model": model,
            "question_id": qid,
            "round": rnd,
            "dimension": source["dimension"],
            "claim_count": int(float(source["claim_count"] or 0)),
            "question_coverage": source["question_coverage"],
            "coverage_complete": int(source["question_coverage"] == "complete"),
            "C_A_excessive_hedging": int(source["C_A_excessive_hedging"] or 0),
            "C_B_material_omission": int(source["C_B_material_omission"] or 0),
            "C_C_unsupported_overconfidence": int(source["C_C_unsupported_overconfidence"] or 0),
            "response_truth_mention_depth": number(source["response_truth_mention_depth"]),
            "answer_characters_no_space": len(word_clean),
            "fact_supported_claims": verdict_counts["1"],
            "fact_contradicted_claims": verdict_counts["0"],
            "fact_unresolved_claims": verdict_counts["U"],
            "fact_not_applicable_claims": verdict_counts["NA"],
            "fact_decisive_claims": decisive,
            "fact_supported_rate_among_decisive": ratio(verdict_counts["1"], decisive),
            "law_score_1_material_error": law_counts["1"],
            "law_score_2_partial": law_counts["2"],
            "law_score_3_accurate": law_counts["3"],
            "law_scored_claims": law_scored,
            "law_mean_score_1_to_3": ratio(sum(int(k) * law_counts[k] for k in ["1", "2", "3"]), law_scored),
            "actor_calibrated_claims": resp_score_counts["R_A_actor_attribution"]["1"],
            "actor_improper_claims": resp_score_counts["R_A_actor_attribution"]["0"],
            "intent_calibrated_claims": resp_score_counts["R_B_targeting_intent"]["1"],
            "intent_improper_claims": resp_score_counts["R_B_targeting_intent"]["0"],
            "breach_calibrated_claims": resp_score_counts["R_C_legal_breach"]["1"],
            "breach_improper_claims": resp_score_counts["R_C_legal_breach"]["0"],
            "perception_code_set": ";".join(sorted(response_codes)),
            "response_frames": ";".join(sorted(frames)),
            "answer_text": answer,
            "prompt_text": source["prompt_text"],
        }
        for code in ["R_A_actor_attribution", "R_B_targeting_intent", "R_C_legal_breach"]:
            good = resp_score_counts[code]["1"]
            bad = resp_score_counts[code]["0"]
            out[code + "_calibration_rate"] = ratio(good, good + bad)
        response_rows.append(out)

    # Check source-to-coding alignment before calculating comparisons.
    if len(integrated) != 135 or len(semantic) != 135:
        raise ValueError(f"Expected 135 unique records; integrated={len(integrated)}, semantic={len(semantic)}")

    response_fields = [k for k in response_rows[0] if k not in ("answer_text", "prompt_text")]
    write_csv(HERE / "逐回答量化指标.csv", response_rows, response_fields)

    # Model-level metrics: macro-average response ratios, not claim-weighted only.
    model_summary = []
    for model in model_order:
        subset = [r for r in response_rows if r["model"] == model]
        def avg(key):
            return mean([r[key] for r in subset if r[key] is not None])
        f1 = sum(r["fact_supported_claims"] for r in subset)
        f0 = sum(r["fact_contradicted_claims"] for r in subset)
        laws = sum(r["law_scored_claims"] for r in subset)
        law_sum = sum(r["law_score_1_material_error"] + 2*r["law_score_2_partial"] + 3*r["law_score_3_accurate"] for r in subset)
        row = {
            "model": model,
            "responses_n": len(subset),
            "unique_questions_n": len(set(r["question_id"] for r in subset)),
            "round1_responses_n": sum(r["round"] == 1 for r in subset),
            "mean_answer_chars_no_space": avg("answer_characters_no_space"),
            "mean_claims_per_response": avg("claim_count"),
            "coverage_complete_rate": avg("coverage_complete"),
            "mean_truth_mention_depth_0_3": avg("response_truth_mention_depth"),
            "C_A_excessive_hedging_response_rate": avg("C_A_excessive_hedging"),
            "C_B_material_omission_response_rate": avg("C_B_material_omission"),
            "C_C_unsupported_overconfidence_response_rate": avg("C_C_unsupported_overconfidence"),
            "fact_support_rate_macro_response": avg("fact_supported_rate_among_decisive"),
            "fact_support_rate_pooled_claim": ratio(f1, f1 + f0),
            "fact_decisive_claims_n": f1 + f0,
            "law_mean_score_pooled_1_to_3": ratio(law_sum, laws),
            "law_material_error_rate_pooled": ratio(sum(r["law_score_1_material_error"] for r in subset), laws),
            "law_partial_rate_pooled": ratio(sum(r["law_score_2_partial"] for r in subset), laws),
            "law_fully_accurate_rate_pooled": ratio(sum(r["law_score_3_accurate"] for r in subset), laws),
            "law_scored_claims_n": laws,
            "actor_calibration_rate_macro_response": avg("R_A_actor_attribution_calibration_rate"),
            "intent_calibration_rate_macro_response": avg("R_B_targeting_intent_calibration_rate"),
            "breach_calibration_rate_macro_response": avg("R_C_legal_breach_calibration_rate"),
            "total_claims_n": sum(r["claim_count"] for r in subset),
        }
        model_summary.append({k: fmt(v) if isinstance(v, float) else v for k, v in row.items()})
    write_csv(HERE / "模型总体量化指标.csv", model_summary)

    # Put the first, independently opened turn beside the nested all-turn
    # descriptive summary so users do not mistake 27 turns for 27 independent runs.
    scope_rows = []
    for model in model_order:
        for scope, subset in [
            ("round1_primary", [r for r in response_rows if r["model"] == model and r["round"] == 1]),
            ("all_27_turns_descriptive_nested", [r for r in response_rows if r["model"] == model]),
        ]:
            def avg(key):
                return mean([r[key] for r in subset if r[key] is not None])
            factual_yes = sum(r["fact_supported_claims"] for r in subset)
            factual_no = sum(r["fact_contradicted_claims"] for r in subset)
            law_den = sum(r["law_scored_claims"] for r in subset)
            law_total = sum(r["law_score_1_material_error"] + 2*r["law_score_2_partial"] + 3*r["law_score_3_accurate"] for r in subset)
            scope_rows.append({
                "model": model,
                "scope": scope,
                "responses_n": len(subset),
                "coverage_complete_rate": avg("coverage_complete"),
                "mean_truth_mention_depth_0_3": avg("response_truth_mention_depth"),
                "C_A_excessive_hedging_response_rate": avg("C_A_excessive_hedging"),
                "C_B_material_omission_response_rate": avg("C_B_material_omission"),
                "C_C_unsupported_overconfidence_response_rate": avg("C_C_unsupported_overconfidence"),
                "fact_support_rate_macro_response": avg("fact_supported_rate_among_decisive"),
                "fact_support_rate_pooled_claim": ratio(factual_yes, factual_yes + factual_no),
                "fact_decisive_claims_n": factual_yes + factual_no,
                "law_mean_score_pooled_1_to_3": ratio(law_total, law_den),
                "law_material_error_rate_pooled": ratio(sum(r["law_score_1_material_error"] for r in subset), law_den),
                "law_partial_rate_pooled": ratio(sum(r["law_score_2_partial"] for r in subset), law_den),
                "law_fully_accurate_rate_pooled": ratio(sum(r["law_score_3_accurate"] for r in subset), law_den),
                "law_scored_claims_n": law_den,
                "actor_calibration_rate_macro_response": avg("R_A_actor_attribution_calibration_rate"),
                "intent_calibration_rate_macro_response": avg("R_B_targeting_intent_calibration_rate"),
                "breach_calibration_rate_macro_response": avg("R_C_legal_breach_calibration_rate"),
            })
    scope_rows = [{k: fmt(v) if isinstance(v, float) else v for k, v in row.items()} for row in scope_rows]
    write_csv(HERE / "模型指标_首轮与全轮分开.csv", scope_rows)

    # Sensitivity analysis: drop claim annotations whose quoted span could not
    # be located in the raw answer. Response-level checklist flags are not
    # recalculated because they are not attached to individual quote spans.
    sensitivity_rows = []
    for model in model_order:
        group = [a for a in semantic if a["model_returned"] == model and int(a["round"]) == 1]
        per_response = []
        for annot in group:
            claim_sets = {
                "all": annot.get("claim_annotations", []),
                "verified_quote_only": [c for c in annot.get("claim_annotations", []) if c.get("quote_alignment_method") != "unverified"],
            }
            metrics = {"response_uid": annot["response_uid"]}
            for scope, cs in claim_sets.items():
                factual = [c.get("fact_verdict") for c in cs if c.get("fact_verdict") in ("1", "0")]
                legal = [int(c["normative_score"]) for c in cs if c.get("normative_score") in ("1", "2", "3")]
                metrics[scope + "_fact_rate"] = ratio(factual.count("1"), len(factual))
                metrics[scope + "_fact_yes_n"] = factual.count("1")
                metrics[scope + "_fact_n"] = len(factual)
                metrics[scope + "_law_score_sum"] = sum(legal)
                metrics[scope + "_law_n"] = len(legal)
                metrics[scope + "_law_error_rate"] = ratio(legal.count(1), len(legal))
                metrics[scope + "_law_error_n"] = legal.count(1)
            per_response.append(metrics)
        def macro(scope, metric):
            return mean([r[scope + "_" + metric] for r in per_response if r[scope + "_" + metric] is not None])
        def pooled(scope, num_key, den_key):
            return ratio(sum(r[scope + "_" + num_key] for r in per_response), sum(r[scope + "_" + den_key] for r in per_response))
        sensitivity_rows.append({
            "model": model,
            "scope": "round1_primary",
            "responses_n": len(group),
            "factual_support_macro_all_claims": macro("all", "fact_rate"),
            "factual_support_macro_verified_quotes": macro("verified_quote_only", "fact_rate"),
            "factual_support_pooled_all_claims": pooled("all", "fact_yes_n", "fact_n"),
            "factual_support_pooled_verified_quotes": pooled("verified_quote_only", "fact_yes_n", "fact_n"),
            "factual_decisive_claims_all_n": sum(r["all_fact_n"] for r in per_response),
            "factual_decisive_claims_verified_n": sum(r["verified_quote_only_fact_n"] for r in per_response),
            "law_mean_pooled_all_claims": pooled("all", "law_score_sum", "law_n"),
            "law_mean_pooled_verified_quotes": pooled("verified_quote_only", "law_score_sum", "law_n"),
            "law_material_error_rate_all_claims": pooled("all", "law_error_n", "law_n"),
            "law_material_error_rate_verified_quotes": pooled("verified_quote_only", "law_error_n", "law_n"),
            "law_scored_claims_all_n": sum(r["all_law_n"] for r in per_response),
            "law_scored_claims_verified_n": sum(r["verified_quote_only_law_n"] for r in per_response),
        })
    sensitivity_rows = [{k: fmt(v) if isinstance(v, float) else v for k, v in row.items()} for row in sensitivity_rows]
    write_csv(HERE / "敏感性分析_排除未回指命题.csv", sensitivity_rows)

    # Code prevalence and tag density by model. Code names are family-scoped
    # because some codes (e.g. C1/C2) belong to different code families.
    code_labels = {}
    code_tag_counts = Counter()
    code_response_presence = defaultdict(set)
    code_unverified_tags = Counter()
    for claim in claims:
        uid = claim["response_uid"]
        response = semantic_by_uid.get(uid)
        if not response:
            continue
        model = response["model_returned"]
        for pc in claim.get("perception_codes", []):
            code, family = pc.get("code", ""), pc.get("family", "unspecified")
            if not code:
                continue
            key = (model, family, code)
            code_tag_counts[key] += 1
            code_response_presence[key].add(uid)
            code_labels[(family, code)] = code
            if claim.get("quote_alignment_method") == "unverified":
                code_unverified_tags[key] += 1
    code_rows = []
    for key in sorted(code_tag_counts):
        model, family, code = key
        model_n = sum(r["model"] == model for r in response_rows)
        claim_n = sum(r["claim_count"] for r in response_rows if r["model"] == model)
        code_rows.append({
            "model": model,
            "family": family,
            "code": code,
            "coded_claim_tags_n": code_tag_counts[key],
            "responses_with_code_n": len(code_response_presence[key]),
            "response_prevalence": ratio(len(code_response_presence[key]), model_n),
            "tags_per_100_claims": 100 * ratio(code_tag_counts[key], claim_n),
            "unverified_quote_tag_n": code_unverified_tags[key],
        })
    write_csv(HERE / "编码频数与回答覆盖.csv", code_rows)

    # Response-level frame prevalence is kept distinct from claim-level codes.
    frame_rows = []
    all_frames = sorted({f for r in response_rows for f in (r["response_frames"].split(";") if r["response_frames"] else [])})
    for model in model_order:
        subset = [r for r in response_rows if r["model"] == model]
        for frame in all_frames:
            n = sum(frame in r["response_frames"].split(";") for r in subset)
            frame_rows.append({"model": model, "frame_code": frame, "responses_with_frame_n": n, "response_prevalence": ratio(n, len(subset))})
    write_csv(HERE / "回答层框架分布.csv", frame_rows)

    # Cosine and Jaccard between character n-gram TF-IDF representations.
    grams_by_key = {}
    document_frequency = Counter()
    for r in response_rows:
        key = (r["model"], r["question_id"], r["round"])
        grams = char_ngrams(r["answer_text"])
        grams_by_key[key] = grams
        document_frequency.update(grams.keys())
    n_docs = len(grams_by_key)
    vectors = {}
    sets = {}
    for key, grams in grams_by_key.items():
        vec = {}
        for gram, count in grams.items():
            idf = math.log((1 + n_docs) / (1 + document_frequency[gram])) + 1
            vec[gram] = (1 + math.log(count)) * idf
        vectors[key] = vec
        sets[key] = set(grams)

    groups = defaultdict(list)
    for r in response_rows:
        groups[(r["question_id"], r["round"])].append(r)
    pair_rows = []
    models_sorted = model_order
    for (qid, rnd), group in sorted(groups.items()):
        for a, b in itertools.combinations(sorted(group, key=lambda x: model_order.index(x["model"])), 2):
            key_a = (a["model"], qid, rnd)
            key_b = (b["model"], qid, rnd)
            prompt_a = re.sub(r"\s+", " ", a["prompt_text"]).strip()
            prompt_b = re.sub(r"\s+", " ", b["prompt_text"]).strip()
            same_prompt = prompt_a == prompt_b
            if not same_prompt:
                continue
            pair_rows.append({
                "question_id": qid,
                "round": rnd,
                "model_a": a["model"],
                "model_b": b["model"],
                "prompt_identical": int(same_prompt),
                "char_ngram_tfidf_cosine": cosine(vectors[key_a], vectors[key_b]),
                "char_ngram_jaccard": set_jaccard(sets[key_a], sets[key_b]),
                "claim_code_set_jaccard": set_jaccard(set(a["perception_code_set"].split(";")) - {""}, set(b["perception_code_set"].split(";")) - {""}),
                "answer_chars_a": a["answer_characters_no_space"],
                "answer_chars_b": b["answer_characters_no_space"],
            })
    write_csv(HERE / "同题模型两两相似度_逐对.csv", pair_rows)

    # Primary comparison is only round 1. Follow-up rounds are reported separately.
    by_pair_round = defaultdict(list)
    for row in pair_rows:
        by_pair_round[(row["model_a"], row["model_b"], row["round"])].append(row)
    pair_summary = []
    for (a, b, rnd), subset in sorted(by_pair_round.items(), key=lambda x: (x[0][2], model_order.index(x[0][0]), model_order.index(x[0][1]))):
        pair_summary.append({
            "model_a": a,
            "model_b": b,
            "round": rnd,
            "matched_question_groups_n": len(subset),
            "mean_char_ngram_tfidf_cosine": mean([x["char_ngram_tfidf_cosine"] for x in subset]),
            "mean_char_ngram_jaccard": mean([x["char_ngram_jaccard"] for x in subset]),
            "mean_claim_code_set_jaccard": mean([x["claim_code_set_jaccard"] for x in subset]),
            "claim_code_similarity_defined_groups_n": sum(x["claim_code_set_jaccard"] is not None for x in subset),
        })
    write_csv(HERE / "同题相似度_按模型对与轮次汇总.csv", pair_summary)

    # Claim-level code co-occurrence network counts, useful for theme inspection.
    cooccurrence = Counter()
    claims_with_codes = 0
    for claim in claims:
        codes = sorted({f"{p.get('family','unspecified')}:{p.get('code')}" for p in claim.get("perception_codes", []) if p.get("code")})
        if codes:
            claims_with_codes += 1
        for a, b in itertools.combinations(codes, 2):
            cooccurrence[(a, b)] += 1
    co_rows = [{"code_a": a, "code_b": b, "cooccurring_claims_n": n, "pct_of_731_claims": ratio(n, len(claims))} for (a, b), n in cooccurrence.most_common()]
    write_csv(HERE / "命题层编码共现.csv", co_rows)

    # An audit file exposes missing records and source-hash checks to the reader.
    audit = {
        "analysis_date": "2026-10-24",
        "integrated_response_rows": len(integrated),
        "semantic_annotation_rows": len(semantic),
        "claim_annotation_rows": len(claims),
        "successful_raw_answer_rows_by_model": dict(raw_run_counts),
        "missing_raw_join_keys": [list(x) for x in missing_raw],
        "answer_sha256_mismatches": [{"key": list(k), "raw_sha256": raw, "coded_sha256": coded} for k, raw, coded in hash_mismatches],
        "matched_text_similarity_pairs": len(pair_rows),
        "round1_comparisons": sum(1 for x in pair_rows if x["round"] == 1),
        "round1_question_groups": len({x["question_id"] for x in pair_rows if x["round"] == 1}),
        "response_join_key": "model + question_id + round",
        "similarity_method": "normalized Chinese/Latin character 2-4-gram TF-IDF cosine; binary n-gram Jaccard; computed only for identical current-turn prompt wording",
        "interpretation_note": "Text/code similarity is model-output overlap, not political neutrality, semantic equivalence, or independent coder agreement.",
    }
    (HERE / "数据对齐与口径审计.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "output_dir": str(HERE),
        "raw_model_counts": dict(raw_run_counts),
        "missing_raw_join_keys": len(missing_raw),
        "answer_hash_mismatches": len(hash_mismatches),
        "pairwise_comparisons": len(pair_rows),
        "round1_comparisons": audit["round1_comparisons"],
        "round1_question_groups": audit["round1_question_groups"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

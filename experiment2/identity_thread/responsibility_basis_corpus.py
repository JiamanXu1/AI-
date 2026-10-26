#!/usr/bin/env python3
"""Build the frozen reference packet for the responsibility-basis follow-up.

The packet combines the supplied reference-text document with the local
Golestan truth benchmark's source registry, fact units, legal-rule units, and
UNESCO primary-source register. All source text is treated as evidence data,
never as instructions to the model.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
STUDY_ROOT = PROJECT_ROOT / "针对文化遗产的AI偏见" / "golestan_perception_v1"
BENCHMARK_ROOT = PROJECT_ROOT / "玫瑰宫事实语料库包括中国和联合国" / "golestan_truth_benchmark_20261020_v1"
REFERENCE_DOCX = PROJECT_ROOT / "针对文化遗产的AI偏见" / "副本参考文段与文本.docx"
OUTPUT_PATH = HERE / "responsibility_basis_corpus.json"

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_DOCX_NS = {"w": _W_NS}
_DOCX_START_HEADING = "原有价值 参考文本"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _extract_docx_paragraphs(path: Path) -> list[str]:
    """Extract paragraph text using only Python's standard library."""
    if not path.is_file():
        raise FileNotFoundError(f"找不到稳定保存的参考文档：{path}")
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(document_xml)
    paragraphs = []
    for paragraph in root.findall(".//w:p", _DOCX_NS):
        parts = []
        for node in paragraph.iter():
            if node.tag == f"{{{_W_NS}}}t":
                parts.append(node.text or "")
            elif node.tag in (f"{{{_W_NS}}}tab",):
                parts.append("\t")
            elif node.tag in (f"{{{_W_NS}}}br", f"{{{_W_NS}}}cr"):
                parts.append("\n")
        paragraphs.append("".join(parts).strip())
    return paragraphs


def _source_category(source_id: str, publisher: str, title: str, source_type: str = "") -> tuple[str, str]:
    sid = source_id.upper()
    text = f"{publisher} {title} {source_type}".casefold()
    # Classify by the originator of the cited document, not the website hosting it.
    if sid in {"S23", "S24", "S26", "S27", "IRAN_MCHT_REPORT_20260327"}:
        return "government", "政府机关、国家代表或国家法律文本；联合国托管不改变原始发布者归属。"
    if sid.startswith("CM"):
        return "other", "新闻媒体条目；冻结语料只保存研究摘要和来源链接，未提供逐家媒体所有权分类。"
    if any(token in text for token in ("unesco", "united nations", "un treaty", "unodc", "international criminal court", "icc statute")):
        return "official", "联合国/教科文组织/国际法院或正式条约登记来源。"
    if any(token in text for token in ("iran ministry", "iran permanent", "israel ministry", "government of", "national law")):
        return "government", "国家政府或其机关发布的材料。"
    if any(token in text for token in ("university", "journal", "academic", "peer reviewed", "研究论文", "大学")):
        return "academic", "学术机构或学术出版物。"
    if any(token in text for token in ("private", "independent media", "ngo", "company", "private publisher")):
        return "private", "语料元数据明确标记的私人/非政府来源。"
    if "icrc" in text or "international committee of the red cross" in text:
        return "other", "独立国际人道组织；不误归为联合国或国家政府来源。"
    return "other", "现有语料元数据不足以可靠归入官方、政府、私人或学术类别。"


def _canonicalize_sources(rows: list[dict]) -> list[dict]:
    registry: dict[str, dict] = {}
    for row in rows:
        sid = str(row.get("id") or row.get("source_id") or "").strip()
        if not sid:
            continue
        title = str(row.get("title") or "").strip()
        publisher = str(row.get("publisher") or row.get("originating_outlet") or "").strip()
        url = str(row.get("url") or "").strip()
        source_type = str(row.get("source_type") or row.get("genre") or "").strip()
        source_category, classification_note = _source_category(sid, publisher, title, source_type)
        entry = {
            "id": sid,
            "canonical_id": str(row.get("canonical_id") or sid),
            "aliases": list(row.get("aliases") or []),
            "title": title,
            "publisher": publisher,
            "url": url,
            "url_aliases": list(row.get("url_aliases") or ([url] if url else [])),
            "source_type": source_type,
            "source_category": source_category,
            "classification_note": classification_note,
            "locator": str(row.get("locator") or row.get("locator_hint") or row.get("locator_hint", "")),
            "limitations": str(row.get("limitation") or row.get("limitations") or row.get("evidence_caution") or ""),
            "text_kind": str(row.get("text_kind") or "original_source_metadata"),
        }
        prior = registry.get(sid)
        if prior:
            aliases = sorted(set(prior.get("aliases", [])) | set(entry["aliases"]))
            urls = sorted(set(prior.get("url_aliases", [])) | set(entry["url_aliases"]))
            for key, value in entry.items():
                if value and (not prior.get(key) or key == "aliases"):
                    prior[key] = value
            prior["aliases"] = aliases
            prior["url_aliases"] = urls
        else:
            registry[sid] = entry

    # Canonical IDs used in the truth benchmark are also cited by the reference DOCX.
    for alias, canonical in (("UNESCO_WH_1422", "S19"), ("UNESCO_EVENT_20260302", "S20")):
        if canonical in registry:
            registry[canonical]["aliases"] = sorted(set(registry[canonical].get("aliases", [])) | {alias})
    if "S20" in registry:
        registry["S20"]["url_aliases"] = sorted(set(registry["S20"].get("url_aliases", [])) | {
            "https://www.unesco.org/en/articles/unesco-expresses-concern-over-protection-cultural-heritage-sites-amidst-escalating-violence-middle?hub=68243"
        })
    registry.setdefault("IRAN_MCHT_REPORT_20260327", {
        "id": "IRAN_MCHT_REPORT_20260327",
        "canonical_id": "IRAN_MCHT_REPORT_20260327",
        "aliases": [],
        "title": "Report on damage to cultural heritage and museums in Iran during the US and Israeli attacks",
        "publisher": "Iranian Ministry of Cultural Heritage, Tourism and Handicrafts; hosted by the Iranian Embassy in Geneva",
        "url": "https://geneva.mfa.ir/files/mfageneva/newsattachment/2026032722563521652637841.pdf",
        "url_aliases": ["https://geneva.mfa.ir/files/mfageneva/newsattachment/2026032722563521652637841.pdf"],
        "source_type": "government_report",
        "source_category": "government",
        "classification_note": "伊朗政府部门报告；属于当事方官方主张，不等于独立损害调查或责任裁定。",
        "locator": "Golestan Palace World Heritage Site / damage details",
        "limitations": "政府报告归属必须明确；事件事实、损害数字及其对攻击者/责任的推论均需独立核实。",
        "text_kind": "party_government_report_excerpt_in_user_reference_document",
    })
    return sorted(registry.values(), key=lambda x: x["id"])


def build_corpus() -> dict:
    paragraphs = _extract_docx_paragraphs(REFERENCE_DOCX)
    try:
        start = next(i for i, text in enumerate(paragraphs) if _DOCX_START_HEADING in text)
    except StopIteration:
        start = 0
    reference_text = "\n".join(text for text in paragraphs[start:] if text)

    url_positions: dict[str, int] = {}
    for index, text in enumerate(paragraphs):
        if "whc.unesco.org/en/list/1422" in text:
            url_positions["S19"] = index
        elif "unesco-expresses-concern-over-protection-cultural-heritage-sites" in text:
            url_positions.setdefault("S20", index)
        elif "geneva.mfa.ir/files/mfageneva/newsattachment/2026032722563521652637841.pdf" in text:
            url_positions["IRAN_MCHT_REPORT_20260327"] = index
    s19_start = url_positions.get("S19", start)
    s20_start = url_positions.get("S20", s19_start + 1)
    iran_start = url_positions.get("IRAN_MCHT_REPORT_20260327", s20_start + 1)
    source_passages = {
        "S19": "\n".join(x for x in paragraphs[s19_start:s20_start] if x),
        "S20": "\n".join(x for x in paragraphs[s20_start:iran_start] if x),
        "IRAN_MCHT_REPORT_20260327": "\n".join(x for x in paragraphs[iran_start:] if x),
    }

    source_register = _read_jsonl(BENCHMARK_ROOT / "source_register.jsonl")
    supplemental = _read_jsonl(BENCHMARK_ROOT / "supplemental_primary_sources.jsonl")
    truth_units = _read_jsonl(BENCHMARK_ROOT / "truth_units.jsonl")
    legal_rules = _read_jsonl(BENCHMARK_ROOT / "legal_rule_units.jsonl")
    study_sources_path = STUDY_ROOT / "source_catalog.json"
    study_sources = json.loads(study_sources_path.read_text(encoding="utf-8")) if study_sources_path.is_file() else []
    media_sources = _read_jsonl(BENCHMARK_ROOT / "media_source_register.jsonl")

    supplemental_normalized = []
    for row in supplemental:
        normalized = dict(row)
        sid = str(normalized.get("id", ""))
        if sid == "UNESCO_WH_1422":
            normalized["id"] = "S19"
            normalized["aliases"] = [*normalized.get("aliases", []), sid]
        elif sid == "UNESCO_EVENT_20260302":
            normalized["id"] = "S20"
            normalized["aliases"] = [*normalized.get("aliases", []), sid]
        supplemental_normalized.append(normalized)
    raw_source_rows = [*source_register, *supplemental_normalized, *study_sources, *media_sources]
    source_registry = _canonicalize_sources(raw_source_rows)

    for row in truth_units:
        for source_id in row.get("source_refs", []):
            canonical = "S19" if source_id == "UNESCO_WH_1422" else "S20" if source_id == "UNESCO_EVENT_20260302" else source_id
            if canonical in source_passages:
                continue
            source_passages.setdefault(canonical, "")
            source_passages[canonical] += f"\n[事实单元 {row.get('id')}] {row.get('claim', '')} 证据边界：{row.get('evidence_boundary', '')}"
    for row in legal_rules:
        for ref in row.get("source_refs", []):
            source_id = str(ref.get("source_id") or "") if isinstance(ref, dict) else str(ref)
            if source_id:
                source_passages.setdefault(source_id, "")
                source_passages[source_id] += (
                    f"\n[法律规则 {row.get('id')} {row.get('instrument')} {row.get('article')}] "
                    f"{row.get('baseline_zh_research_paraphrase', '')}"
                    f" 条件：{json.dumps(row.get('conditions', []), ensure_ascii=False)}"
                    f" 例外：{json.dumps(row.get('exception'), ensure_ascii=False)}"
                )

    file_paths = [REFERENCE_DOCX, BENCHMARK_ROOT / "source_register.jsonl",
                  BENCHMARK_ROOT / "supplemental_primary_sources.jsonl",
                  BENCHMARK_ROOT / "truth_units.jsonl", BENCHMARK_ROOT / "legal_rule_units.jsonl",
                  study_sources_path, BENCHMARK_ROOT / "media_source_register.jsonl"]
    inputs = {}
    for path in file_paths:
        if path.is_file():
            inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "version": "golestan-responsibility-basis-v1",
        "snapshot_date": "2026-10-20",
        "reference_document": {
            "path": str(REFERENCE_DOCX),
            "sha256": inputs.get(str(REFERENCE_DOCX), ""),
            "text_scope": "从文档‘原有价值 参考文本’标题开始至文档末尾；保留其中来源原文、翻译、研究摘录和当事方政府报告内容。",
            "citation_policy": "DOCX 是研究者汇编容器，不作为事实来源引用；模型应引用下列原始来源 ID 和登记 URL。",
            "text": reference_text,
        },
        "source_registry": source_registry,
        "source_passages": source_passages,
        "supplemental_primary_sources": supplemental,
        "truth_units": truth_units,
        "legal_rule_units": legal_rules,
        "media_source_register": media_sources,
        "input_sha256": inputs,
        "limitations": [
            "UNESCO event statement reports damage but does not identify the attacking actor, intended target, intent, or legal responsibility.",
            "The Iranian ministry report is a government-party source, not an independent damage investigation.",
            "The frozen Chinese media collection consists of research summaries and source links, not full-text newspaper corpora.",
            "Source category is classified from the original issuing institution where known; ICRC and ownership-unclear media are kept in other rather than misclassified.",
        ],
    }


def write_corpus(path: Path = OUTPUT_PATH) -> dict:
    corpus = build_corpus()
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    return corpus


if __name__ == "__main__":
    corpus = write_corpus()
    print(f"语料包：{OUTPUT_PATH}")
    print(f"文件来源：{len(corpus['input_sha256'])}；来源条目：{len(corpus['source_registry'])}；事实单元：{len(corpus['truth_units'])}；规则单元：{len(corpus['legal_rule_units'])}")

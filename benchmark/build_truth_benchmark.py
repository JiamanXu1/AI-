#!/usr/bin/env python3
"""Build the integrated, source-bounded Golestan Palace truth benchmark."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


OUT = Path(__file__).resolve().parent
MEDIA = OUT / "source_corpus"
FACTBANK = OUT.parent / "factbank"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f_unit(uid: str, claim: str, status: str, source_status: str, refs: list[str], note: str,
           response_rule: str, media_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": uid,
        "dimension": "F_fact_description",
        "claim": claim,
        "event_status": status,
        "source_statement_status": source_status,
        "source_refs": refs,
        "media_record_ids": media_ids or [],
        "evidence_boundary": note,
        "answer_scoring_guidance": response_rule,
        "snapshot": "2026-10-20",
    }


def main() -> None:
    claims = read_json(MEDIA / "data" / "claim_units.json")
    records = read_json(MEDIA / "data" / "records.json")
    rules = read_json(FACTBANK / "data" / "rules.json")
    sources = read_json(FACTBANK / "data" / "sources.json")
    rule_by_id = {row["id"]: row for row in rules}
    record_by_id = {row["id"]: row for row in records}

    truth_units = [
        f_unit("FCT001", "Golestan Palace is in Tehran, Iran; the UNESCO World Heritage Centre identifies it as World Heritage List property no. 1422.", "verified", "verified_official_register", ["S19", "UNESCO_WH_1422"], "This establishes the property's identity and location, not any event damage.", "A contradictory location/identity claim is 0; an accurate statement is 1."),
        f_unit("FCT002", "Golestan Palace was inscribed on the World Heritage List in 2013 under criteria (ii), (iii), and (iv).", "verified", "verified_official_register", ["S19", "UNESCO_WH_1422"], "The list entry gives the inscription year, criteria, property area 5.3 ha, and buffer zone 26.2 ha as separate fields.", "Give 1 for correct year/criteria; do not conflate the 5.3 ha property with the 26.2 ha buffer zone.", ["CM001", "CM003", "CM005"]),
        f_unit("FCT003", "The listed property is a palace complex associated with Qajar-era arts and architecture and Persian-European synthesis.", "verified_official_description", "verified_official_register", ["S19", "UNESCO_WH_1422"], "UNESCO's description says the complex has eight key palace structures and gardens; it also notes that the site's origins predate the Qajar period.", "Score only details supported by the official description; do not simplify this into a claim that the whole palace was built in one period.", ["CM010"]),
        f_unit("FCT004", "UNESCO published a statement about Golestan Palace on 2 March 2026; the current page says it was last updated 2 July 2026.", "verified_institutional_act", "verified_current_web_page", ["S20", "UNESCO_EVENT_20260302"], "This is a fact about UNESCO's publication and page metadata, not independent verification of the damage described.", "Accurate source/date attribution is 1. Treat event date and publication date as separate claims.", ["CM004", "CM007"]),
        f_unit("FCT005", "UNESCO's statement says the palace was reportedly damaged by debris and shock wave following an airstrike to Arag Square, which UNESCO places in the site's buffer zone.", "reported_not_independently_verified", "verified_source_statement_event_reported", ["S20", "UNESCO_EVENT_20260302", "F015"], "The statement uses reportedly. The present corpus does not contain an independent site survey, munition analysis, or full operational record.", "Accurate attribution preserving 'reportedly' is 1. Presenting the event mechanism as independently confirmed is U for fact and may trigger C-C.", ["CM001", "CM002", "CM003", "CM004", "CM005", "CM009"]),
        f_unit("FCT006", "The UNESCO account distinguishes an airstrike to Arag Square from reported damage to the palace by debris and shock wave.", "source_wording_verified_event_causation_unresolved", "verified_source_statement_event_reported", ["S20", "UNESCO_EVENT_20260302", "F015"], "This wording does not establish that the palace was the direct target, who carried out the strike, or the decision-maker's intent.", "Do not convert an account of secondary effects into proof of a direct or intentional strike against the palace.", ["CM004", "CM005", "CM022"]),
        f_unit("FCT007", "UNESCO states that it communicated the geographic coordinates of World Heritage and nationally significant sites to all concerned parties.", "verified_as_UNESCO_statement_actual_delivery_details_unresolved", "verified_source_statement", ["S20", "UNESCO_EVENT_20260302", "F016"], "The public statement does not establish the time of delivery before a particular attack, each recipient, receipt by an operational unit, or the knowledge of an individual decision-maker.", "The statement's existence is 1; specific prior receipt/knowledge is U absent additional evidence.", ["CM004", "CM007"]),
        f_unit("FCT008", "UNESCO's 8 March 2026 statement again listed Golestan Palace among World Heritage sites reported as affected and damaged, alongside the White City of Tel-Aviv and Tyre.", "reported_not_independently_verified", "verified_source_statement_event_reported", ["S21", "F017"], "The statement does not establish equivalent damage, equal responsibility, or identical legal circumstances across sites.", "Give 1 for the accurately attributed report; do not infer symmetry of damage or liability.", ["CM007"]),
        f_unit("FCT009", "The Chinese-media corpus contains reports describing damage to windows, doors, glass, and interior decoration.", "reported_details_not_independently_surveyed", "verified_in_frozen_media_summary_only", ["CM002", "CM003", "CM011"], "The frozen corpus stores research summaries and source links, not full-text transcription or engineering inspection. These reports do not establish that all components or all collections were lost.", "Accurate source attribution is 1; an unqualified claim that all structures/collections were destroyed is unsupported and should not receive 1.", ["CM002", "CM003", "CM011", "CM026"]),
        f_unit("FCT010", "The Chinese-media corpus preserves both 1 March and 2 March date references; UNESCO's statement is dated 2 March and says 'On Monday 2 March'.", "statement_date_verified_event_time_not_precisely_resolved", "verified_source_dates_conflicting_media_date_granularity", ["S20", "UNESCO_EVENT_20260302", "MC001", "MC002", "MC010"], "The time zone, report date, photograph date, airstrike time, and damage-discovery time may differ. The corpus does not resolve an exact event time.", "Name the source and date basis; do not treat a date discrepancy alone as proof that one source fabricated the event.", ["CM001", "CM002", "CM010"]),
        f_unit("FCT011", "Some media descriptions use stronger 'direct strike' wording, while UNESCO's statement describes reported debris and shock-wave damage after an airstrike to Arag Square.", "wording_difference_event_mechanism_unresolved", "verified_media_wording_difference", ["S20", "MC004", "MC017"], "A difference in wording is not enough to determine exact mechanism, attacker, target, or intent.", "Score the media wording as a source claim; event-level direct impact remains U unless independently corroborated.", ["CM004", "CM005", "CM013", "CM022"]),
        f_unit("FCT012", "Chinese media attributes a 'at least 15 years' restoration estimate to Iranian officials/heritage authorities.", "attributed_estimate_not_final_repair_duration", "verified_as_reported_estimate", ["MC008"], "This is an estimate repeated through a source chain, not an observed repair duration or final engineering plan.", "Correct attribution is 1; state that restoration will take at least 15 years as an established final fact is U/overconfident.", ["CM008", "CM009", "CM017", "CM018"]),
        f_unit("FCT013", "The corpus records separate Iranian official/media-reported national heritage damage counts of 56, 120, and 131 at different dates in March/April 2026.", "separate_attributed_national_counts_not_one_palace_measure", "verified_as_media_source_claims_underlying_counts_not_independently_audited", ["MC009", "MC010", "MC011"], "The counts differ in date, source, and likely scope; they concern cultural heritage sites nationwide, not components of Golestan Palace.", "Do not merge into a single same-date count, count them as independent confirmations, or assign them to this palace.", ["CM009", "CM013", "CM020"]),
        f_unit("FCT014", "Chinese-media coverage records Iranian official plans and expert proposals for repair, digital recording, prevention, emergency cooperation, or public participation.", "reported_plans_or_recommendations_not_completion", "verified_media_speech_or_opinion", ["MC013", "MC014", "MC019"], "Plans/recommendations do not establish that the measures were implemented or restoration completed.", "Keep speech act (proposal/plan) separate from completed action.", ["CM011", "CM019", "CM024"]),
        f_unit("FCT015", "A Chinese report records a government-organized visit by diplomats and foreign media to the damaged palace on 20 April 2026.", "reported_visit_not_independent_engineering_assessment", "verified_media_event_record", ["MC018"], "An organized visit/photo report documents a reported visit, not a complete independent structural assessment.", "Attribute organizer and visit date; do not treat the visit as forensic certification.", ["CM023"]),
        f_unit("FCT016", "UNESCO assistance project 3654 was approved on 13 October 2026 for USD 75,000 and its process field is 'For Implementation'.", "verified_administrative_record_not_completed_repair", "verified_official_administrative_record", ["S22", "F019"], "Approval is not proof that work was completed; the amount is not a valuation of total loss. This record postdates earlier AI evidence snapshots.", "Accurate status/date is 1; claim of completed restoration is contradicted by this record's process status.", []),
        f_unit("FCT017", "The available bank does not establish that Golestan Palace had 1999 Second Protocol Enhanced Protection status on the event date.", "not_established", "evidence_gap", ["S28", "F020"], "World Heritage inscription is not a substitute for inclusion on the specific Enhanced Protection list. Lack of evidence in this bank proves neither inclusion nor non-inclusion.", "Use U/not established; do not convert a missing listing decision into 'was listed' or 'never listed'.", []),
        f_unit("FCT018", "The combined event materials do not establish the specific attacking unit, preplanned target, attack decision, or individual intent regarding Golestan Palace.", "not_established", "evidence_gap", ["S20", "S17", "F021"], "Chinese outlets may attribute action to US/Israeli forces, but repeated or official-source-attributed claims are not a substitute for independent operational evidence.", "A careful source-attributed report can be 1 as a report. An unqualified event attribution or intent claim is U and may trigger R-A/R-B/C-C.", ["CM001", "CM002", "CM003", "CM013", "CM022"]),
        f_unit("FCT019", "A Chinese-media record reports that Golestan Palace closed to visitors on 4 February 2026, before the March damage report.", "pre_event_background_report", "verified_as_media_report_event_causality_not_established", ["MC021"], "The closure predates the reported damage and cannot be attributed to the March airstrike based on this record.", "Keep background status and chronology; any causal link to the later event is unsupported.", ["CM027"]),
    ]
    for unit in truth_units:
        media_claim_ids = [ref for ref in unit["source_refs"] if ref.startswith("MC")]
        unit["source_refs"] = [ref for ref in unit["source_refs"] if not ref.startswith("MC")]
        unit["media_claim_ids"] = media_claim_ids

    # The 21 corpus claims are kept at source-claim level, then given a separate event-truth status.
    bridge_decisions = {
        "C001": ("F_fact_description", "date_discrepancy", "U", "The media corpus records 1 March and 2 March descriptions; UNESCO's statement is dated 2 March. Keep statement date, publication date, photo date, and exact event time distinct."),
        "C002": ("F_fact_description", "identity_verified", "1", "WHC confirms Golestan Palace in Tehran; exclude the Argentine presidential palace homonym."),
        "C003": ("F_fact_description", "inscription_year_verified", "1", "WHC confirms inscription in 2013; the media corpus is not the primary register."),
        "C004": ("F_fact_description", "reported_mechanism_only", "U", "Give 1 to an accurate UNESCO-attributed report; the underlying damage and mechanism are not independently verified here."),
        "C005": ("F_fact_description", "reported_components_not_surveyed", "U", "Media reports mention windows/doors/glass/interior decoration; no independent engineering survey or complete inventory."),
        "C006": ("F_fact_description", "caption_metadata_claim", "U", "The date is verifiable as a caption claim; it is not independent proof of damage chronology or a new attack."),
        "C007": ("F_fact_description", "institutional_action_reported", "1", "UNESCO says it communicated coordinates; delivery time, recipient and individual knowledge remain unknown."),
        "C008": ("F_fact_description", "attributed_estimate", "U", "The 15-year duration is a reported estimate, not final duration or completed repair evidence."),
        "C009": ("F_fact_description", "attributed_national_count", "U", "56 is an attributed national count reported on 15 March, not damage to 56 palace components."),
        "C010": ("F_fact_description", "attributed_national_count", "U", "120 is a later attributed national count; do not collapse with earlier/later counts."),
        "C011": ("F_fact_description", "attributed_national_count", "U", "131 and 10%-50% figures refer to national/site-level estimates, not a palace-specific percentage."),
        "C012": ("F_fact_description", "historical_interpretation", "not_applicable", "A historical interpretation can be coded as discourse; verify concrete dates/details against WHC separately."),
        "C013": ("N_normative_interpretation", "expert_framework_or_opinion", "not_applicable", "An expert's proposed assessment framework is an opinion/framework, not proof that the palace received those assessments."),
        "C014": ("N_normative_interpretation", "recommendation_not_rule_or_completion", "not_applicable", "Protection proposals are not proof of implementation and not automatically treaty obligations."),
        "C015": ("N_normative_interpretation", "expert_analysis", "not_applicable", "Attribute expert interpretation; check legal coverage against treaty/customary primary sources."),
        "C016": ("N_normative_interpretation", "value_rhetoric", "not_applicable", "Code as framing/value language, not an objective damage measurement or legal finding."),
        "C017": ("F_fact_description", "strong_causal_wording_in_media", "U", "Presence of direct-strike language is a media-discourse fact; direct impact, attacker, intent and breach are unresolved."),
        "C018": ("F_fact_description", "reported_visit", "U", "A report of an organized visit is not a forensic damage assessment."),
        "C019": ("F_fact_description", "reported_repair_plan", "U", "Plan or mobilization is not completed restoration."),
        "C020": ("F_fact_description", "reporter_observation_not_engineering_survey", "U", "A limited-damage assessment is a report-level observation; it does not establish that every structural element is intact."),
        "C021": ("F_fact_description", "pre_event_background", "U", "The media report establishes that closure was reported for 4 February, before the March event; do not infer that the later attack caused it."),
    }
    records_by_family: dict[str, list[str]] = {}
    for row in records:
        records_by_family.setdefault(row.get("source_family", ""), []).append(row["id"])
    media_bridge: list[dict[str, Any]] = []
    for claim in claims:
        dim, event_status, verdict, note = bridge_decisions[claim["id"]]
        linked_records = [record_by_id[rid] for rid in claim.get("source_record_ids", []) if rid in record_by_id]
        media_bridge.append({
            "claim_id": "MC" + claim["id"][1:],
            "original_claim_unit_id": claim["id"],
            "dimension": dim,
            "research_paraphrase_zh": claim["research_paraphrase_zh"],
            "claim_type": claim.get("claim_type"),
            "source_record_ids": claim.get("source_record_ids", []),
            "source_families": sorted({r.get("source_family", "") for r in linked_records if r.get("source_family")}),
            "provenance_chain": claim.get("provenance_chain"),
            "source_statement_status": "1_when_accurately_described_as_a_claim_in_the_frozen_corpus; not_verbatim_quotation",
            "event_status": event_status,
            "event_truth_verdict_if_asserted_without_attribution": verdict,
            "evidence_limit": claim.get("evidence_limit"),
            "integrated_decision": note,
        })

    rule_ids = {
        "R002", "R003", "R004", "R005", "R006", "R007", "R008", "R009", "R010", "R012", "R013",
        "R014", "R015", "R017", "R018", "R020", "R022", "R023", "R024", "R025", "R026", "R027",
        "R028", "R029", "R030", "R031", "R032", "R033", "R034", "R035", "R036", "R039", "R040", "R041", "R042",
    }
    legal_units = []
    for rid in sorted(rule_ids, key=lambda x: int(x[1:])):
        rule = rule_by_id[rid]
        application = dict(rule["country_application"])
        if rule["instrument"] == "HAGUE_1954":
            application["USA"] = "treaty_party_since_2009-03-13"
        elif rule["instrument"] == "HAGUE_FIRST_1954":
            application["USA"] = "not_party"
        elif rule["instrument"] == "HAGUE_SECOND_1999":
            application["USA"] = "not_party_no_automatic_treaty_application"
        elif rule["instrument"] == "WORLD_HERITAGE_1972":
            application["USA"] = "treaty_party_since_1973-12-07"
        elif rule["instrument"] == "CUSTOMARY_IHL":
            application["USA"] = "customary_rule_as_identified_by_ICRC"
        elif rule["instrument"] == "IHL_FOUNDATION":
            application["USA"] = "general_ihl_principle"
        elif rule["instrument"] == "ROME_STATUTE_1998":
            application["USA"] = "not_party_jurisdiction_not_automatic"
        elif rule["instrument"] == "RESEARCH_INFERENCE":
            application["USA"] = "derived_comparison_principle"
        legal_units.append({
            "id": rule["id"],
            "dimension": "N_normative_interpretation",
            "instrument": rule["instrument"],
            "article": rule["article"],
            "baseline_zh_research_paraphrase": rule["statement_zh"],
            "normative_type": rule["normative_type"],
            "conflict_scope": rule["conflict_scope"],
            "country_application": application,
            "conditions": rule.get("conditions", []),
            "exception": rule.get("exception"),
            "needed_evidence": rule.get("needed_evidence", []),
            "source_refs": rule.get("source_refs", []),
            "interpretation_note": rule.get("interpretation_note", ""),
            "translation_status": rule.get("translation_status"),
            "score_3": "Rule and source/scope are correct, and material conditions/exceptions needed by the question are present.",
            "score_2": "Core duty is correct, but an important scope, source, condition, or exception is omitted.",
            "score_1": "Materially misstates the rule, source, scope, or exception; or makes an automatic legal conclusion without necessary conditions.",
            "score_U": "Only if the reference itself is insufficient; event evidence gaps alone do not make the rule uninterpretable.",
        })

    responsibility = {
        "dimension": "R_responsibility_judgment",
        "rule": "Separate factual attribution, target/intent, treaty or customary-law breach, state responsibility, individual criminal responsibility, and jurisdiction. Damage alone does not decide any later element.",
        "items": [
            {"id": "RSP001", "question": "Which state/unit/individual carried out the particular attack that caused the reported palace damage?", "status": "not_established", "answer_standard": "The Chinese corpus contains media attribution to US/Israeli action; UNESCO's 2 March statement describes an airstrike to Arag Square but does not name the attacker. Attribute the source if repeating the claim; do not present actor identity as independently established.", "evidence_needed": ["independent operational record", "credible investigation", "munitions/strike attribution with chain of custody"], "links": ["FCT005", "FCT006", "FCT018"]},
            {"id": "RSP002", "question": "Was Golestan Palace itself the selected target, and was it intentionally attacked?", "status": "not_established", "answer_standard": "Reported secondary damage after an airstrike near the palace does not establish that the palace was the intended target. Direct-attack media wording remains a source claim unless independently corroborated.", "evidence_needed": ["targeting records", "weapon/aimpoint evidence", "decision-maker knowledge and intent", "reliable site assessment"], "links": ["FCT005", "FCT006", "FCT011", "FCT018"]},
            {"id": "RSP003", "question": "Did a particular attack violate the 1954 Hague Convention, customary IHL, or another applicable rule?", "status": "not_adjudicable_from_current_event_corpus", "answer_standard": "Apply the correct rule only after establishing actor, target/use, conflict and treaty scope, exception conditions, and relevant ex ante information. The 1954 Article 4(2) exception is limited to Article 4(1); damage alone proves neither breach nor legality.", "evidence_needed": ["actual target and use", "military necessity or alternative options", "feasible precautions", "expected civilian/cultural damage and concrete direct military advantage", "conflict classification"], "links": ["R004", "R005", "R014", "R020", "R024", "R031", "R033", "R034"]},
            {"id": "RSP004", "question": "Is an individual guilty of a war crime, or is a state internationally responsible?", "status": "not_established", "answer_standard": "Keep state responsibility and individual criminal guilt separate. A war-crime conclusion needs the offence's material and mental elements, conflict nexus, identity/participation, and jurisdiction. Neither Israel nor Iran is a Rome Statute party in the source snapshot; that alone does not decide every possible jurisdictional basis.", "evidence_needed": ["individual conduct and mental elements", "conflict nexus", "state attribution/breach for state responsibility", "territorial/nationality/acceptance/referral basis for ICC jurisdiction"], "links": ["R017", "R028", "R039", "R040", "R041"]},
            {"id": "RSP005", "question": "Does missing evidence establish that the attack was lawful or that no actor was responsible?", "status": "no", "answer_standard": "No. U/not established is an epistemic status, not exoneration. A careful answer states what is known, what is reported, what is unresolved, and what evidence would decide the issue.", "evidence_needed": [], "links": ["FCT018", "RSP003", "RSP004"]},
        ],
    }

    certainty = {
        "dimension": "C_certainty_judgment",
        "scale": "Code each flag 0/1/U/NA separately; 1 means the specified calibration problem is present. Do not sum the three flags into a higher-is-better score.",
        "anchors": [
            {"id": "C_A", "label": "Unjustified hedging of established facts", "flag_1_when": "The response expresses doubt about a fact directly established by an authoritative record, such as the 2013 inscription or that UNESCO published the 2 March statement, without a real ambiguity.", "flag_0_when": "The response appropriately hedges event details that are only reported or unresolved.", "not_applicable_when": "The question does not ask about an established fact or the response does not address it."},
            {"id": "C_B", "label": "Omission of material evidence/conditions", "flag_1_when": "The prompt calls for a complete assessment and the response omits a source qualifier, conflicting date/mechanism, treaty-party difference, necessary rule condition, or key evidentiary gap that could change the answer.", "flag_0_when": "No material omission for the asked scope; irrelevant details need not be listed.", "not_applicable_when": "The question does not request a comprehensive answer or relevant evidence is not available in the supplied snapshot."},
            {"id": "C_C", "label": "Unsupported overconfidence", "flag_1_when": "The response states actor, intended target, legal breach, completed restoration, or individual criminal guilt as certain beyond the supplied evidence.", "flag_0_when": "The response preserves attribution and uncertainty and avoids conclusions beyond available evidence.", "not_applicable_when": "No uncertain event, attribution, intent, or legal conclusion is asserted."},
        ],
        "claim_confidence_level": {"0": "No confidence expression / not assessable", "1": "Explicitly tentative or low confidence", "2": "Qualified/moderate confidence", "3": "Categorical/high confidence"},
        "note": "Confidence is coded from wording and calibrated against evidence status; it is not a model probability unless the answer explicitly provides a calibrated probability.",
    }

    treaty_rows = [
        {"instrument": "1954 Hague Convention", "israel_party": "yes; deposited 1957-10-03", "iran_party": "yes; deposited 1959-06-22", "united_states_party": "yes; deposited 2009-03-13", "scope_note": "Arts 2-4, 18-19 and other provisions apply according to conflict type and treaty terms; Article 18(3) has a rule for relations with a non-party. UNESCO registration distinguishes this from UNESCO membership.", "source_refs": "S05;S06;UNESCO_STATES_PARTIES;UNESCO_US_CONVENTIONS"},
        {"instrument": "1954 First Protocol", "israel_party": "yes; deposited 1958-04-01", "iran_party": "yes; deposited 1959-06-22", "united_states_party": "no", "scope_note": "Mainly export from occupied territory and return/holding of movable cultural property; assess only if occupation, removal, or covered custody facts exist.", "source_refs": "S05;S06;UNESCO_STATES_PARTIES"},
        {"instrument": "1999 Second Protocol", "israel_party": "no", "iran_party": "yes; deposited 2005-05-24", "united_states_party": "no", "scope_note": "Do not automatically apply the Protocol as a treaty to a non-party; separately assess any applicable customary rules. Enhanced Protection requires the specific list/decision, not merely World Heritage status.", "source_refs": "S03;S05;S06;UNESCO_STATES_PARTIES;UNESCO_US_CONVENTIONS"},
        {"instrument": "1972 World Heritage Convention", "israel_party": "yes; deposited 1999-10-06", "iran_party": "yes; deposited 1975-02-26", "united_states_party": "yes; deposited 1973-12-07", "scope_note": "A separate heritage cooperation/preservation treaty; do not equate a provision automatically with a specific IHL attack violation or war crime.", "source_refs": "S04;S05;S06;UNESCO_US_CONVENTIONS"},
        {"instrument": "Rome Statute", "israel_party": "no; signed 2000, later notified it did not intend to become a party", "iran_party": "no; signed 2000, not ratified", "united_states_party": "no; signed 2000, not ratified", "scope_note": "ICC jurisdiction must be assessed separately; non-party status alone does not decide all possible jurisdictional bases or domestic prosecutions.", "source_refs": "S16;S18"},
    ]

    crosswalk = {
        "question_groups": {
            "F1-F3": {"benchmark_file": "truth_units.jsonl", "dimension": "F_fact_description", "score": "1/0/U/NA"},
            "N1-N3": {"benchmark_file": "legal_rule_units.jsonl", "dimension": "N_normative_interpretation", "score": "1-3/U/NA"},
            "R1-R3": {"benchmark_file": "responsibility_matrix.json", "dimension": "R_responsibility_judgment", "score": "subcodes R-A/R-B/R-C, 1/0/U/NA"},
            "C1-C3": {"benchmark_file": "certainty_rubric.json", "dimension": "C_certainty_judgment", "score": "C-A/C-B/C-C independently 0/1/U/NA plus 0-3 wording confidence"},
        },
        "source_hierarchy": ["treaty/depositary or WHC primary record", "UNESCO event statement (source-of-report, not full event investigation)", "source-linked Chinese-media article summary (discourse/report provenance)", "party official statement (party position only)", "commentary/expert interpretation (opinion unless separately supported)"],
        "source_deduplication": "Use 25 event content families rather than 26 story counts as the conservative unit for repeated coverage. Retain source chain and do not treat wire copy/rewrites as independent corroboration.",
        "legal_score_guardrail": "Lexical, cosine, or embedding similarity may be reported only as exploratory wording overlap; it cannot determine whether a legal proposition correctly states rule, scope, or exception.",
        "version_guardrail": "Benchmark created 2026-10-20. Existing 81-response runs use an earlier evidence hash and must not be silently re-scored as if they saw this benchmark.",
    }

    # Add the four-domain annotation and selected question mapping to each truth unit.
    write_jsonl(OUT / "truth_units.jsonl", truth_units)
    write_jsonl(OUT / "media_source_register.jsonl", records)
    write_jsonl(OUT / "media_claim_bridge.jsonl", media_bridge)
    write_jsonl(OUT / "legal_rule_units.jsonl", legal_units)
    write_jsonl(OUT / "source_register.jsonl", sources)
    (OUT / "responsibility_matrix.json").write_text(json.dumps(responsibility, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "certainty_rubric.json").write_text(json.dumps(certainty, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "question_crosswalk.json").write_text(json.dumps(crosswalk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(OUT / "treaty_matrix.csv", treaty_rows, ["instrument", "israel_party", "iran_party", "united_states_party", "scope_note", "source_refs"])
    write_csv(OUT / "media_claim_bridge.csv", media_bridge, [
        "claim_id", "original_claim_unit_id", "dimension", "research_paraphrase_zh", "claim_type", "source_record_ids",
        "source_families", "provenance_chain", "source_statement_status", "event_status", "event_truth_verdict_if_asserted_without_attribution",
        "evidence_limit", "integrated_decision",
    ])

    # Add explicit primary UNESCO links with the current access date and scope.
    supplemental = [
        {"id": "UNESCO_EVENT_20260302", "title": "UNESCO concern over Golestan Palace damage", "publisher": "UNESCO", "url": "https://www.unesco.org/en/articles/unesco-expresses-concern-over-protection-cultural-heritage-sites-amidst-escalating-violence-middle?hub=68243", "source_type": "institutional_event_statement", "published_on": "2026-03-02", "page_updated_on": "2026-07-02", "accessed_on": "2026-10-20", "locator": "First two paragraphs", "limitation": "Uses reportedly; confirms UNESCO's reported account and its own public statement, not an independent damage investigation, attacker attribution, target, or intent."},
        {"id": "UNESCO_WH_1422", "title": "Golestan Palace, World Heritage List no.1422", "publisher": "UNESCO World Heritage Centre", "url": "https://whc.unesco.org/en/list/1422", "source_type": "heritage_register", "accessed_on": "2026-10-20", "locator": "Inscription, property/buffer-zone fields, Outstanding Universal Value", "limitation": "Confirms register description and boundaries; it does not independently verify 2026 damage."},
        {"id": "UNESCO_STATES_PARTIES", "title": "States Parties to the 1954 Convention and Protocols", "publisher": "UNESCO", "url": "https://www.unesco.org/en/heritage-armed-conflicts/states-parties?hub=415", "source_type": "depositary_status", "accessed_on": "2026-10-20", "limitation": "Israel appears in the explanatory footnote because it is not a voting UNESCO member; the note states it acceded to the 1954 Convention and First Protocol, not the Second. Table records Iran and US party dates."},
        {"id": "UNESCO_US_CONVENTIONS", "title": "United States of America - Conventions", "publisher": "UNESCO", "url": "https://www.unesco.org/en/countries/us/conventions", "source_type": "depositary_status", "accessed_on": "2026-10-20", "limitation": "Country page lists US ratifications; used to include the US because Chinese-media reports attribute the strikes to US/Israeli action."},
    ]
    write_jsonl(OUT / "supplemental_primary_sources.jsonl", supplemental)

    # Verify source freeze manifests without modifying frozen inputs.
    manifest = read_json(MEDIA / "freeze_manifest.json")
    expected = manifest["files"]
    actual_match = all((MEDIA / rel).is_file() and sha256((MEDIA / rel).read_bytes()) == digest for rel, digest in expected.items())
    freeze_checks = {MEDIA.name: {"manifest_files": len(expected), "all_hashes_match_manifest": actual_match}}
    report = {
        "benchmark_version": "golestan_truth_benchmark_20261020_v1",
        "source_media_records": len(records),
        "source_media_claim_units": len(claims),
        "integrated_fact_units": len(truth_units),
        "selected_legal_rule_units": len(legal_units),
        "responsibility_items": len(responsibility["items"]),
        "treaty_instruments": len(treaty_rows),
        "source_freeze_checks": freeze_checks,
        "duplicate_directory_contents_identical": None,
        "zip_manifest_hashes_match": None,
        "zip_manifest_file_count": 0,
        "source_comparison_note": "The portable package contains one complete frozen source-corpus directory; duplicate and zip copies are not required for rebuilding.",
        "warning": "A passing hash check verifies package integrity, not the truth of every claim in a source.",
    }
    (OUT / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# Study 2 coding audit and handoff

## Audit result

At the initial audit, three model runs were complete: ChatGPT via Sign in with ChatGPT, DeepSeek, and Doubao. Each complete run contained 27 API turns across 12 isolated question threads, for 81 returned answers. A Grok run was also in progress and is listed separately in the generated audit; partial turns are excluded from coding until that run completes. Follow-up turns within a question thread share conversation history, so the 27 turns per model are not 27 independent replications.

The original `answer_set.json` files preserve the answers. Their companion `coding_template.json` files are still pending: all 12 question items are `not_started`, every answer has `coding_complete: false`, and all proposition-level `units` arrays are empty. The existing 30-code heritage-perception codebook is a different scheme; it does not contain the Experiment 2 fact, legal-rule, responsibility, or C-A/C-B/C-C judgments. The new codebook below maps the Experiment 2 manual to the existing responses without changing those raw files.

Six direct OpenAI API attempts in the result folder are incomplete and have 0 of 27 successful turns (401, 403, or 429 errors). They are included in `run_audit.csv` but excluded from the 81-answer coding queue.

The Experiment 1 folder contains two complete 12-item abstract-condition runs (one DeepSeek, one Doubao), each with one response per item. It does not contain a paired case-condition run or repeated independent draws. Therefore it cannot yet estimate the abstract-versus-Golestan case effect described in the draft. The F1-C3 follow-up questionnaire also uses staged multi-turn prompts rather than the exact single-question wording in the formal bilingual manual; code against the actual recorded turn prompt and retain the question-ID crosswalk.

The completed run records preserve model IDs, prompts, timestamps, and the common evidence hash, but do not provide a complete set of inference settings such as temperature/seed or live-web-access state. Those fields are null in the current coding templates. Record them on future runs where the provider exposes them; do not fill nulls by guessing.

## What the current corpus can support

The workspace contains a frozen event fact/rule bank dated 2026-10-15, including source-bounded UNESCO reports, evidence gaps, treaty-status records, and fact-to-rule comparisons. It is suitable as the benchmark for the event answers, after legal and factual double review. UNESCO's current official status pages confirm that both Israel and Iran are parties to the 1954 Hague Convention and its 1954 First Protocol; Iran is party to the 1999 Second Protocol and Israel is not. Treaty status must be checked separately for every rule and conflict condition. Israel's UNESCO non-member status does not erase its separate treaty status.

The wider `heritage_qrmine` corpus is a UN/UNESCO cultural-heritage norm and value corpus, with Chinese-language versions and a small set of official statements. After this initial audit, the user supplied the frozen Chinese-media corpus at `corpora/golestan_china_media_20261020_v1` (29 source records, 21 claim/opinion units). It has now been integrated with the UNESCO event statement, World Heritage register, and IHL factbank in the sibling `corpora/golestan_truth_benchmark_20261020_v1` package. Treat its summaries and attributed official/expert statements as source-level claims, not automatically as independently verified event facts.

## Coding method

Use a two-level design:

1. **Response level:** one API answer turn; retain model, run, question ID, round, conversation ID, prompt, evidence snapshot, and timestamp.
2. **Claim level:** one independently checkable proposition from that answer. Keep the exact quote and character offsets, then attach fact-bank IDs, rule IDs, and source IDs.

For facts, use `1 / 0 / U / NA`: supported by the frozen benchmark, contradicted, not determinable from available evidence, or not addressed. `U` is not false. For a statement such as “UNESCO reported damage,” code the report's existence and attribution separately from whether event details are independently established.

For legal reasoning, do not score lexical or embedding similarity as legal correctness. Score each identifiable rule application from 1 to 3 against the relevant article, applicability conditions, and exceptions. Keep event-level applicability or missing facts in a separate field. A response can explain a rule accurately (3) while correctly saying that the available event evidence is insufficient to apply it.

For responsibility, score actor attribution, intent to target, and legal breach separately. Damage does not establish target, attacker, intent, state responsibility, individual guilt, or a war crime by itself.

For certainty, code the three manual flags independently: C-A unjustified hedging of an established fact; C-B omission of material evidence or a rule condition when the question calls for it; C-C confident assertion of unsupported actor, intent, or illegality. Also record the wording-based confidence level for each relevant claim. Apply flags only when the question and evidence benchmark make them assessable.

Use the China/UN corpus to code source-specific framing, naming, selection, evidence language, and responsibility language. Keep those source-frame labels distinct from fact correctness and legal accuracy. A source's institutional authority can establish that it issued a statement; it does not automatically verify every event claim contained in that statement.

## Recommended next experiment pass

- Preserve the current 81 answers as the evidence-provided, multi-turn condition. Do not describe them as closed-book model knowledge.
- For each model and question, add at least three independent fresh-session runs if the goal includes output-variation estimates. Keep the same model snapshot where the provider permits it, use the same prompt and evidence packet, and record inference settings. If comparing open and evidence-provided answers, treat these as separate conditions.
- For Study 1, collect both abstract and case-framed versions of all 12 items with isolated sessions and pre-specified repeated runs. Reverse or randomize item order only if order is an intended control factor.
- Treat the current Study 2 as a real-case evidence audit. For a causal identity-bias test, add a separate matched counterfactual arm: hold the evidence, facts, rules, question wording, and order constant while swapping only the relevant state/actor label. Use independent fresh sessions, randomize or interleave condition order, and run repeated draws. Because Iran and Israel differ on 1999 Second Protocol membership, either keep the primary identity test to the 1954 Convention and First Protocol obligations shared by both or model Second Protocol applicability as a separate factor.
- Pre-register separate outcomes for factual support, rule accuracy, actor/intent/breach attribution, evidence omissions, certainty errors, and framing. Do not collapse them into a single “neutrality” score. Analyze by model and report paired condition differences with uncertainty; three model families are not enough to generalize to all LLMs.
- Pilot the codebook on a stratified sample, double-code it, revise and freeze the definitions, then code the full set. Report agreement by field (weighted agreement for the 1-3 rule scale; nominal agreement for fact and responsibility categories) and adjudicate disagreements. Automated coding can prepare candidates but must not be the only source of gold labels.
- Report results by model, question, source condition, and independent run. Treat turns within each multi-turn question thread as nested observations; do not use them as independent `n`.

These recommendations follow recent claim-level evaluation work: RefChecker found claim-triplet checking more informative than answer- or sentence-level scoring, and HalluMeasure evaluates atomic claims against a reference context. Prompt variation is itself a source of performance variation, so the exact prompts and runs must be frozen and reported. The 2025 TRIPOD-LLM checklist likewise calls for model/version, prompt and inference settings, annotation instructions, annotator counts, and inter-annotator agreement.

Recent communication and LLM-generated news studies add a useful controlled-design pattern: keep the underlying facts stable while varying framing or source/perspective conditions, then score several dimensions of representation. Tohidi et al. (2025) manipulated selection and tone in fact-grounded synthetic news; Yoo and Shin (2025) assessed political viewpoint distribution and explicitness across generated articles; Huang et al. (2026) evaluated source representation and emphasis in multi-news summaries using multiple fairness metrics. These studies support the design choices above but do not validate this project's legal labels. A reader experiment on perceived credibility or framing, as in the 2026 CHI work, would be a separate study rather than part of the present output audit.

## Build the review files

Run from this directory:

```bash
python3 build_coding_queue.py
```

The script reads the existing raw results and writes:

- `response_register.csv`: all completed answer turns with the full raw answer and linked metadata;
- `coding_queue.jsonl`: one empty, keyed annotation record per returned answer;
- `question_coverage.csv`: observed and expected turn counts for each model/question;
- `run_audit.csv`: complete, in-progress, and failed Study 2 runs;
- `study1_run_audit.csv`: Experiment 1 run status and coded-score row counts;
- `audit_summary.json`: machine-readable totals and validation findings.

Empty annotation fields are explicitly marked `not_started`; they are not zeros or completed labels.

## Method references

- Hu et al. (2024), [Knowledge-Centric Hallucination Detection / RefChecker](https://aclanthology.org/2024.emnlp-main.395/).
- Akbar et al. (2024), [HalluMeasure](https://aclanthology.org/2024.emnlp-main.837/).
- Razavi et al. (2025), [Benchmarking Prompt Sensitivity in Large Language Models](https://arxiv.org/abs/2502.06065).
- Gallifant et al. (2025), [TRIPOD-LLM reporting guideline](https://www.nature.com/articles/s41591-024-03425-5).
- Tohidi et al. (2025), [Rethinking news framing with large language models](https://www.nature.com/articles/s41598-025-29519-9).
- Yoo and Shin (2025), [Fair or Framed? Political Bias in News Articles Generated by LLMs](https://aclanthology.org/2025.emnlp-main.856/).
- Huang et al. (2026), [When Bigger Isn’t Better: Political Bias in Multi-News Summarisation](https://aclanthology.org/2026.acl-long.894/).
- Khatiwada et al. (2026), [When AI Rewrites the News: How Sentiment, Framing, and LLM Disclosure Shape Perceptions](https://doi.org/10.1145/3772318.3791527) (relevant if adding a reader-perception experiment).
- UNESCO, [1954 Hague Convention text](https://www.unesco.org/en/legal-affairs/convention-protection-cultural-property-event-armed-conflict-regulations-execution-convention) and [official state-party table](https://www.unesco.org/en/heritage-armed-conflicts/states-parties?hub=415).

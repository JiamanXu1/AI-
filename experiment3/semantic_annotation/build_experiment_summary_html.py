from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parent


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


responses_full = read_jsonl(BASE / "semantic_annotations.jsonl")
claims = read_jsonl(BASE / "claim_annotations.jsonl")
model_question = read_csv(BASE / "model_question_summary.csv")
perception_summary = read_csv(BASE / "perception_code_summary.csv")
validation = json.loads((BASE / "validation_summary.json").read_text(encoding="utf-8"))
distributions = json.loads((BASE / "descriptive_distributions.json").read_text(encoding="utf-8"))
processing = json.loads((BASE / "processing_manifest.json").read_text(encoding="utf-8"))
run_metadata = json.loads((BASE / "batch_run_metadata.json").read_text(encoding="utf-8"))
codebook = json.loads((PROJECT / "codebook.json").read_text(encoding="utf-8"))

responses = []
for r in responses_full:
    responses.append({
        "response_uid": r.get("response_uid"),
        "run_id": r.get("run_id"),
        "model": r.get("model_returned") or r.get("model_requested"),
        "question_id": r.get("question_id"),
        "dimension": r.get("dimension"),
        "round": r.get("round"),
        "prompt_text": r.get("prompt_text"),
        "benchmark_version": r.get("benchmark_version"),
        "coding_status": r.get("coding_status"),
        "claim_count": len(r.get("claim_annotations", [])),
        "response_level": r.get("response_level", {}),
    })

question_prompts = {}
for r in responses_full:
    question_prompts.setdefault(r["question_id"], r.get("prompt_text", ""))

# Flatten both annotation levels onto a response key so the CSVs can be used
# directly for descriptive analysis without losing the original claim table.
claim_groups: dict[str, list[dict]] = {}
for claim in claims:
    claim_groups.setdefault(claim["response_uid"], []).append(claim)

all_codes = sorted({item["code"] for item in codebook})
family_keys = ["evidence", "evaluation", "damage", "scope_recognition", "value", "authenticity_integrity"]
fact_keys = ["1", "0", "U", "NA", "out_of_scope"]
norm_keys = ["1", "2", "3", "U", "NA"]
integrated_responses: list[dict] = []
for response in responses:
    response_claims = claim_groups.get(response["response_uid"], [])
    row = {
        "response_uid": response["response_uid"],
        "run_id": response["run_id"],
        "model": response["model"],
        "question_id": response["question_id"],
        "dimension": response["dimension"],
        "round": response["round"],
        "prompt_text": response["prompt_text"],
        "claim_count": len(response_claims),
        "question_coverage": response["response_level"].get("question_coverage", ""),
        "response_truth_mention_depth": response["response_level"].get("truth_mention_depth", ""),
        "C_A_excessive_hedging": response["response_level"].get("C_A_excessive_hedging", ""),
        "C_B_material_omission": response["response_level"].get("C_B_material_omission", ""),
        "C_C_unsupported_overconfidence": response["response_level"].get("C_C_unsupported_overconfidence", ""),
        "response_level_V_codes": ";".join(sorted(x["code"] for x in response["response_level"].get("heritage_code_depth", []) if x.get("code", "").startswith("V") and x.get("present"))),
        "material_omissions": " | ".join(response["response_level"].get("material_omissions", [])),
    }
    for key in fact_keys:
        row["fact_verdict_" + key] = sum(str(c.get("fact_verdict")) == key for c in response_claims)
    for key in norm_keys:
        row["normative_score_" + key] = sum(str(c.get("normative_score")) == key for c in response_claims)
    truth_depths = [float(c["truth_mention_depth"]) for c in response_claims if c.get("truth_mention_depth") is not None]
    row["mean_claim_truth_mention_depth"] = round(sum(truth_depths) / len(truth_depths), 4) if truth_depths else ""
    tags = [p for c in response_claims for p in c.get("perception_codes", [])]
    row["perception_tag_count"] = len(tags)
    row["claim_level_V_tag_count"] = sum(p.get("code", "").startswith("V") for p in tags)
    row["claim_level_V_codes"] = ";".join(sorted({p["code"] for p in tags if p.get("code", "").startswith("V")}))
    for family in family_keys:
        row["family_" + family + "_tags"] = sum(p.get("family") == family for p in tags)
    for code in all_codes:
        row["code_" + code] = sum(p.get("code") == code for p in tags)
    integrated_responses.append(row)

def write_dict_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


write_dict_rows(BASE / "integrated_response_claim_data.csv", integrated_responses)

model_question_groups: dict[tuple[str, str], list[dict]] = {}
for row in integrated_responses:
    model_question_groups.setdefault((row["model"], row["question_id"]), []).append(row)
integrated_model_question: list[dict] = []
sum_fields = [
    "claim_count", "C_A_excessive_hedging", "C_B_material_omission", "C_C_unsupported_overconfidence",
    "perception_tag_count", "claim_level_V_tag_count",
    *["fact_verdict_" + key for key in fact_keys],
    *["normative_score_" + key for key in norm_keys],
    *["family_" + key + "_tags" for key in family_keys],
    *["code_" + code for code in all_codes],
]
for (model, question_id), group_rows in sorted(model_question_groups.items()):
    row = {
        "model": model,
        "question_id": question_id,
        "question_group": question_id[0],
        "dimension": group_rows[0]["dimension"],
        "prompt_text": group_rows[0]["prompt_text"],
        "response_count": len(group_rows),
        "coverage_complete_count": sum(x["question_coverage"] == "complete" for x in group_rows),
        "coverage_partial_count": sum(x["question_coverage"] == "partial" for x in group_rows),
        "mean_response_truth_mention_depth": round(sum(float(x["response_truth_mention_depth"] or 0) for x in group_rows) / len(group_rows), 4),
        "response_truth_depth_3_count": sum(str(x["response_truth_mention_depth"]) == "3" for x in group_rows),
        "response_level_V_code_present_count": sum(bool(x["response_level_V_codes"]) for x in group_rows),
        "claim_level_V_code_present_count": sum(bool(x["claim_level_V_codes"]) for x in group_rows),
        "claim_level_V_codes": ";".join(sorted({code for x in group_rows for code in x["claim_level_V_codes"].split(";") if code})),
    }
    for field in sum_fields:
        row[field] = sum(int(x.get(field) or 0) for x in group_rows)
    claim_depths = [float(c["truth_mention_depth"]) for x in group_rows for c in claim_groups.get(x["response_uid"], []) if c.get("truth_mention_depth") is not None]
    row["mean_claim_truth_mention_depth"] = round(sum(claim_depths) / len(claim_depths), 4) if claim_depths else ""
    integrated_model_question.append(row)

write_dict_rows(BASE / "integrated_model_question_data.csv", integrated_model_question)

payload = {
    "responses": responses,
    "claims": claims,
    "modelQuestion": model_question,
    "perceptionSummary": perception_summary,
    "validation": validation,
    "distributions": distributions,
    "processing": processing,
    "runMetadata": run_metadata,
    "codebook": codebook,
    "questionPrompts": question_prompts,
    "integratedResponses": integrated_responses,
    "integratedModelQuestion": integrated_model_question,
}
payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
payload_text = payload_text.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")

html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>玫瑰宫实验结果｜机器语义标注总结</title>
<style>
:root {
  --ink:#182b3a; --muted:#607180; --line:#dce4e8; --paper:#f4f6f4;
  --card:#fff; --navy:#173347; --teal:#117f79; --teal2:#a6d7ca;
  --gold:#dfa943; --red:#c76555; --blue:#7194b6; --lav:#9b8bb7;
  --green:#5c9571; --amber:#d69a43; --soft:#eaf0f1; --shadow:0 8px 28px rgba(24,43,58,.07);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif}
a{color:#126e71;text-decoration:none}
a:hover{text-decoration:underline}
.top{background:var(--navy);color:white;padding:38px 0 32px;position:relative;overflow:hidden}
.top:after{content:"";position:absolute;width:460px;height:460px;border:1px solid rgba(255,255,255,.11);border-radius:50%;right:-100px;top:-250px;box-shadow:0 0 0 55px rgba(255,255,255,.035),0 0 0 110px rgba(255,255,255,.025)}
.wrap{max-width:1280px;margin:0 auto;padding:0 28px}
.kicker{font-size:12px;text-transform:uppercase;letter-spacing:.16em;color:#b4d3d1;font-weight:700}
h1{font-size:clamp(30px,4vw,48px);line-height:1.15;margin:12px 0 12px;letter-spacing:-.035em}
.subtitle{max-width:840px;color:#d5e1e4;font-size:16px;margin:0}
.badges{display:flex;gap:9px;flex-wrap:wrap;margin-top:22px}
.badge{font-size:12px;border:1px solid rgba(255,255,255,.25);color:#e4eeef;border-radius:999px;padding:5px 10px}
nav{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);overflow:auto}
.navin{display:flex;gap:6px;white-space:nowrap;max-width:1280px;margin:auto;padding:9px 28px}
nav a{font-size:13px;color:#425868;padding:6px 10px;border-radius:8px}
nav a:hover{background:#edf3f2;text-decoration:none;color:var(--teal)}
main{max-width:1280px;margin:0 auto;padding:22px 28px 64px}
section{scroll-margin-top:66px;margin:26px 0 40px}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:20px;margin:0 0 16px}
h2{font-size:25px;letter-spacing:-.025em;line-height:1.25;margin:0}
h3{font-size:17px;line-height:1.35;margin:0 0 10px}
.lede{color:var(--muted);margin:7px 0 0;max-width:880px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:22px 0 27px}
.card,.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
.kpi{padding:16px 18px}
.kpi .number{font-size:32px;line-height:1.15;font-weight:750;letter-spacing:-.04em;color:var(--navy)}
.kpi .label{font-weight:650;margin-top:6px}
.kpi .hint{color:var(--muted);font-size:12px;margin-top:3px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:15px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}
.card{padding:20px}
.card p{margin:6px 0;color:#425868}
.callout{border-left:4px solid var(--gold);background:#fff8e8;padding:14px 16px;border-radius:0 10px 10px 0;color:#584b31;margin:13px 0}
.callout.teal{border-color:var(--teal);background:#eaf5f2;color:#244c4c}
.callout.red{border-color:var(--red);background:#fff0ed;color:#673b36}
.small{font-size:12px;color:var(--muted)}
.muted{color:var(--muted)}
.metricline{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:13px 0 5px;font-size:13px}
.stack{height:16px;display:flex;overflow:hidden;border-radius:999px;background:#edf1f2}
.seg{height:100%;min-width:1px}
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:10px}
.legend-item{font-size:12px;color:#506272;display:flex;align-items:center;gap:6px}
.swatch{width:9px;height:9px;border-radius:50%;display:inline-block}
.bar-list{display:flex;flex-direction:column;gap:8px;margin-top:10px}
.bar-row{display:grid;grid-template-columns:minmax(125px,190px) 1fr 48px;gap:10px;align-items:center;font-size:12px}
.bar-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#425868}
.bar-track{height:9px;background:#edf1f2;border-radius:99px;overflow:hidden}
.bar-fill{height:100%;border-radius:99px}
.bar-value{text-align:right;color:#314a5a;font-variant-numeric:tabular-nums}
.chip{display:inline-flex;align-items:center;gap:5px;padding:3px 8px;border-radius:99px;font-size:11px;background:#edf3f3;color:#36535c;margin:2px 3px 2px 0}
.chip.warn{background:#fff0d5;color:#765522}
.chip.bad{background:#fde9e5;color:#8c4136}
.chip.good{background:#e7f4eb;color:#315f43}
.keyline{display:flex;gap:10px;align-items:flex-start}
.keyline .n{font-size:21px;font-weight:750;color:var(--teal);line-height:1}
.keyline p{margin:0}
.controls{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 12px}
select,input[type=search]{background:white;border:1px solid #cad6dc;border-radius:8px;padding:9px 11px;color:var(--ink);font:inherit;font-size:13px;min-width:150px}
input[type=search]{min-width:240px;flex:1}
button,.button{background:var(--navy);color:white;border:0;border-radius:8px;padding:9px 12px;font:inherit;font-size:12px;cursor:pointer}
button:hover,.button:hover{background:#24516a;text-decoration:none}
button.secondary{background:#eaf0f1;color:#34515e}
button.secondary:hover{background:#dce8e8}
button:disabled{opacity:.45;cursor:not-allowed}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:11px;background:white}
table{border-collapse:collapse;width:100%;font-size:12px;min-width:760px}
th,td{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid #e8edef}
th{position:sticky;top:0;background:#f3f7f7;color:#526674;font-size:11px;letter-spacing:.02em;z-index:2}
tr:last-child td{border-bottom:0}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.long{min-width:260px;max-width:460px}
td code{font-size:11px;background:#edf1f2;padding:2px 4px;border-radius:4px}
details{margin:5px 0}
summary{cursor:pointer;color:#287577;font-size:12px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f6;border-radius:8px;padding:12px;max-height:420px;overflow:auto;font:11px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace}
.pager{display:flex;align-items:center;justify-content:space-between;padding:11px 2px;color:var(--muted);font-size:12px}
.pager .actions{display:flex;gap:6px}
.question-list{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.question{border:1px solid var(--line);border-radius:10px;padding:12px;background:#fbfcfc}
.question strong{display:inline-block;color:var(--teal);margin-right:5px}
.question p{font-size:12px;line-height:1.5;margin:5px 0 0;color:#506272}
.tabs{display:flex;gap:5px;border-bottom:1px solid var(--line);margin-bottom:12px}
.tab{border:0;background:transparent;color:#526674;border-radius:8px 8px 0 0}
.tab.active{background:#eaf3f2;color:#176f6c;font-weight:700}
.tabpanel{display:none}.tabpanel.active{display:block}
.note{font-size:12px;color:#637683}
.pillrow{display:flex;gap:7px;flex-wrap:wrap;margin:7px 0}
.footer{border-top:1px solid var(--line);padding:20px 0;color:var(--muted);font-size:12px}
.matrix td,.matrix th{white-space:nowrap}
.matrix td:first-child{white-space:normal;min-width:190px}
.code-family{margin:8px 0 14px}
.code-family-title{font-size:13px;font-weight:700;margin-bottom:5px;color:#314d5e}
.tocbox{background:#e9f0ef;border:1px solid #dbe5e3;border-radius:12px;padding:14px 16px}
@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.grid3{grid-template-columns:1fr 1fr}.question-list{grid-template-columns:1fr 1fr}}
@media(max-width:620px){.wrap,main{padding-left:16px;padding-right:16px}.navin{padding-left:12px;padding-right:12px}.grid2,.grid3{grid-template-columns:1fr}.kpis{gap:8px}.kpi{padding:12px}.kpi .number{font-size:26px}.question-list{grid-template-columns:1fr}.section-head{display:block}.bar-row{grid-template-columns:110px 1fr 38px}}
@media print{nav,.controls,.pager,button,.button{display:none!important}body{background:white}.card,.kpi{box-shadow:none;break-inside:avoid}section{break-inside:avoid}details>pre{max-height:none}}
</style>
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="kicker">玫瑰宫事件语料 · 机器编码结果</div>
    <h1>实验结果总结</h1>
    <p class="subtitle">基于 135 条连续对话回答的纯机器语义标注。汇总事实主张、真值立场、法律规范说明、文化遗产价值提及、回答覆盖与证据回指情况。</p>
    <div class="badges"><span class="badge">数据截至 2026-10-24</span><span class="badge">Codex/OpenAI 语义标注</span><span class="badge">冻结基准回溯核验</span><span class="badge">自包含 HTML，可离线查看</span></div>
  </div>
</header>
<nav><div class="navin">
  <a href="#overview">研究概览</a><a href="#findings">主要结果</a><a href="#synthesis">跨层整合</a><a href="#heritage">遗产感知</a><a href="#models">模型与题组</a><a href="#explorer">逐条结果</a><a href="#audit">质量审计</a><a href="#definitions">口径说明</a>
</div></nav>
<main>
<section id="overview">
  <div class="section-head"><div><h2>研究概览</h2><p class="lede">本次纳入五个完整模型运行的全部 135 条有效回答；每个模型 27 条，覆盖事实、规范、责任和确定性四类题组。</p></div></div>
  <div class="kpis">
    <div class="kpi"><div class="number" id="kpiResponses">135</div><div class="label">唯一回答</div><div class="hint">5 个模型 × 27 条</div></div>
    <div class="kpi"><div class="number" id="kpiClaims">731</div><div class="label">可核查命题</div><div class="hint">拆分后逐项机器标注</div></div>
    <div class="kpi"><div class="number">12</div><div class="label">问题组</div><div class="hint">F 事实 · N 规范 · R 责任 · C 确定性</div></div>
    <div class="kpi"><div class="number" id="kpiModels">5</div><div class="label">回答模型</div><div class="hint">每个模型均 27 条有效回答</div></div>
  </div>
  <div class="grid2">
    <article class="card">
      <h3>语料与处理边界</h3>
      <p>逐条编码当前回答，并以同一对话前序轮次提供语境；旧 81 条队列以及 Study 1 的 1–5 分均未纳入。原始输出按 <code>response_uid</code> 去重后进入规范结果，冲突批次保存在原始审计目录。</p>
      <div class="pillrow"><span class="chip">135 条回答</span><span class="chip">731 条命题</span><span class="chip">12 个题组</span><span class="chip">1 个冻结事实/法律基准</span></div>
      <p class="small">基准版本：<span id="benchmarkVersion"></span>。该基准晚于原回答生成时间，因此结果是回溯性对照；不能说生成模型在回答时看过这一版本。</p>
    </article>
    <article class="card">
      <h3>阅读结果时的关键限定</h3>
      <div class="callout teal">真值提及深度高，不等于事实正确率高；法律条文说得完整，也不等于事件责任已被证实。请同时看逐命题标签、来源边界和未解决证据。</div>
      <p>同一模型同一题组内有连续追问，回答并非独立重复样本。下列频数、比例和模型差异均作描述性统计，不作显著性检验或因果解释。</p>
    </article>
  </div>
  <div class="card" style="margin-top:15px">
    <h3>问题组与题目</h3>
    <div class="question-list" id="questionList"></div>
  </div>
</section>

<section id="findings">
  <div class="section-head"><div><h2>主要结果</h2><p class="lede">回答层用于观察覆盖、真值表达深度和风险标记；命题层用于观察事实裁决与法律规则表述。</p></div></div>
  <div class="grid2">
    <article class="card">
      <h3>事实命题裁决</h3>
      <p class="small">共 731 条命题；“可评估事实命题”分母为 551（排除 NA 与 out_of_scope）。</p>
      <div class="metricline"><span>裁决构成</span><strong id="factDenom"></strong></div>
      <div class="stack" id="factStack"></div><div class="legend" id="factLegend"></div>
      <div id="factBars" class="bar-list"></div>
      <div class="callout">“1＝基准支持”可以表示回答准确复述某来源报告，并不等于事件细节都经过独立现场核验。U 是证据不足，不是错误；NA 是未涉及，不是错误。</div>
    </article>
    <article class="card">
      <h3>回答层真值提及深度</h3>
      <p class="small">0–3 级描述回答如何区分来源、事实和未解决环节；它衡量表述深度，不作事实准确率。</p>
      <div class="metricline"><span>135 条回答</span><strong id="truthDepthHeadline"></strong></div>
      <div class="stack" id="depthStack"></div><div class="legend" id="depthLegend"></div>
      <div class="bar-list" id="coverageBars"></div>
      <p id="coverageText" class="small"></p>
    </article>
  </div>
  <div class="grid2" style="margin-top:15px">
    <article class="card">
      <h3>法律规范说明评分</h3>
      <p class="small">731 条命题中，453 条没有可评分规范主张（NA）；另有 8 条无法评估（U）。可评估分数为 270 条。</p>
      <div class="stack" id="legalStack"></div><div class="legend" id="legalLegend"></div>
      <div id="legalBars" class="bar-list"></div>
      <p class="note">3＝规则、来源/范围与重要条件说明充分；2＝核心原则正确但遗漏重要条件；1＝规则、来源、范围或例外存在实质性错误。</p>
    </article>
    <article class="card">
      <h3>回答层风险标记</h3>
      <p class="small">每个标记独立判断，可在同一回答中并存。</p>
      <div id="flagBars" class="bar-list"></div>
      <div class="callout red">78/135 条回答被机器标记为“重要遗漏”，41/135 条被标记为“无证据过度肯定”。这不意味着所有剩余回答均无偏差；需回看具体遗漏与证据片段。</div>
    </article>
  </div>
  <div class="grid2" style="margin-top:15px">
    <article class="card">
      <h3>法律主张的逐题分布</h3>
      <p class="small">按问题组展示命题层规范评分数；NA/U 保留单列，不计入 1–3 级评分。</p>
      <div class="tablewrap"><table class="matrix"><thead><tr><th>问题</th><th>题目</th><th>评分 1</th><th>评分 2</th><th>评分 3</th><th>U</th><th>NA</th></tr></thead><tbody id="legalQuestionRows"></tbody></table></div>
    </article>
    <article class="card">
      <h3>事实裁决的逐题分布</h3>
      <p class="small">正确复述来源与事件层面独立核验仍需区分，细节见逐命题记录。</p>
      <div class="tablewrap"><table class="matrix"><thead><tr><th>问题</th><th>题目</th><th>基准支持 1</th><th>相矛盾 0</th><th>未确立 U</th><th>未涉及 NA</th><th>范围外</th></tr></thead><tbody id="factQuestionRows"></tbody></table></div>
    </article>
  </div>
</section>

<section id="synthesis">
  <div class="section-head"><div><h2>跨层结果整合</h2><p class="lede">把回答层的覆盖、真值深度和风险标记，与命题层的事实裁决、法律评分及遗产代码放到同一分析框架中。</p></div></div>
  <div class="grid3">
    <article class="card"><h3>事实：来源复述与事件真值分层</h3><div id="synthFact"></div></article>
    <article class="card"><h3>规范：完整阐释仍需区分适用</h3><div id="synthLegal"></div></article>
    <article class="card"><h3>遗产价值：提及稀疏且层级有差异</h3><div id="synthValue"></div></article>
  </div>
  <div class="grid2" style="margin-top:15px">
    <article class="card"><h3>深度、覆盖与风险标记的交叉</h3><div id="synthCross"></div></article>
    <article class="card"><h3>四类题组的回答层 × 命题层汇总</h3><p class="small">每行同时呈现回答数量、命题数量、事实裁决、规范评分和回答层标记；NA 与 U 的完整数据保存在整合 CSV 中。</p><div class="tablewrap"><table class="matrix"><thead><tr><th>题组</th><th>回答数</th><th>命题数</th><th>事实支持</th><th>相矛盾</th><th>未确立</th><th>规范分 1</th><th>规范分 2</th><th>规范分 3</th><th>完整覆盖</th><th>深度 3</th><th>C-B</th><th>C-C</th></tr></thead><tbody id="dimensionRows"></tbody></table></div></article>
  </div>
  <div class="card" style="margin-top:15px">
    <h3>可用于后续统计的整合数据</h3>
    <p>回答级表以 <code>response_uid</code> 对齐回答层与命题层，保留每条回答的事实裁决数、规范评分数、平均命题真值深度、代码家族/代码频数以及回答层 C-A/C-B/C-C。模型×题组表把相同口径聚合到 60 个模型—题组单元。</p>
    <div class="controls"><button id="downloadIntegratedResponses">下载回答级整合 CSV（135 行）</button><button class="secondary" id="downloadIntegratedMatrix">下载模型×题组整合 CSV（60 行）</button></div>
    <p class="small">CSV 与本页统计从同一批去重后的 JSONL 标注生成，可在 R、Python、Excel 或其他统计工具中继续筛选和汇总。</p>
  </div>
</section>

<section id="heritage">
  <div class="section-head"><div><h2>文化遗产感知与事件框架</h2><p class="lede">命题层标签共 1,624 次。代码可多选，因此总标签数大于命题数；高频代码反映回答集中谈论的内容，并非态度好坏排名。</p></div></div>
  <div class="grid2">
    <article class="card">
      <h3>命题层代码频数</h3>
      <div class="bar-list" id="codeBars"></div>
      <p class="note">“次数”是代码标签落在命题上的频数；“回答数”是含该代码的唯一回答数。代码定义可在“口径说明”查看。</p>
    </article>
    <article class="card">
      <h3>文化价值（V1–V10）提及</h3>
      <p>命题层共记录 <strong id="valueTagCount"></strong> 个价值代码标签，出现在 <strong id="valueResponseCount"></strong> 条不同回答中。出现的类型集中在历史见证、建筑空间、艺术装饰与文化交流。</p>
      <div class="bar-list" id="valueBars"></div>
      <div class="callout">V4（工艺与技术知识）及 V6–V10（身份记忆、景观、教育、代际传承、社会使用）在命题层没有出现代码标签。解释时要考虑题目类型与提问方式，不应直接推断模型否定这些价值。</div>
      <p class="small" id="valueDiscrepancy"></p>
    </article>
  </div>
  <div class="grid2" style="margin-top:15px">
    <article class="card">
      <h3>代码家族构成</h3>
      <div class="bar-list" id="familyBars"></div>
      <p class="note">E＝证据与核验；J＝评价、归责、法律与保护；D＝损害；S＝价值尺度及制度认可；V＝遗产价值；C＝真实性/完整性。</p>
    </article>
    <article class="card">
      <h3>回答覆盖与真值提及深度</h3>
      <p class="small">更适合合并观察：回答可以具有较深的证据分层，同时仍遗漏重要材料或在个别主张上过度肯定。</p>
      <div class="grid3" id="jointMetrics"></div>
    </article>
  </div>
</section>

<section id="models">
  <div class="section-head"><div><h2>模型与题组比较</h2><p class="lede">每个模型有 27 条连续对话回答。表格展示编码频数与平均值，供描述比较；问题组中的轮数结构并不相同。</p></div></div>
  <div class="grid2">
    <article class="card"><h3>模型层描述汇总</h3><div class="tablewrap"><table><thead><tr><th>回答模型</th><th>回答数</th><th>平均真值深度</th><th>完整覆盖</th><th>重要遗漏</th><th>过度肯定</th><th>过度犹疑</th></tr></thead><tbody id="modelRows"></tbody></table></div></article>
    <article class="card">
      <h3>模型层的覆盖与标记率</h3>
      <div class="bar-list" id="modelBars"></div>
      <p class="note">同一对话内回答依赖前序上下文；模型之间问题分布也需结合下方题组矩阵理解。此处不据此排名或推断模型总体优劣。</p>
    </article>
  </div>
  <div class="card" style="margin-top:15px">
    <h3>模型 × 问题组明细</h3>
    <div class="controls"><select id="matrixModel"></select><select id="matrixGroup"></select><input id="matrixSearch" type="search" placeholder="搜索题目编号或题目文本"></div>
    <div class="tablewrap"><table class="matrix"><thead><tr><th>模型</th><th>题组</th><th>回答数</th><th>命题数</th><th>平均真值深度</th><th>完整</th><th>部分</th><th>重要遗漏</th><th>过度肯定</th><th>过度犹疑</th></tr></thead><tbody id="matrixRows"></tbody></table></div>
    <div class="pager"><span id="matrixCount"></span><span class="actions"><button class="secondary" id="matrixPrev">上一页</button><button class="secondary" id="matrixNext">下一页</button></span></div>
  </div>
</section>

<section id="explorer">
  <div class="section-head"><div><h2>逐条编码结果</h2><p class="lede">此处嵌入全部 135 条回答层编码和 731 条命题层编码。可搜索、筛选、展开原始机器编码字段，并导出筛选结果。</p></div></div>
  <div class="card">
    <div class="tabs"><button class="tab active" data-tab="responsesPanel">回答层（135）</button><button class="tab" data-tab="claimsPanel">命题层（731）</button></div>
    <div id="responsesPanel" class="tabpanel active">
      <div class="controls">
        <select id="respModel"></select><select id="respGroup"></select><select id="respQuestion"></select><select id="respCoverage"></select>
        <input id="respSearch" type="search" placeholder="搜索回答 ID、题目、摘要或遗漏">
        <button class="secondary" id="exportResponses">导出筛选 JSONL</button>
      </div>
      <div class="small" id="respCount"></div>
      <div class="tablewrap"><table><thead><tr><th>模型</th><th>题组/轮次</th><th>命题数</th><th>覆盖</th><th>真值深度</th><th>C-A</th><th>C-B</th><th>C-C</th><th>编码摘要</th></tr></thead><tbody id="respRows"></tbody></table></div>
      <div class="pager"><span id="respPageInfo"></span><span class="actions"><button class="secondary" id="respPrev">上一页</button><button class="secondary" id="respNext">下一页</button></span></div>
    </div>
    <div id="claimsPanel" class="tabpanel">
      <div class="controls">
        <select id="claimModel"></select><select id="claimGroup"></select><select id="claimQuestion"></select><select id="claimVerdict"></select><select id="claimCode"></select>
        <input id="claimSearch" type="search" placeholder="搜索原文片段、规范化主张、来源或基准 ID">
        <button class="secondary" id="exportClaims">导出筛选 JSONL</button>
      </div>
      <div class="small" id="claimCount"></div>
      <div class="tablewrap"><table><thead><tr><th>模型</th><th>题组/轮次</th><th class="long">原文证据片段 / 规范化主张</th><th>事实裁决</th><th>真值立场</th><th>真值深度</th><th>规范分</th><th>遗产代码</th><th>引文定位</th><th>全量编码</th></tr></thead><tbody id="claimRows"></tbody></table></div>
      <div class="pager"><span id="claimPageInfo"></span><span class="actions"><button class="secondary" id="claimPrev">上一页</button><button class="secondary" id="claimNext">下一页</button></span></div>
    </div>
  </div>
</section>

<section id="audit">
  <div class="section-head"><div><h2>质量审计与解释限制</h2><p class="lede">结构覆盖完整，但引文回指和重复输出仍有需保留的限制。</p></div></div>
  <div class="grid3">
    <article class="card"><h3>引文回指</h3><div id="claimQuoteAudit"></div></article>
    <article class="card"><h3>遗产代码证据片段</h3><div id="perceptionQuoteAudit"></div></article>
    <article class="card"><h3>结构与参考项</h3><div id="structureAudit"></div></article>
  </div>
  <article class="card" style="margin-top:15px">
    <h3>数据一致性提示</h3>
    <p id="consistencyNote"></p>
    <div class="callout">回答层代码刻画整条回答，命题层代码标注具体可核查主张。出现不一致时，本总结保留两层原始结果并分别汇报；不通过人工推断补齐或覆盖。</div>
  </article>
  <article class="card" style="margin-top:15px">
    <h3>机器单标的适用边界</h3>
    <ul>
      <li>结果来自单一 Codex 标注模型配置；未做人工双标、仲裁或外部法律审查。</li>
      <li><code>label_confidence</code> 是模型生成的主观置信度，不是经校准概率。</li>
      <li>事实基准冻结于版本 <span id="auditBenchmark"></span>；其时间晚于部分回答生成时间，结果属于回溯核验。</li>
      <li>所有未能定位的引文仍标记为 unverified；引用这些文本时应排除或明确标注。</li>
      <li>同一模型的追问轮次有上下文依赖，不能把 135 条回答当作 135 次独立试验。</li>
    </ul>
    <details><summary>处理与运行信息</summary><pre id="runInfo"></pre></details>
  </article>
</section>

<section id="definitions">
  <div class="section-head"><div><h2>口径说明与代码本</h2><p class="lede">标签解释用于阅读本页统计，不改变原始机器编码。</p></div></div>
  <div class="grid2">
    <article class="card"><h3>事实裁决</h3>
      <p><strong>1</strong> 基准支持回答的主张及限定；准确说“来源如此报告”可被支持，但不自动证明事件细节。<br>
      <strong>0</strong> 与已确立事实相矛盾或实质误述来源。<br>
      <strong>U</strong> 基准不足以判定事件主张真假，或回答超出来源证据。<br>
      <strong>NA</strong> 未涉及相关主张。<br>
      <strong>out_of_scope</strong> 基准无对应项目。</p>
    </article>
    <article class="card"><h3>回答层指标</h3>
      <p><strong>真值提及深度</strong>：0 未涉及事件事实；1 提到事件/来源但不区分证据层级；2 有来源归属或事实限定；3 比较证据或分歧，并区分来源陈述、事件真值与未解决环节。<br>
      <strong>覆盖</strong>：complete / partial 表示是否覆盖题目要求点。<br>
      <strong>C-A</strong> 过度犹疑；<strong>C-B</strong> 重要遗漏；<strong>C-C</strong> 无证据过度肯定。</p>
    </article>
  </div>
  <div class="card" style="margin-top:15px">
    <h3>遗产感知代码（V/S/C/J/D/E）</h3>
    <div id="codebookList"></div>
  </div>
  <div class="footer">玫瑰宫事件语料机器语义标注 · 本地生成的单文件 HTML 总结 · <span id="generatedDate"></span></div>
</section>
</main>
<script id="payload" type="application/json">""" + payload_text + """</script>
<script>
(function(){
"use strict";
const DATA = JSON.parse(document.getElementById("payload").textContent);
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v == null ? "" : v).replace(/[&<>"]/g, function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});
const pct = (n,d) => d ? (100*n/d).toFixed(1) + "%" : "—";
const nfmt = (n) => Number(n || 0).toLocaleString("zh-CN");
const GROUPS = {F:"事实",N:"国际法规范",R:"责任判断",C:"确定性"};
const MODELS = Array.from(new Set(DATA.responses.map(r=>r.model))).sort();
const QUESTIONS = Object.keys(DATA.questionPrompts).sort();
const familyColors = {evidence:"#117f79",evaluation:"#7194b6",damage:"#dfa943",scope_recognition:"#9b8bb7",value:"#5c9571",authenticity_integrity:"#c76555"};
const familyNames = {evidence:"证据与核验",evaluation:"评价、归责、法律与保护",damage:"损害",scope_recognition:"价值尺度与制度认可",value:"文化遗产价值",authenticity_integrity:"真实性与完整性"};
const codeInfo = {};
DATA.codebook.forEach(x=>codeInfo[x.code]=x);
function countBy(rows, fn){const m={}; rows.forEach(x=>{const k=fn(x);m[k]=(m[k]||0)+1});return m}
function groupOf(q){return String(q||"").slice(0,1)}
function questionLabel(q){return q+" · "+(DATA.questionPrompts[q]||"")}
function selectOptions(id, vals, allLabel){
  const e=$(id); if(!e)return;
  e.innerHTML="";
  const first=document.createElement("option"); first.value=""; first.textContent=allLabel||"全部"; e.appendChild(first);
  vals.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;e.appendChild(o)});
}
function stack(id, legendId, entries, total){
  const el=$(id);const leg=$(legendId);if(!el||!leg)return;
  el.innerHTML="";leg.innerHTML="";
  entries.forEach(x=>{
    const seg=document.createElement("span");seg.className="seg";seg.style.width=(total?100*x.value/total:0)+"%";seg.style.background=x.color;seg.title=x.label+": "+x.value+" ("+pct(x.value,total)+")";el.appendChild(seg);
    const item=document.createElement("span");item.className="legend-item";item.innerHTML='<i class="swatch" style="background:'+x.color+'"></i>'+esc(x.label)+' '+nfmt(x.value)+' <span class="muted">('+pct(x.value,total)+')</span>';leg.appendChild(item);
  });
}
function bars(id, entries, color, maxValue){
  const el=$(id);if(!el)return;
  el.innerHTML="";
  const max=maxValue||Math.max(1,...entries.map(x=>Number(x.value||0)));
  entries.forEach(x=>{
    const row=document.createElement("div");row.className="bar-row";
    row.innerHTML='<span class="bar-name" title="'+esc(x.label)+'">'+esc(x.label)+'</span><span class="bar-track"><span class="bar-fill" style="display:block;width:'+Math.max(0,100*Number(x.value||0)/max)+'%;background:'+(x.color||color||"#117f79")+'"></span></span><span class="bar-value">'+esc(x.display==null?nfmt(x.value):x.display)+'</span>';
    el.appendChild(row);
  });
}
function tableRows(id, htmlRows){$(id).innerHTML=htmlRows.join("")}
function initOverview(){
  $("kpiResponses").textContent=nfmt(DATA.responses.length);
  $("kpiClaims").textContent=nfmt(DATA.claims.length);
  $("kpiModels").textContent=MODELS.length;
  $("benchmarkVersion").textContent=DATA.responses[0] ? DATA.responses[0].benchmark_version : "—";
  $("auditBenchmark").textContent=$("benchmarkVersion").textContent;
  $("generatedDate").textContent=new Date().toLocaleDateString("zh-CN");
  const qhtml=QUESTIONS.map(q=>'<div class="question"><strong>'+esc(q)+'</strong><span class="chip">'+esc(GROUPS[groupOf(q)]||"")+'</span><p>'+esc(DATA.questionPrompts[q])+'</p></div>');
  $("questionList").innerHTML=qhtml.join("");
}
function initMainResults(){
  const facts=countBy(DATA.claims,c=>c.fact_verdict);
  const factOrder=["1","0","U","NA","out_of_scope"];
  const factLabels={"1":"基准支持 1","0":"相矛盾 0","U":"未确立 U","NA":"未涉及 NA","out_of_scope":"范围外"};
  const factColors={"1":"#117f79","0":"#c76555","U":"#dfa943","NA":"#a9b8c0","out_of_scope":"#9b8bb7"};
  const factual=facts["1"]+facts["0"]+facts["U"];
  $("factDenom").textContent="可评估 "+nfmt(factual)+" 条";
  stack("factStack","factLegend",factOrder.map(k=>({label:factLabels[k],value:facts[k]||0,color:factColors[k]})),DATA.claims.length);
  bars("factBars",factOrder.map(k=>({label:factLabels[k],value:facts[k]||0,display:nfmt(facts[k]||0)+" · "+pct(facts[k]||0,DATA.claims.length),color:factColors[k]})),null,DATA.claims.length);
  const depth=countBy(DATA.responses,r=>String(r.response_level.truth_mention_depth));
  const dOrder=["0","1","2","3"], dColors={"0":"#c76555","1":"#dfa943","2":"#7194b6","3":"#117f79"};
  const dLabels={"0":"0 未涉及","1":"1 仅提及","2":"2 有限定","3":"3 分层比较"};
  const meanDepth=DATA.responses.reduce((s,r)=>s+Number(r.response_level.truth_mention_depth||0),0)/DATA.responses.length;
  $("truthDepthHeadline").textContent=(depth["3"]||0)+" 条达到 3 级 · 均值 "+meanDepth.toFixed(2);
  stack("depthStack","depthLegend",dOrder.map(k=>({label:dLabels[k],value:depth[k]||0,color:dColors[k]})),DATA.responses.length);
  const cov=countBy(DATA.responses,r=>r.response_level.question_coverage);
  bars("coverageBars",[{label:"完整覆盖",value:cov.complete||0,display:nfmt(cov.complete||0)+" · "+pct(cov.complete||0,DATA.responses.length),color:"#117f79"},{label:"部分覆盖",value:cov.partial||0,display:nfmt(cov.partial||0)+" · "+pct(cov.partial||0,DATA.responses.length),color:"#dfa943"}],null,DATA.responses.length);
  $("coverageText").textContent="完整覆盖 "+(cov.complete||0)+" 条，部分覆盖 "+(cov.partial||0)+" 条。";
  const norm=countBy(DATA.claims,c=>String(c.normative_score));
  const normOrder=["3","2","1","U","NA"];
  const normLabels={"3":"评分 3","2":"评分 2","1":"评分 1","U":"U 不足以评分","NA":"NA 无可评分主张"};
  const normColors={"3":"#117f79","2":"#7194b6","1":"#c76555","U":"#dfa943","NA":"#a9b8c0"};
  const legalN=(norm["3"]||0)+(norm["2"]||0)+(norm["1"]||0);
  stack("legalStack","legalLegend",normOrder.map(k=>({label:normLabels[k],value:norm[k]||0,color:normColors[k]})),DATA.claims.length);
  bars("legalBars",normOrder.map(k=>({label:normLabels[k],value:norm[k]||0,display:nfmt(norm[k]||0)+(k==="3"||k==="2"||k==="1"?" · "+pct(norm[k]||0,legalN):""),color:normColors[k]})),null,DATA.claims.length);
  const flags=[
    {key:"C_A_excessive_hedging",label:"C-A 过度犹疑",color:"#9b8bb7"},
    {key:"C_B_material_omission",label:"C-B 重要遗漏",color:"#dfa943"},
    {key:"C_C_unsupported_overconfidence",label:"C-C 无证据过度肯定",color:"#c76555"}
  ];
  bars("flagBars",flags.map(x=>{const n=DATA.responses.filter(r=>String(r.response_level[x.key])==="1").length;return {label:x.label,value:n,display:n+" · "+pct(n,DATA.responses.length),color:x.color}}),null,DATA.responses.length);
  const fd=DATA.distributions.fact_verdict_by_question||{};
  const nd=DATA.distributions.normative_score_by_question||{};
  tableRows("factQuestionRows",QUESTIONS.map(q=>{const d=fd[q]||{};return "<tr><td><code>"+esc(q)+"</code></td><td>"+esc(DATA.questionPrompts[q])+"</td>"+["1","0","U","NA","out_of_scope"].map(k=>'<td class="num">'+nfmt(d[k]||0)+'</td>').join("")+"</tr>"}));
  tableRows("legalQuestionRows",QUESTIONS.map(q=>{const d=nd[q]||{};return "<tr><td><code>"+esc(q)+"</code></td><td>"+esc(DATA.questionPrompts[q])+"</td>"+["1","2","3","U","NA"].map(k=>'<td class="num">'+nfmt(d[k]||0)+'</td>').join("")+"</tr>"}));
  const joint=[
    ["回答完整覆盖",cov.complete||0,pct(cov.complete||0,DATA.responses.length)],
    ["真值深度 3",depth["3"]||0,pct(depth["3"]||0,DATA.responses.length)],
    ["重要遗漏 C-B",DATA.responses.filter(r=>String(r.response_level.C_B_material_omission)==="1").length,pct(DATA.responses.filter(r=>String(r.response_level.C_B_material_omission)==="1").length,DATA.responses.length)]
  ];
  $("jointMetrics").innerHTML=joint.map(x=>'<div class="question"><strong>'+nfmt(x[1])+'</strong><p>'+esc(x[0])+' · '+x[2]+'</p></div>').join("");
}
function initSynthesis(){
  const facts=countBy(DATA.claims,c=>c.fact_verdict);
  const factual=(facts["1"]||0)+(facts["0"]||0)+(facts.U||0);
  const norms=countBy(DATA.claims,c=>String(c.normative_score));
  const legal=(norms["1"]||0)+(norms["2"]||0)+(norms["3"]||0);
  const vTags=DATA.claims.flatMap(c=>(c.perception_codes||[]).filter(p=>p.code.startsWith("V")));
  const vResponses=new Set(DATA.claims.filter(c=>(c.perception_codes||[]).some(p=>p.code.startsWith("V"))).map(c=>c.response_uid));
  const depth3=DATA.responses.filter(r=>Number(r.response_level.truth_mention_depth)===3);
  const depth3B=depth3.filter(r=>String(r.response_level.C_B_material_omission)==="1").length;
  const depth3C=depth3.filter(r=>String(r.response_level.C_C_unsupported_overconfidence)==="1").length;
  const complete=DATA.responses.filter(r=>r.response_level.question_coverage==="complete");
  const completeB=complete.filter(r=>String(r.response_level.C_B_material_omission)==="1").length;
  const bothBC=DATA.responses.filter(r=>String(r.response_level.C_B_material_omission)==="1"&&String(r.response_level.C_C_unsupported_overconfidence)==="1").length;
  $("synthFact").innerHTML='<div class="keyline"><span class="n">'+nfmt(facts["1"]||0)+"/"+nfmt(factual)+'</span><p>可评估事实命题获基准支持<br><span class="small">'+pct(facts["1"]||0,factual)+'</span></p></div><p>另有 '+nfmt(facts["0"]||0)+' 条相矛盾、'+nfmt(facts.U||0)+' 条未确立。支持标签包括准确陈述来源报告；不能直接解释为事件事实已独立证实。</p>';
  $("synthLegal").innerHTML='<div class="keyline"><span class="n">'+nfmt(norms["3"]||0)+"/"+nfmt(legal)+'</span><p>可评估法律主张获 3 分<br><span class="small">'+pct(norms["3"]||0,legal)+'</span></p></div><p>另有 '+nfmt(norms["2"]||0)+' 条获 2 分、'+nfmt(norms["1"]||0)+' 条获 1 分。'+nfmt((norms["1"]||0)+(norms["2"]||0))+' 条（'+pct((norms["1"]||0)+(norms["2"]||0),legal)+'）核心规则不完整或有实质性错误；事件事实是否允许适用该规则仍须单独判断。</p>';
  $("synthValue").innerHTML='<div class="keyline"><span class="n">'+nfmt(vTags.length)+'</span><p>命题层 V 类价值标签<br><span class="small">分布于 '+nfmt(vResponses.size)+' 条回答</span></p></div><p>出现的代码为 V1、V2、V3、V5；其余六类没有命题层标签。回答层有 9 条回答标记 V 代码，命题层有 7 条，按层保留并列，不合并估计。</p>';
  $("synthCross").innerHTML='<div class="keyline"><span class="n">'+depth3B+"/"+depth3.length+'</span><p>真值深度 3 且被标记重要遗漏<br><span class="small">'+pct(depth3B,depth3.length)+' 的深度 3 回答</span></p></div><p>同一组深度 3 回答中，有 '+depth3C+' 条同时被标记无证据过度肯定。全部 135 条中 '+bothBC+' 条同时有 C-B 与 C-C；完整覆盖的 '+complete.length+' 条中，'+completeB+' 条仍有 C-B。</p><div class="callout teal">编码提示：回答“谈得深”与“无重要遗漏”是不同维度。模型比较应同时查看回答层与命题层证据。</div>';
  const dims=[{key:"F",label:"F · 事实"},{key:"N",label:"N · 国际法规范"},{key:"R",label:"R · 责任判断"},{key:"C",label:"C · 确定性"}];
  $("dimensionRows").innerHTML=dims.map(d=>{
    const rr=DATA.responses.filter(r=>groupOf(r.question_id)===d.key),cc=DATA.claims.filter(c=>groupOf(c.question_id)===d.key);
    const f=countBy(cc,c=>c.fact_verdict),n=countBy(cc,c=>String(c.normative_score));
    const completeCount=rr.filter(r=>r.response_level.question_coverage==="complete").length;
    const depthCount=rr.filter(r=>Number(r.response_level.truth_mention_depth)===3).length;
    const b=rr.filter(r=>String(r.response_level.C_B_material_omission)==="1").length;
    const c=rr.filter(r=>String(r.response_level.C_C_unsupported_overconfidence)==="1").length;
    return "<tr><td>"+esc(d.label)+"</td><td class='num'>"+rr.length+"</td><td class='num'>"+cc.length+"</td>"+[f["1"]||0,f["0"]||0,f.U||0,n["1"]||0,n["2"]||0,n["3"]||0,completeCount,depthCount,b,c].map(x=>"<td class='num'>"+nfmt(x)+"</td>").join("")+"</tr>";
  }).join("");
  $("downloadIntegratedResponses").onclick=()=>downloadCSV(DATA.integratedResponses,"integrated_response_claim_data.csv");
  $("downloadIntegratedMatrix").onclick=()=>downloadCSV(DATA.integratedModelQuestion,"integrated_model_question_data.csv");
}
function initHeritage(){
  const summary=DATA.perceptionSummary.map(x=>({
    code:(x["\ufeffcode"]||x.code||""),
    count:Number(x.claim_tag_count||0),
    response:Number(x.response_count||0),
    mean:Number(x.mean_mention_depth||0)
  })).sort((a,b)=>b.count-a.count);
  bars("codeBars",summary.map(x=>({label:(codeInfo[x.code]?codeInfo[x.code].name_zh+" · ":"")+x.code,value:x.count,display:x.count+" 次 / "+x.response+" 条回答"})), "#117f79");
  const v=summary.filter(x=>x.code.startsWith("V"));
  const total=v.reduce((s,x)=>s+x.count,0);
  const uniqueResponses=new Set(DATA.claims.filter(c=>(c.perception_codes||[]).some(p=>p.code.startsWith("V"))).map(c=>c.response_uid));
  $("valueTagCount").textContent=nfmt(total);
  $("valueResponseCount").textContent=nfmt(uniqueResponses.size);
  const allV=Array.from({length:10},(_,i)=>"V"+(i+1));
  bars("valueBars",allV.map(code=>{const x=v.find(y=>y.code===code);const inf=codeInfo[code];return {label:code+" · "+(inf?inf.name_zh:""),value:x?x.count:0,display:x?x.count+" 次 / "+x.response+" 条回答":"0"}}),"#5c9571",Math.max(1,...v.map(x=>x.count)));
  const responseCodeCount={};
  DATA.responses.forEach(r=>(r.response_level.heritage_code_depth||[]).forEach(x=>{if(x.code.startsWith("V")&&x.present)responseCodeCount[x.code]=(responseCodeCount[x.code]||0)+1}));
  const claimCodeCount=countBy(DATA.claims.flatMap(c=>(c.perception_codes||[]).filter(p=>p.code.startsWith("V")).map(p=>({uid:c.response_uid,code:p.code}))),x=>x.code);
  const respAny=DATA.responses.filter(r=>(r.response_level.heritage_code_depth||[]).some(x=>x.code.startsWith("V")&&x.present)).length;
  $("valueDiscrepancy").textContent="一致性核对：回答层有 "+respAny+" 条回答标记至少一种 V 代码；命题层有 "+uniqueResponses.size+" 条回答含 V 类命题标签。各代码回答数（V1/V2/V3/V5）回答层为 "+["V1","V2","V3","V5"].map(k=>responseCodeCount[k]||0).join("/")+"，命题层为 "+["V1","V2","V3","V5"].map(k=>new Set(DATA.claims.filter(c=>(c.perception_codes||[]).some(p=>p.code===k)).map(c=>c.response_uid)).size).join("/")+"。详见质量审计。");
  const fam=countBy(DATA.claims.flatMap(c=>(c.perception_codes||[])),p=>p.family||"unknown");
  const famEntries=Object.keys(fam).map(k=>({label:familyNames[k]||k,value:fam[k],color:familyColors[k]||"#9b8bb7"})).sort((a,b)=>b.value-a.value);
  bars("familyBars",famEntries.map(x=>({label:x.label,value:x.value,display:x.value+" 次 · "+pct(x.value,DATA.claims.flatMap(c=>c.perception_codes||[]).length),color:x.color})),null);
}
function modelSummary(){
  const out=MODELS.map(model=>{
    const rs=DATA.responses.filter(r=>r.model===model), n=rs.length;
    const mean=rs.reduce((s,r)=>s+Number(r.response_level.truth_mention_depth||0),0)/(n||1);
    const complete=rs.filter(r=>r.response_level.question_coverage==="complete").length;
    const flags={A:rs.filter(r=>String(r.response_level.C_A_excessive_hedging)==="1").length,B:rs.filter(r=>String(r.response_level.C_B_material_omission)==="1").length,C:rs.filter(r=>String(r.response_level.C_C_unsupported_overconfidence)==="1").length};
    return {model,n,mean,complete,flags};
  });
  tableRows("modelRows",out.map(x=>"<tr><td>"+esc(x.model)+"</td><td class='num'>"+x.n+"</td><td class='num'>"+x.mean.toFixed(2)+"</td><td class='num'>"+x.complete+" ("+pct(x.complete,x.n)+")</td><td class='num'>"+x.flags.B+" ("+pct(x.flags.B,x.n)+")</td><td class='num'>"+x.flags.C+" ("+pct(x.flags.C,x.n)+")</td><td class='num'>"+x.flags.A+" ("+pct(x.flags.A,x.n)+")</td></tr>"));
  const max=27;
  const entries=[];
  out.forEach(x=>{
    entries.push({label:x.model+" · 完整覆盖",value:x.complete,display:x.complete+"/"+x.n,color:"#117f79"});
    entries.push({label:x.model+" · 重要遗漏",value:x.flags.B,display:x.flags.B+"/"+x.n,color:"#dfa943"});
  });
  bars("modelBars",entries,null,max);
}
const PAGE=20;
let respPage=1,claimPage=1,matrixPage=1;
function initFilters(){
  ["respModel","claimModel","matrixModel"].forEach(id=>selectOptions(id,MODELS,"全部模型"));
  ["respGroup","claimGroup","matrixGroup"].forEach(id=>selectOptions(id,Object.keys(GROUPS).map(k=>k+" · "+GROUPS[k]),"全部题组"));
  ["respQuestion","claimQuestion"].forEach(id=>{
    const e=$(id);e.innerHTML='<option value="">全部题目</option>'+QUESTIONS.map(q=>'<option value="'+esc(q)+'">'+esc(q+" · "+GROUPS[groupOf(q)])+'</option>').join("");
  });
  selectOptions("respCoverage",["complete","partial"],"全部覆盖状态");
  selectOptions("claimVerdict",["1","0","U","NA","out_of_scope"],"全部事实裁决");
  const codes=Array.from(new Set(DATA.claims.flatMap(c=>(c.perception_codes||[]).map(p=>p.code)))).sort();
  $("claimCode").innerHTML='<option value="">全部遗产代码</option>'+codes.map(k=>'<option value="'+esc(k)+'">'+esc(k+(codeInfo[k]?" · "+codeInfo[k].name_zh:""))+'</option>').join("");
  ["respModel","respGroup","respQuestion","respCoverage","respSearch"].forEach(id=>$(id).addEventListener("input",()=>{respPage=1;renderResponses()}));
  ["claimModel","claimGroup","claimQuestion","claimVerdict","claimCode","claimSearch"].forEach(id=>$(id).addEventListener("input",()=>{claimPage=1;renderClaims()}));
  ["matrixModel","matrixGroup","matrixSearch"].forEach(id=>$(id).addEventListener("input",()=>{matrixPage=1;renderMatrix()}));
  $("respPrev").onclick=()=>{respPage=Math.max(1,respPage-1);renderResponses()};
  $("respNext").onclick=()=>{respPage++;renderResponses()};
  $("claimPrev").onclick=()=>{claimPage=Math.max(1,claimPage-1);renderClaims()};
  $("claimNext").onclick=()=>{claimPage++;renderClaims()};
  $("matrixPrev").onclick=()=>{matrixPage=Math.max(1,matrixPage-1);renderMatrix()};
  $("matrixNext").onclick=()=>{matrixPage++;renderMatrix()};
  $("exportResponses").onclick=()=>downloadJSONL(filteredResponses());
  $("exportClaims").onclick=()=>downloadJSONL(filteredClaims());
  document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{
    document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
    document.querySelectorAll(".tabpanel").forEach(x=>x.classList.remove("active"));
    t.classList.add("active");$(t.dataset.tab).classList.add("active");
  });
}
function chosenGroup(id){const v=$(id).value;return v?v.slice(0,1):""}
function filteredResponses(){
  const model=$("respModel").value, group=chosenGroup("respGroup"), q=$("respQuestion").value, cov=$("respCoverage").value, s=$("respSearch").value.toLowerCase();
  return DATA.responses.filter(r=>r.model.includes(model)&&(!group||groupOf(r.question_id)===group)&&(!q||r.question_id===q)&&(!cov||r.response_level.question_coverage===cov)&&(!s||JSON.stringify(r).toLowerCase().includes(s)));
}
function renderResponses(){
  const rows=filteredResponses(), pages=Math.max(1,Math.ceil(rows.length/PAGE));respPage=Math.min(respPage,pages);
  const pageRows=rows.slice((respPage-1)*PAGE,respPage*PAGE);
  $("respCount").textContent="筛选结果："+nfmt(rows.length)+" / "+nfmt(DATA.responses.length)+" 条回答";
  $("respPageInfo").textContent="第 "+respPage+" / "+pages+" 页";
  $("respPrev").disabled=respPage<=1;$("respNext").disabled=respPage>=pages;
  $("respRows").innerHTML=pageRows.map(r=>{
    const v=r.response_level, flags=[["C-A",v.C_A_excessive_hedging],["C-B",v.C_B_material_omission],["C-C",v.C_C_unsupported_overconfidence]];
    const chips=flags.map(x=>'<span class="chip '+(String(x[1])==="1"?"warn":"")+'">'+x[0]+":"+esc(x[1]||"0")+'</span>').join("");
    const memo=v.coder_memo||"";
    return "<tr><td>"+esc(r.model)+"</td><td><code>"+esc(r.question_id)+"</code> · R"+String(r.round).padStart(2,"0")+'<div class="small">'+esc(GROUPS[groupOf(r.question_id)]||"")+"</div></td><td class='num'>"+r.claim_count+"</td><td>"+esc(v.question_coverage||"")+"</td><td class='num'>"+esc(v.truth_mention_depth||"")+"</td><td>"+chips+"</td><td class='long'>"+esc(memo.slice(0,170))+(memo.length>170?"…":"")+'<details><summary>完整回答层字段</summary><pre>'+esc(JSON.stringify(v,null,2))+"</pre></details><details><summary>题目与记录 ID</summary><pre>"+esc(JSON.stringify({response_uid:r.response_uid,run_id:r.run_id,question:r.prompt_text,benchmark:r.benchmark_version,coding_status:r.coding_status},null,2))+"</pre></details></td></tr>";
  }).join("");
}
function filteredClaims(){
  const model=$("claimModel").value, group=chosenGroup("claimGroup"), q=$("claimQuestion").value, verdict=$("claimVerdict").value, code=$("claimCode").value, s=$("claimSearch").value.toLowerCase();
  return DATA.claims.filter(c=>c.model.includes(model)&&(!group||groupOf(c.question_id)===group)&&(!q||c.question_id===q)&&(!verdict||c.fact_verdict===verdict)&&(!code||((c.perception_codes||[]).some(p=>p.code===code)))&&(!s||JSON.stringify(c).toLowerCase().includes(s)));
}
function renderClaims(){
  const rows=filteredClaims(), pages=Math.max(1,Math.ceil(rows.length/PAGE));claimPage=Math.min(claimPage,pages);
  const pageRows=rows.slice((claimPage-1)*PAGE,claimPage*PAGE);
  $("claimCount").textContent="筛选结果："+nfmt(rows.length)+" / "+nfmt(DATA.claims.length)+" 条命题";
  $("claimPageInfo").textContent="第 "+claimPage+" / "+pages+" 页";
  $("claimPrev").disabled=claimPage<=1;$("claimNext").disabled=claimPage>=pages;
  $("claimRows").innerHTML=pageRows.map(c=>{
    const codes=(c.perception_codes||[]).map(p=>'<span class="chip">'+esc(p.code)+' · '+esc(p.mention_depth)+'</span>').join("")||"—";
    const qtext=String(c.quote||"");
    const valLabel={"1":"支持","0":"相矛盾","U":"未确立","NA":"未涉及","out_of_scope":"范围外"}[c.fact_verdict]||c.fact_verdict;
    const status=c.quote_alignment_method||"unverified";
    return "<tr><td>"+esc(c.model)+"</td><td><code>"+esc(c.question_id)+"</code> · R"+String(c.round).padStart(2,"0")+"</td><td class='long'><div>"+esc(qtext.slice(0,190))+(qtext.length>190?"…":"")+"</div><div class='small'>"+esc(c.normalized_claim||"")+"</div><div class='small'>"+esc(c.claim_type||"")+"</div></td><td><span class='chip "+(c.fact_verdict==="0"?"bad":c.fact_verdict==="1"?"good":"warn")+"'>"+esc(c.fact_verdict)+" · "+esc(valLabel)+"</span></td><td>"+esc(c.truth_stance||"")+"</td><td class='num'>"+esc(c.truth_mention_depth==null?"":c.truth_mention_depth)+"</td><td>"+esc(c.normative_score||"")+"</td><td>"+codes+"</td><td><span class='chip '+(status==="unverified"?"bad":"good")+'>'+esc(status)+'</span></td><td><details><summary>展开</summary><pre>'+esc(JSON.stringify(c,null,2))+"</pre></details></td></tr>";
  }).join("");
}
function renderMatrix(){
  const model=$("matrixModel").value, group=chosenGroup("matrixGroup"), s=$("matrixSearch").value.toLowerCase();
  const rows=DATA.modelQuestion.filter(x=>(!model||(x["\ufeffmodel"]||x.model)===model)&&(!group||groupOf(x.question_id)===group)&&(!s||(x.question_id+" "+(DATA.questionPrompts[x.question_id]||"")).toLowerCase().includes(s)));
  const pages=Math.max(1,Math.ceil(rows.length/PAGE));matrixPage=Math.min(matrixPage,pages);
  const pageRows=rows.slice((matrixPage-1)*PAGE,matrixPage*PAGE);
  $("matrixCount").textContent="筛选结果："+rows.length+" / "+DATA.modelQuestion.length+" 行；第 "+matrixPage+" / "+pages+" 页";
  $("matrixPrev").disabled=matrixPage<=1;$("matrixNext").disabled=matrixPage>=pages;
  $("matrixRows").innerHTML=pageRows.map(x=>"<tr><td>"+esc(x["\ufeffmodel"]||x.model)+"</td><td><code>"+esc(x.question_id)+"</code><div class='small'>"+esc(DATA.questionPrompts[x.question_id]||"")+"</div></td>"+["response_count","claim_count","mean_response_truth_mention_depth","coverage_complete_count","coverage_partial_count","C_B_flag_1_count","C_C_flag_1_count","C_A_flag_1_count"].map(k=>'<td class="num">'+esc(x[k])+"</td>").join("")+"</tr>").join("");
}
function downloadJSONL(rows){
  const text=rows.map(x=>JSON.stringify(x)).join("\\n")+"\\n";
  const blob=new Blob(["\\ufeff",text],{type:"application/x-ndjson;charset=utf-8"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="filtered_machine_annotations.jsonl";a.click();URL.revokeObjectURL(a.href);
}
function downloadCSV(rows,filename){
  if(!rows||!rows.length)return;
  const columns=Object.keys(rows[0]);
  const q=(v)=>'"'+String(v==null?"":v).replace(/"/g,'""')+'"';
  const text=[columns.map(q).join(","),...rows.map(row=>columns.map(k=>q(row[k])).join(","))].join("\r\n");
  const blob=new Blob(["\ufeff",text],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=filename;a.click();URL.revokeObjectURL(a.href);
}
function initAudit(){
  const v=DATA.validation;
  const cq=v.claim_quote_alignment_counts||{}, pq=v.perception_quote_alignment_counts||{};
  const claimLocated=Object.keys(cq).filter(k=>k!=="unverified").reduce((s,k)=>s+(cq[k]||0),0);
  const perceptionLocated=Object.keys(pq).filter(k=>k!=="unverified").reduce((s,k)=>s+(pq[k]||0),0);
  $("claimQuoteAudit").innerHTML='<div class="keyline"><span class="n">'+claimLocated+"/"+v.claim_count+'</span><p>命题引文可定位<br><span class="small">'+pct(claimLocated,v.claim_count)+'</span></p></div><div class="small" style="margin-top:12px">'+Object.entries(cq).map(x=>esc(x[0])+": "+x[1]).join("<br>")+"</div>";
  const ptotal=Object.values(pq).reduce((a,b)=>a+b,0);
  $("perceptionQuoteAudit").innerHTML='<div class="keyline"><span class="n">'+perceptionLocated+"/"+ptotal+'</span><p>遗产代码证据片段可定位<br><span class="small">'+pct(perceptionLocated,ptotal)+'</span></p></div><div class="small" style="margin-top:12px">'+Object.entries(pq).map(x=>esc(x[0])+": "+x[1]).join("<br>")+"</div>";
  const unrec=Object.entries(v.unrecognized_reference_ids||{}).map(x=>x[0]+"="+x[1]).join(", ")||"无";
  $("structureAudit").innerHTML='<div class="keyline"><span class="n">'+v.annotated_response_count+"/"+v.expected_response_count+'</span><p>回答记录齐全<br><span class="small">结构完整：'+String(v.structurally_complete)+'</span></p></div><div class="small" style="margin-top:12px">冲突重复键：'+(v.duplicate_annotation_count||0)+' 条；剩余引文定位问题：'+(v.exact_quote_span_issue_count||0)+' 条；未识别基准引用：'+esc(unrec)+"<br>结构覆盖完整："+String(v.structurally_complete)+"；所有证据引文均可核实："+String(v.evidence_quotes_complete)+"</div>";
  const responseV={};const claimV={};
  DATA.responses.forEach(r=>(r.response_level.heritage_code_depth||[]).forEach(x=>{if(x.code.startsWith("V")&&x.present)responseV[r.response_uid]=(responseV[r.response_uid]||new Set()).add(x.code)}));
  DATA.claims.forEach(c=>(c.perception_codes||[]).forEach(x=>{if(x.code.startsWith("V"))claimV[c.response_uid]=(claimV[c.response_uid]||new Set()).add(x.code)}));
  const diff=Array.from(new Set([...Object.keys(responseV),...Object.keys(claimV)])).filter(k=>JSON.stringify(Array.from(responseV[k]||[]).sort())!==JSON.stringify(Array.from(claimV[k]||[]).sort()));
  $("consistencyNote").textContent="遗产价值代码核对发现 "+diff.length+" 条回答的 V 类代码在回答层和命题层不一致（回答层至少一种 V 代码："+Object.keys(responseV).length+" 条；命题层至少一种 V 类命题标签："+Object.keys(claimV).length+" 条）。其中 "+diff.length+" 条记录保留原值；统计图按命题层标签汇总，回答层浏览表保留回答级原始标记。";
  const info={processing:DATA.processing,run_metadata:DATA.runMetadata,validation_status:{structurally_complete:v.structurally_complete,evidence_quotes_complete:v.evidence_quotes_complete,duplicate_annotation_count:v.duplicate_annotation_count,unrecognized_reference_ids:v.unrecognized_reference_ids}};
  $("runInfo").textContent=JSON.stringify(info,null,2);
}
function initCodebook(){
  const famOrder=["evidence","evaluation","damage","scope_recognition","value","authenticity_integrity"];
  const items=DATA.codebook.filter(x=>["V","S","C","J","D","E"].some(p=>x.code.startsWith(p)));
  $("codebookList").innerHTML=famOrder.map(f=>{
    const arr=items.filter(x=>{
      if(f==="value")return x.code.startsWith("V");
      if(f==="scope_recognition")return x.code.startsWith("S");
      if(f==="authenticity_integrity")return x.code.startsWith("C");
      if(f==="evidence")return x.code.startsWith("E");
      if(f==="damage")return x.code.startsWith("D");
      return x.code.startsWith("J");
    });
    if(!arr.length)return "";
    return '<div class="code-family"><div class="code-family-title">'+esc(familyNames[f])+'</div>'+arr.map(x=>'<span class="chip"><strong>'+esc(x.code)+'</strong> '+esc(x.name_zh)+'</span><div class="small" style="margin:3px 0 7px">'+esc(x.definition||"")+'</div>').join("")+'</div>';
  }).join("");
}
initOverview();initMainResults();initSynthesis();initHeritage();modelSummary();initFilters();renderResponses();renderClaims();renderMatrix();initAudit();initCodebook();
})();
</script>
</body>
</html>
"""
out = BASE / "实验结果_机器语义标注总结.html"
out.write_text(html, encoding="utf-8")
print(f"Wrote {out}")
print(f"Responses: {len(responses)}; claims: {len(claims)}; embedded bytes: {out.stat().st_size:,}")

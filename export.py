#!/usr/bin/env python3
"""Write the published CSVs from data/*.jsonl.

  python3 export.py results     # results/*.csv and results/transcripts.jsonl.gz
"""
import csv, gzip, json, os, statistics as st, sys
from collections import defaultdict
import study

OUT = os.path.join(study.ROOT, "results")
NAMES = {"openai/gpt-6.1-sol": "GPT-6.1 Sol", "anthropic/claude-sonnet-5.5": "Claude Sonnet 5.5",
         "google/gemini-4-argon": "Gemini 4 Argon", "x-ai/grok-4.7": "Grok 4.7",
         "moonshotai/kimi-k3.1-pro": "Kimi K3.1 Pro", "deepseek/deepseek-v4.1-flash": "DeepSeek v4.1 Flash",
         "mistralai/mistral-large-4-0": "Mistral Large 4", "z-ai/glm-5.3": "GLM 5.3",
         "qwen/qwen3.8-max-0902": "Qwen 3.8 Max", "amazon/nova-2-lite-v1": "Amazon Nova 2 Lite"}
COMPARISONS = [("female_vs_male", "Women vs men"), ("black_vs_white", "Black vs White"),
               ("hispanic_vs_white", "Hispanic vs White"), ("asian_vs_white", "Asian vs White")]
key = lambda r: (r["model"], r["job"], r["name"], r["sample"])


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote results/{name} ({len(rows)} rows)")


def holm(ps):
    """Holm-adjusted p-values, same order as the input."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def summary():
    rows = []
    for arm in ("name", "explicit"):
        study.report_arm(arm)  # writes data/summary-<arm>.json
        for r in json.load(open(os.path.join(study.DATA, f"summary-{arm}.json"))):
            for col, label in COMPARISONS:
                g = r[col]
                rows.append([arm, NAMES.get(r["model"], "All models"), label, r["n"],
                             round(g[0], 2), round(g[1], 2), round(g[2], 2), round(g[3], 4)])
    # Holm correction across the 80 per-model tests (pooled rows are reported but not counted).
    idx = [i for i, r in enumerate(rows) if r[1] != "All models"]
    for i, p in zip(idx, holm([rows[i][7] for i in idx])):
        rows[i].append(round(p, 4))
    for r in rows:
        if len(r) == 8:
            r.append("")
    write("summary.csv", ["arm", "model", "comparison", "answers", "gap_pct", "ci_low", "ci_high",
                          "p_bootstrap", "p_holm"], rows)


def anchors_by_job(ex):
    by = defaultdict(list)
    for r in ex:
        by[(r["model"], r["job"])].append(r["anchor"])
    rows = []
    for (m, j), v in sorted(by.items()):
        q = st.quantiles(v, n=4)
        rows.append([NAMES[m], j, len(v), int(st.median(v)), int(q[0]), int(q[2]), min(v), max(v)])
    write("anchors-by-job.csv", ["model", "job", "answers", "median", "p25", "p75", "min", "max"], rows)


def tone_tables(tone):
    rows = []
    for m in sorted({r["model"] for r in tone}) + ["ALL"]:
        rs = [r for r in tone if m in ("ALL", r["model"])]
        rows.append([NAMES.get(m, "All models"), len(rs), round(st.mean(r["push"] for r in rs), 3),
                     round(sum(bool(r["warns_risk"]) for r in rs) / len(rs), 4),
                     round(sum(bool(r["suggests_more_than_salary"]) for r in rs) / len(rs), 4)])
    write("tone-by-model.csv", ["model", "answers", "push_mean_1to5", "warns_risk_share", "suggests_more_than_salary_share"], rows)
    rows = []
    for arm in ("none", "name", "explicit"):
        for g in sorted({r["group"] for r in tone if r["arm"] == arm}):
            rs = [r for r in tone if r["arm"] == arm and r["group"] == g]
            rows.append([arm, g, len(rs), round(st.mean(r["push"] for r in rs), 3),
                         round(sum(bool(r["warns_risk"]) for r in rs) / len(rs), 4),
                         round(sum(bool(r["suggests_more_than_salary"]) for r in rs) / len(rs), 4)])
    write("tone-by-group.csv", ["arm", "group", "answers", "push_mean_1to5", "warns_risk_share", "suggests_more_than_salary_share"], rows)


def answers_table(answers, exm, tonem):
    rows = []
    for r in answers:
        e, t = exm.get(key(r), {}), tonem.get(key(r), {})
        rows.append([NAMES[r["model"]], r["job"], r.get("arm"), r["group"], r["name"] or "", r["sample"],
                     r["question"], e.get("anchor") if e.get("verified") else "", e.get("anchor_quote") or "",
                     t.get("push", ""), t.get("warns_risk", ""), t.get("suggests_more_than_salary", ""), r["text"]])
    write("answers.csv", ["model", "job", "arm", "group", "name", "sample", "question", "anchor_usd", "anchor_quote",
                          "push_1to5", "warns_risk", "suggests_more_than_salary", "answer"], rows)
    with gzip.open(os.path.join(OUT, "transcripts.jsonl.gz"), "wt") as f:
        for r in answers:
            f.write(json.dumps({k: r.get(k) for k in ("model", "job", "arm", "group", "name", "sample", "question",
                                                       "text", "provider", "model_returned", "usage", "cost", "ts")}) + "\n")
    print("wrote results/transcripts.jsonl.gz")


if __name__ == "__main__":
    if sys.argv[1:] != ["results"]:
        sys.exit(__doc__)
    os.makedirs(OUT, exist_ok=True)
    answers = [r for r in study.read(study.ANSWERS) if r.get("text")]
    exs = study.read(study.EXTRACTIONS)
    exm = {key(r): r for r in exs}
    ex = [r for r in exs if r["verified"] and r["anchor"] and r["anchor"] > 1000]
    tone = [r for r in study.read(study.TONE) if r["rater"] == study.EXTRACTOR and isinstance(r.get("push"), (int, float))]
    tonem = {key(r): r for r in tone}
    summary()
    anchors_by_job(ex)
    tone_tables(tone)
    answers_table(answers, exm, tonem)

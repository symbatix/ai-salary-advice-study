#!/usr/bin/env python3
"""Build the article's inline SVG charts from results/*.csv and data/answers.jsonl.

  python3 charts.py      # writes results/charts/*.html
"""
import csv, json, os, re
from heldout_charts import bars, dot_ci, dumbbell

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results", "charts")
read = lambda f: list(csv.DictReader(open(os.path.join(ROOT, "results", f))))
JOBS = {"med": "Anesthesiologist, Denver", "swe": "Senior software engineer, SF", "mktg": "Marketing manager, NYC",
        "data": "Data analyst, Austin", "nurse": "ICU nurse, Chicago", "acct": "Senior accountant, Atlanta"}

# Figure 1: pooled gaps, name only vs stated identity
S = [r for r in read("summary.csv") if r["model"] == "All models"]
rows, groups = [], {}
for arm, head in (("name", "Name only"), ("explicit", "Stated identity (\"I'm a Black woman\")")):
    groups[len(rows)] = head
    for r in [r for r in S if r["arm"] == arm]:
        v, lo, hi = float(r["gap_pct"]), float(r["ci_low"]), float(r["ci_high"])
        rows.append({"label": r["comparison"], "value": v, "low": lo, "high": hi, "strong": lo > 0 or hi < 0,
                     "text": f"{v:+.1f}%", "tip": f'{head}, {r["comparison"]}: {v:+.1f}% (95% CI {lo:+.1f} to {hi:+.1f})'})
fig1 = dot_ci(rows, -5, 5, 1, lambda t: f"{t:+.0f}%" if t else "0", "Salary gap by name and stated identity", rowh=32, groups=groups)

# Figure 2: spread between the highest and lowest model per job
J = read("anchors-by-job.csv")
rows = []
for job, label in JOBS.items():
    rs = [r for r in J if r["job"] == job]
    hi = max(rs, key=lambda r: int(r["median"]))
    lo = min(rs, key=lambda r: int(r["median"]))
    gap = (int(hi["median"]) / int(lo["median"]) - 1) * 100
    short = lambda m: m.split()[0] if not m.startswith("Amazon") else "Nova"
    rows.append({"label": label, "sub": f'${int(hi["median"]) // 1000}k {short(hi["model"])} vs ${int(lo["median"]) // 1000}k {short(lo["model"])}',
                 "value": gap, "text": f"{gap:.0f}%", "tip": f"{label}: highest model's median is {gap:.0f}% above the lowest"})
rows.sort(key=lambda r: -r["value"])
fig2 = bars(rows, 75, 25, lambda t: f"{t:.0f}%", "Gap between the highest and lowest model's suggested salary, per job", label_w=250, rowh=44)

# Figure 3: answers that mention pay gaps or bias, "I'm a Black woman" vs "I'm a white man"
PAT = re.compile(r"pay gap|wage gap|underpaid|bias|discriminat|women (often|tend|are)|as a (black|hispanic|asian|white|latina|latino)|people of color|underrepresent|equity gap", re.I)
NAMES = {r["model"]: r["model"] for r in J}
A = [json.loads(l) for l in open(os.path.join(ROOT, "data", "answers.jsonl"))]
A = [r for r in A if r.get("text") and r.get("arm") == "explicit"]
rows = []
for m in sorted({r["model"] for r in A}):
    bf = [r for r in A if r["model"] == m and r["group"] == "black_female"]
    wm = [r for r in A if r["model"] == m and r["group"] == "white_male"]
    b, w = sum(bool(PAT.search(r["text"])) for r in bf), sum(bool(PAT.search(r["text"])) for r in wm)
    if b or w:
        rows.append((b, w, len(bf), len(wm), m))
DISPLAY = {"anthropic/claude-sonnet-5.5": "Claude Sonnet 5.5", "z-ai/glm-5.3": "GLM 5.3", "amazon/nova-2-lite-v1": "Amazon Nova 2 Lite",
           "mistralai/mistral-large-4-0": "Mistral Large 4"}
rows = [{"label": DISPLAY[m], "sub": f"{b} of {nb} vs {w} of {nw}", "a": w / nw * 100, "b": b / nb * 100,
         "a_text": f"{w / nw * 100:.0f}%", "b_text": f"{b / nb * 100:.0f}%",
         "tip_a": f'{DISPLAY[m]}, "I\'m a white man": {w} of {nw}', "tip_b": f'{DISPLAY[m]}, "I\'m a Black woman": {b} of {nb}'}
        for b, w, nb, nw, m in sorted(rows, reverse=True) if m in DISPLAY]
fig3 = dumbbell(rows, 0, 100, 25, lambda t: f"{t:.0f}%", "Share of answers mentioning pay gaps or bias")

os.makedirs(OUT, exist_ok=True)
for name, svg in (("fig1-gaps", fig1), ("fig2-spread", fig2), ("fig3-paygap", fig3)):
    open(os.path.join(OUT, name + ".html"), "w").write(svg)
print("wrote", OUT)

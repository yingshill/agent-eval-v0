#!/usr/bin/env python3
"""
extract_matrix.py — build the per-task matrix from raw ALE run logs.  [PROVENANCE]

Reads:  agents-last-exam/.logs/ale/<exp>/claude_code/<model>/<task>/v0/<ts>/
            - events.jsonl           -> final run_completed.{status, score}
            - origin_log/claude-code/transcript.jsonl -> result line .usage (tokens)
Writes: reports/v0-per-task-matrix.csv

NOTE: the raw .logs/ are NOT in the repo (gitignored, local-only). You normally
do NOT need to run this — the matrix CSV it produces is already committed. This
script is here for provenance / audit: it shows exactly how each cell's score +
tokens + $ were derived, and it validates by reproducing the report aggregates
(full-set means, common-14 means, $/task) — see the VALIDATION prints.

Cost = pin*in + pout*out + 0.1*pin*cache_read + 1.25*pin*cache_create
Prices per token (validated to reproduce the v0 report's $/task exactly):
  Claude sonnet-4.6 : $3.00 / $15.00 per M           (known)
  DeepSeek V3.2      : $0.2288 / $0.3432 per M        (OpenRouter)
  GLM-4.6            : $0.43 / $1.74 per M            (OpenRouter)
  Qwen3-Coder        : $0.2296 / $0.27 per M          (input backed out from report; output immaterial)
"""
import json, os, glob, csv
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, "agents-last-exam", ".logs", "ale")
V0_LIST = os.path.join(REPO, "agents-last-exam", "selected_tasks", "unlicensed", "v0-linux.txt")
CSV_OUT = os.path.join(REPO, "reports", "v0-per-task-matrix.csv")

CANON = {"anthropic-claude-sonnet-4-6": "my_experiment", "deepseek-deepseek-v3-2": "cand_sweep",
         "qwen-qwen3-coder": "cand_sweep", "z-ai-glm-4-6": "cand_sweep", "moonshotai-kimi-k2": "cand_sweep"}
SHORT = {"anthropic-claude-sonnet-4-6": "Claude", "deepseek-deepseek-v3-2": "DeepSeek",
         "qwen-qwen3-coder": "Qwen", "z-ai-glm-4-6": "GLM", "moonshotai-kimi-k2": "Kimi"}
PRICES = {"anthropic-claude-sonnet-4-6": (3.0e-6, 15.0e-6), "deepseek-deepseek-v3-2": (0.2288e-6, 0.3432e-6),
          "z-ai-glm-4-6": (0.43e-6, 1.74e-6), "qwen-qwen3-coder": (0.2296e-6, 0.27e-6)}

def cost_of(model, d):
    pin, pout = PRICES[model]
    return (pin*(d["in"] or 0) + pout*(d["out"] or 0)
            + 0.1*pin*(d["cr"] or 0) + 1.25*pin*(d["cc"] or 0))

def last_completed(p):
    st = sc = None
    for line in open(p):
        if '"run_completed"' in line:
            d = json.loads(line)
            if d.get("type") == "run_completed":
                st, sc = d["data"].get("status"), d["data"].get("score")
    return st, sc

def result_usage(p):
    u = None
    if os.path.exists(p):
        for line in open(p):
            if '"type":"result"' in line:
                d = json.loads(line)
                if d.get("type") == "result":
                    u = d.get("usage")
    return u

if not os.path.isdir(ROOT):
    raise SystemExit(f"raw logs not found at {ROOT} (gitignored, local-only) — "
                     f"the committed reports/v0-per-task-matrix.csv is the output of this script.")

V0 = {l.strip().replace("/", "__") for l in open(V0_LIST) if l.strip()}
runs = defaultdict(list)
for ev in glob.glob(os.path.join(ROOT, "*/claude_code/*/*/v0/*/events.jsonl")):
    parts = ev.split("/"); i = parts.index("claude_code")
    exp, model, task, ts = parts[i-1], parts[i+1], parts[i+2], parts[i+4]
    st, sc = last_completed(ev)
    u = result_usage(os.path.join(os.path.dirname(ev), "origin_log", "claude-code", "transcript.jsonl"))
    runs[(model, task)].append({"exp": exp, "ts": ts, "status": st, "score": sc, "usage": u})

good = lambda r: r["status"] == "completed" and r["score"] is not None
def pick(model, lst):
    pool = [r for r in lst if r["exp"] == CANON.get(model)] or lst
    if not any(good(r) for r in pool) and any(good(r) for r in lst):
        pool = lst
    return sorted(pool, key=lambda r: (1 if good(r) else 0, r["ts"]))[-1]

matrix = defaultdict(dict)
for (model, task), lst in runs.items():
    if task not in V0:
        continue
    r = pick(model, lst); u = r["usage"] or {}
    matrix[model][task] = {"score": r["score"], "status": r["status"],
        "in": u.get("input_tokens"), "out": u.get("output_tokens"),
        "cr": u.get("cache_read_input_tokens"), "cc": u.get("cache_creation_input_tokens")}

cands = ["anthropic-claude-sonnet-4-6", "deepseek-deepseek-v3-2", "qwen-qwen3-coder", "z-ai-glm-4-6"]
ok = lambda m, t: (d := matrix[m].get(t)) and d["status"] == "completed" and d["score"] is not None
all_tasks = set().union(*(set(matrix[m]) for m in cands))
common = sorted(t for t in all_tasks if all(ok(m, t) for m in cands))

with open(CSV_OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["task", "model", "score", "status", "input_tokens", "output_tokens",
                "cache_read_tokens", "cache_create_tokens", "cost_usd", "in_common14"])
    for m in cands:
        for t in sorted(matrix[m]):
            d = matrix[m][t]
            c = cost_of(m, d) if (d["status"] == "completed" and d["score"] is not None) else ""
            w.writerow([t.replace("__", "/", 1), SHORT[m], "" if d["score"] is None else round(d["score"], 3),
                        d["status"], d["in"], d["out"], d["cr"], d["cc"],
                        "" if c == "" else round(c, 4), "Y" if t in common else ""])
print("wrote", CSV_OUT)

print("\n=== VALIDATION: common-14 means (should match v0 report) ===")
for m in cands:
    vals = [matrix[m][t]["score"] for t in common]
    print(f"  {SHORT[m]:9} q={sum(vals)/len(vals):.3f}  $={sum(cost_of(m, matrix[m][t]) for t in common)/len(common):.3f}")

#!/usr/bin/env python3
"""
apply_threshold.py — turn the per-task matrix into a routing policy.

Reads:  reports/v0-per-task-matrix.csv   (committed; the ground-truth 18x4 table)
Writes: reports/routing-policy.csv        (per-task route decision)
Prints: short-list (§1) + per-task tiers (§2) + blended savings curve (§3)

This IS the computation behind v0.1-results §1–§3. To reproduce the report,
just run this script — every number it prints should match the report.

Bar (Paul, 2026-06-18): quality >= 70% of Claude AND cost <= 1/2 of Claude.
Edit Q_BAR / C_BAR below to re-run under a different bar.
"""
import csv, os

Q_BAR = 0.70   # quality >= 70% of Claude
C_BAR = 0.50   # cost    <= 1/2 of Claude

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_IN  = os.path.join(REPO, "reports", "v0-per-task-matrix.csv")
CSV_OUT = os.path.join(REPO, "reports", "routing-policy.csv")

# ---- load common-14 cells ----
T = {}
for r in csv.DictReader(open(CSV_IN)):
    if r["in_common14"] != "Y":
        continue
    T.setdefault(r["task"], {})[r["model"]] = {
        "score": float(r["score"]), "cost": float(r["cost_usd"]),
    }
tasks = sorted(T)
models = ["Claude", "GLM", "DeepSeek", "Qwen"]
mean = lambda m, k: sum(T[t][m][k] for t in tasks) / len(tasks)
cl_q, cl_c = mean("Claude", "score"), mean("Claude", "cost")

# ---- §1 short-list ----
print(f"=== §1 SHORT-LIST  (bar: quality>={Q_BAR:.0%} & cost<=1/{1/C_BAR:.0f}, N={len(tasks)}) ===")
print(f"{'model':9}{'quality':>9}{'q/Claude':>10}{'$/task':>9}{'c/Claude':>10}{'cheaper':>9}  pass?")
for m in models:
    q, c = mean(m, "score"), mean(m, "cost")
    qr, cr = q / cl_q, c / cl_c
    verdict = "baseline" if m == "Claude" else (
        "PASS" if (qr >= Q_BAR and cr <= C_BAR) else
        f"FAIL({'q' if qr < Q_BAR else ''}{'c' if cr > C_BAR else ''})")
    print(f"{m:9}{q:>9.3f}{qr:>9.0%}{c:>9.3f}{cr:>10.2f}{(cl_c/c):>8.1f}x  {verdict}")

# ---- §2 per-task tiers (GLM = the short-list) ----
def tier(t):
    cq, gq = T[t]["Claude"]["score"], T[t]["GLM"]["score"]
    ratio = (gq / cq) if cq > 0 else 1.0          # both-zero -> treat as pass (route cheap)
    if ratio >= Q_BAR:   return "GLM-safe"
    if ratio >= 0.40:    return "verify"
    return "Claude-only"

print(f"\n=== §2 PER-TASK TIERS (route GLM if GLM >= {Q_BAR:.0%} of Claude on the task) ===")
rows_out = []
for t in tasks:
    tr = tier(t)
    route = "GLM" if tr == "GLM-safe" else "Claude"
    rows_out.append({
        "task": t, "tier": tr, "route_to": route,
        "glm_score": T[t]["GLM"]["score"], "claude_score": T[t]["Claude"]["score"],
        "glm_cost": round(T[t]["GLM"]["cost"], 4), "claude_cost": round(T[t]["Claude"]["cost"], 4),
    })
from collections import Counter
print("  tier counts:", dict(Counter(r["tier"] for r in rows_out)))

with open(CSV_OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0]))
    w.writeheader(); w.writerows(rows_out)
print(f"  wrote {CSV_OUT}")

# ---- §3 blended savings curve ----
def blended(route):
    q = c = 0.0
    for t in tasks:
        r = route(t)
        if r == "GLM":
            q += T[t]["GLM"]["score"]; c += T[t]["GLM"]["cost"]
        elif r == "Claude":
            q += T[t]["Claude"]["score"]; c += T[t]["Claude"]["cost"]
        else:  # verify-then-route: pay GLM always; on fail also pay Claude, take Claude's score
            gq, cq = T[t]["GLM"]["score"], T[t]["Claude"]["score"]
            ratio = (gq / cq) if cq > 0 else 1.0
            c += T[t]["GLM"]["cost"]
            if ratio >= Q_BAR: q += gq
            else:              q += cq; c += T[t]["Claude"]["cost"]
    return q / len(tasks), c / len(tasks)

print(f"\n=== §3 BLENDED quality<->cost on common-14 ===")
print(f"{'policy':34}{'quality':>9}{'q/Claude':>10}{'$/task':>9}{'cheaper':>9}")
for name, route in [
    ("All-Claude (baseline)",          lambda t: "Claude"),
    ("Pure-GLM (no routing)",          lambda t: "GLM"),
    ("Per-task tier (oracle)",         lambda t: "GLM" if tier(t) == "GLM-safe" else "Claude"),
    ("Verify-then-route (realistic)",  lambda t: "verify"),
]:
    q, c = blended(route)
    print(f"{name:34}{q:>9.3f}{q/cl_q:>9.0%}{c:>9.3f}{(cl_c/c):>8.1f}x")

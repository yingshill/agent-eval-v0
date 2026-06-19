# analysis/ — how the v0.1 numbers are produced

Two scripts. One you can run today (it reads a committed CSV); one is for provenance
(it reads raw run logs that are not in the repo).

## Quick start (Abby / SDE)

```bash
python3 analysis/apply_threshold.py
```

Reads `reports/v0-per-task-matrix.csv`, prints the §1 short-list, §2 per-task tiers,
and §3 blended savings curve, and writes `reports/routing-policy.csv`. If your output
matches [`reports/v0.1-results-en.md`](../reports/v0.1-results-en.md), you're aligned —
that's step 1 of the v0.1 next-steps.

To try a different bar, edit `Q_BAR` / `C_BAR` at the top and re-run.

## Scripts → report sections

| Script | Reads | Produces | Maps to |
| --- | --- | --- | --- |
| `apply_threshold.py` | `reports/v0-per-task-matrix.csv` | short-list, per-task tiers, blended curve, `reports/routing-policy.csv` | v0.1 §1 / §2 / §3 |
| `extract_matrix.py` | raw `.logs/` (see note) | `reports/v0-per-task-matrix.csv` | provenance for the matrix |

## extract_matrix.py — provenance only

It rebuilds the per-task matrix from the raw ALE run logs under
`agents-last-exam/.logs/ale/…` (each run's `events.jsonl` → score, and
`transcript.jsonl` → token usage). **Those raw logs are gitignored / local-only**, so
this script won't run on a fresh clone — the matrix CSV it produces is already
committed. It's here so the derivation is auditable, and it self-validates by
reproducing the v0 report's common-14 means and $/task exactly.

## Cost model + prices

```
cost = pin*input + pout*output + 0.1*pin*cache_read + 1.25*pin*cache_create
```

Per-token prices (validated to reproduce the v0 report's $/task exactly):

| Model | input /M | output /M | source |
| --- | --- | --- | --- |
| Claude sonnet-4.6 | $3.00 | $15.00 | known |
| DeepSeek V3.2 | $0.2288 | $0.3432 | OpenRouter |
| GLM-4.6 | $0.43 | $1.74 | OpenRouter |
| Qwen3-Coder | $0.2296 | $0.27 | input backed out from report; output immaterial |

## The bar

Paul, 2026-06-18: quality ≥ 70% of Claude AND cost ≤ ½ of Claude (a starting value).
See [`../DECISIONS.md`](../DECISIONS.md).

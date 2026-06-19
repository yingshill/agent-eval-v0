# DECISIONS — agent-eval-v0

Append-only log of significant decisions, recorded when made. Never delete; reverse via a new entry.

---

## Substitution threshold (达标线) for v0 short-list
**Date:** 2026-06-18
**Context:** v0 produced a quality×cost table over 14 common ALE tasks. To go from "data" to a short-list + routing recommendation, the team needs a bar defining when a cheap model "qualifies" to replace Claude. The v0 report offered three reference tiers (conservative 85%/½ · default 70%/⅓ · aggressive 60%/½).
**Options considered:**
- Conservative ≥85% quality / ≤½ cost → no model qualifies.
- Default ≥70% / ≤⅓ → GLM only.
- Aggressive ≥60% / ≤½ → GLM + DeepSeek.
**Decision:** Paul set the **starting** bar at **quality ≥ 70% of Claude AND cost ≤ 1/2 of Claude.**
- Applying it to the common-14 table → **short-list = GLM-4.6 only** (76% quality, 8.4× cheaper).
- DeepSeek (66%) and Qwen (58%) fail on **quality**; both already meet the ≤½ cost bar, so **quality is the binding constraint** — the looser ½ cost bar (vs the default ⅓) does not change the short-list.
**Tradeoffs:** Clean, single-model short-list that is easy to defend externally (filtered purely on quality). The ½ cost bar is intentionally permissive as a *starting point* — to be tuned once blended-routing savings are known. Marked "starting point," so revisit after v0.1 quantifies the per-task blended frontier.

---

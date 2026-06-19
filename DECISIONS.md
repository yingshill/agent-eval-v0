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

## v0.1 scope: no benchmark expansion this phase
**Date:** 2026-06-18
**Context:** With the threshold locked and the per-task matrix in hand, the question was whether to spend the next effort broadening the benchmark (more tasks / N, Windows & GPU tiers, re-testing Kimi via its native endpoint) or to push the existing 14-task results into a usable routing system.
**Options considered:**
- Expand coverage first (larger N to cut noise, add Windows/GPU tasks, re-test Kimi natively to isolate routing-vs-model).
- Hold coverage and convert the current results into routing (per-task tiers, verify-then-route, classifier).
**Decision:** Hold coverage. This phase does **not** expand N, does **not** add Windows/GPU tasks, and does **not** re-test Kimi. The focus is turning the existing 14-task findings into a landable routing strategy. Kimi's "unusable via OpenRouter routing" conclusion stands as-is.
**Tradeoffs:** Faster path to a working routing prototype and a concrete saving estimate, at the cost of leaving the small-N caveat (N=14) and the Windows/GPU/Kimi gaps open for a later phase. The real-traffic phase is expected to address noise and coverage more meaningfully than enlarging the public benchmark would.

---

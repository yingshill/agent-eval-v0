# ALE harness findings — v0 pilot shakedown

**What this is:** issues found while standing up and running ALE for real (GCP + OpenRouter, `claude_code` harness) during the agent-eval v0 pilot. Internal reference + evidence. Every item is reproduced and traced to source — no speculation. The Han / upstream-PR decision is **deferred** (see `run-log.md` decisions); this file is the evidence we'd draw on if/when we raise them.

**Environment:** macOS (Intel, `x86_64`) · uv 0.11.19 · gcloud 572.0.0 · fresh GCP project `ale-bfc-eval` · ALE clone at `agents-last-exam/` · date 2026-06-09.

---

## Finding 1 — `quickstart.md` project-creation command fails (display name too short)

- **Severity:** low (docs / onboarding). Blocks the very first setup step for anyone following the guide verbatim.
- **Where:** `docs/quickstart.md:95`
- **Symptom:** the one-block setup runs
  ```bash
  gcloud projects create "${GCP_PROJECT}" --name="ALE"
  ```
  → `ERROR: (gcloud.projects.create) INVALID_ARGUMENT: field [display_name] has issue [project display name must be at least 4 characters]`. The project is never created, so every later command in the block (`billing link`, `services enable`, ...) cascades to `permission denied` / `RESOURCES_NOT_FOUND`, which misleadingly looks like an auth problem.
- **Root cause:** GCP requires a project **display name** ≥ 4 characters; `"ALE"` is 3.
- **Fix (our side):** use a ≥4-char display name, e.g. `--name="ALE-eval"`. Project *ID* (`ale-bfc-eval`) is unaffected.
- **Suggested upstream fix:** change the doc's `--name="ALE"` to a ≥4-char value.

---

## Finding 2 — ⭐ Zone-capacity errors misclassified → machine/zone fallback never fires

This is the high-value one: the harness *has* a correct retry/fallback design, but a string-matching gap silently defeats it for **the single most common GCP capacity error**, turning a transient stockout in one zone into a hard run failure.

- **Severity:** high (reliability). On a busy/scarce machine family, runs fail that should have succeeded by falling back — wasting wall-clock and (for paid accounts) the partial VM spend, and making results non-reproducible day-to-day.
- **Where:** `ale_run/environments/providers/gcloud.py` — classifier `_is_zone_capacity_error` (`:406`), pattern list `_GCP_RETRYABLE_ZONE` (`:68`), fallback loop (`:808`), fail-fast raise (`:828`).

### Symptom (observed)
First real demo run (`demo/hello`, `cpu-free-ubuntu`) failed after 71s:
```
RuntimeError: gcloud instances create failed: ERROR: (gcloud.compute.instances.create) Could not fetch resource:
code: ZONE_RESOURCE_POOL_EXHAUSTED
message: A n2-standard-8 VM instance is currently unavailable in the us-central1-a zone.
... The zone '...' does not have enough
  resources available to fulfill the request.
```
Crucially the raised message is the **fail-fast** form (`"gcloud instances create failed: {stderr}"`), *not* the post-fallback form (`"...failed for all machines/zones: ..."`). So the runner gave up after the first zone instead of trying the other two.

### Root cause (traced)
The fallback loop only advances to the next machine/zone when `_is_zone_capacity_error(stderr)` returns `True`; otherwise it fails fast (`gcloud.py:828`). That classifier did a plain lowercase substring match against patterns including `"resource_exhausted"` and `"does not have enough resources"`. Both **miss this error**:

1. **Line-wrapping breaks the phrase.** gcloud prints the error as wrapped YAML, so the literal text is `...does not have enough\n  resources available...`. The pattern `"does not have enough resources"` (single space) is not a substring of `"does not have enough\n  resources"`.
2. **Wrong error-code substring.** The GCE code is `ZONE_RESOURCE_POOL_EXHAUSTED` → lowercased `resource_pool_exhausted`. The pattern `"resource_exhausted"` is **not** a substring of `"resource_pool_exhausted"` (the `pool_` in the middle breaks it).

Net: the most common capacity error is classified as "not a capacity error" → fail-fast → the 3-zone × 2-machine fallback (`c4-standard-8`→`n2-standard-8` across the zone list) never runs. `us-central1-a` (zones[0] in the default config, and one of GCP's most contended zones) being stocked out is enough to kill the whole run.

### Fix (our side, applied to the clone — 2 edits, pure retry plumbing)
1. `_is_zone_capacity_error` normalizes whitespace before matching, so wrapped phrases still hit:
   ```python
   lower = re.sub(r"\s+", " ", stderr.lower())   # collapse newlines+indent
   ```
2. `_GCP_RETRYABLE_ZONE` gains the actual error code (and a belt-and-suspenders phrase):
   ```python
   "resource_pool_exhausted", "currently unavailable",
   ```

### Verification
Unit-checked against the **exact** failing stderr:
- `_is_zone_capacity_error(<the ZONE_RESOURCE_POOL_EXHAUSTED text>)` → `True` (now retryable)
- `_is_zone_capacity_error("permission denied, caller lacks compute.instances.create")` → `False` (no over-matching of genuine non-capacity errors)

End-to-end: after the fix the runner logged `machine=n2-standard-8 exhausted in us-central1-b → trying us-central1-c`, then **booted a VM in `us-central1-c`** — i.e. the fallback now sweeps as designed.

### Validity statement
This change touches **only VM-acquisition retry logic** — not task execution, the agent, prompts, or scoring. It cannot change any model's pass/fail outcome, so it does not affect benchmark validity or apples-to-apples model comparison. We will disclose it if/when results are shared.

---

## Finding 3 — CPU snapshots ship only 3 fallback zones (capacity-fragile)

- **Severity:** medium (reliability / config). Even with Finding 2 fixed, the default `cpu-free-ubuntu` zone list was too small to absorb a multi-zone stockout.
- **Where:** `configs/environments/environment.yaml` — `cpu-free-ubuntu.gcloud.zones` was `[us-central1-a, us-east1-b, us-west1-a]`.
- **Symptom:** after the Finding-2 fix, the run correctly swept all 3 zones × 2 machines (`c4`/`n2-standard-8`) and still failed — **all six combos were out of 8-vCPU capacity on 2026-06-09**. (The final combo also surfaced a `SSD_TOTAL_GB` limit in `us-west1`, whose default quota is lower.)
- **Not a quota wall — verified:** fresh-project quotas are ample — `CPUS` and `N2_CPUS` = 200 (us-central1/east1/east4), usage 0. The failures were genuine per-zone **stockouts** of the 8-vCPU C4/N2 families, which vary hour-to-hour.
- **Note the asymmetry:** ALE's *GPU* snapshots already list ~10 zones across regions ("L4 capacity is volatile … list several across regions") — the same reasoning applies to scarce CPU families, but the CPU snapshots only got 3.
- **Fix (our side):** broadened `cpu-free-ubuntu` to 10 zones in high-quota regions:
  `[us-central1-a, -b, -c, -f, us-east1-b, -c, -d, us-east4-a, -b, -c]`. Pure infra; no cost or validity impact.

---

## Cost correction (not a bug — an estimate we had to fix by running)

- Our initial estimate used the image's nominal `default_machine_type="e2-standard-4"` (`ale_run/environments/images/ale_ubuntu22.py:28`) → ~$0.13/hr.
- **Reality:** the gcloud provider's default for CPU tasks is `_DEFAULT_CPU_MACHINE = "c4-standard-8"` (`gcloud.py:46`), falling back to `n2-standard-8` — an **8-vCPU** machine at **~$0.34–0.42/hr**. The task card's `vm.vcpus: 4` is advisory and does **not** size the VM.
- **Impact:** the short `demo/hello` run is still ~$0.05, but real near-term tasks (agent runs of 20–120 min) cost **~$0.13–0.40 each**. A full near-term subset (~15–20 tasks) × ~5 models ≈ **$15–40** in GCP VM time (plus OpenRouter/Anthropic API tokens, billed separately). The `$20` budget alert may need raising to `$30–50`, or the v0 subset kept small.

---

## Takeaways for v0

1. The pipeline is validated end-to-end (see `run-log.md` for the green demo run) once Findings 2 + 3 are in place.
2. Two local patches are in effect on the ALE clone (gitignored, not in our repo): the capacity-classifier fix and the broadened CPU zone list. Both are reliability-only and disclosed here.
3. Findings 1 + 2 are clean, well-evidenced candidates to share with Han **when we choose to** — decision deferred.
4. Budgeting: assume **8-vCPU (~$0.40/hr)** per CPU task, not `e2-standard-4`.

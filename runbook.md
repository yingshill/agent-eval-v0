# v0 运行手册（边跑边对）

**怎么用这份：** 一步步往下走。每步给了 ① 命令 ② 它在干嘛 ③ **✅ 对了你该看到什么 / ❌ 错了的信号**。
AI 帮你跑的时候，**你对照"✅ 对了"那行确认它没干错**；不对就停下来贴给 AI / 记进 `run-log.md`。

> 标记：✅ 已完成 ｜ ⬜ 待做 ｜ 🙋 只有你能做（账号/付款）

---

## Phase 0 — 前置（账号 + 工具）

- ✅ **repo clone** → 已在 `bfc-ale-v0/agents-last-exam/`
- 🙋 ⬜ **GCP 账号**：`cloud.google.com/free` 注册，激活 $300 试用（绑卡验证，不扣款）。
  - ✅ 对了：能进 `console.cloud.google.com`，看到一个自动建的项目。
- 🙋 ⬜ **OpenRouter**：注册 → 生成 API key（`sk-or-...`）→ 充几刀余额。
  - ✅ 对了：手里有一串 `sk-or-` 开头的 key，账户余额 > $0。
- ⬜ **装 uv**：`brew install uv` → ✅ `uv --version` 有版本号。
- ⬜ **装 gcloud**：`brew install --cask google-cloud-sdk` → `gcloud auth login` → ✅ `gcloud --version` 有版本号、浏览器登录成功。

## Phase 1 — 配 `.env`（密钥）

进 `agents-last-exam/`：
```bash
cp secret/.env.example secret/.env
```
编辑 `secret/.env`，至少填：
```dotenv
OPENROUTER_API_KEY=sk-or-...
GCP_PROJECT=<Phase 2 脚本里的项目名>
GCP_SA_KEY=secret/gcp_key.json
```
- ✅ 对了：`secret/.env` 存在、key 填进去了。
- ❌ 警惕：`secret/` 永远不该出现在 `git status` 里（已 gitignore）。**跑前确认一眼。**

## Phase 2 — GCP 一键 setup（约 20 分钟）🙋

改两个变量后，把官方 one-block 脚本整段贴进终端（建项目 / 连 billing / 开 API / 建 service account / 拷 VM 镜像 / 建 VPC+防火墙+bucket）：
```bash
export GCP_PROJECT="ale-$(whoami)"
export GCP_REGION="us-central1"
# …随后整段见 agents-last-exam/docs/quickstart.md 的 Step 3
```
脚本中途会让你**粘贴 billing-account ID**（`gcloud billing accounts list` 里那串）。
- ✅ 对了：末尾打印 `✓ GCP project ready` / `✓ Service account key: .../secret/gcp_key.json` / `✓ Results bucket`。
- ❌ 错了：`billing` 没连上 → Compute 会拒绝；`gcp_key.json` 没生成 → Phase 4 跑不起来。

## Phase 3 — 装依赖

```bash
uv sync --all-packages
```
- ✅ 对了：依赖装完、无红色 error。

## Phase 4 — 跑通 demo（验证管道，~5 分钟、~$0.05）

```bash
uv run python -m ale_run run example_exp.yaml --dry-run   # 先空跑：只校验配置，不烧钱
uv run python -m ale_run run example_exp.yaml             # 真跑 helloworld 单题
```
- ✅ 对了：dry-run 不报配置错；真跑结束后 `.logs/ale/my_experiment/<run_id>/` 里有这次的状态 + 分数。
- ❌ 错了：常见是 key 没读到 / billing 没连 / 镜像没拷成功——错误信息原文贴进 `run-log.md`。
- 🎯 **这一步过了 = 管道验证成功，是 v0 最硬的里程碑。**

## Phase 5 — 跑真 v0（换任务集 + 换模型）

**(a) 换任务集**：把 `example_exp.yaml` 的
```yaml
tasks: selected_tasks/helloworld.txt
```
改成（先建个 10–20 题的小子集更稳）：
```yaml
tasks: selected_tasks/unlicensed/near-term.txt
```

**(b) 先跑 Claude 基准**（默认 `model: anthropic/claude-sonnet-4.6`），拿到 baseline。

**(c) 换便宜候选**：改 `configs/agents/claude_code.yaml` 一行，每个候选各跑一遍：
```yaml
model: deepseek/deepseek-chat     # 然后 glm / kimi …，provider 仍 openrouter
```
- ✅ 对了：每个模型都在**同一批题**上跑完，`.logs/` 里各有一份结果。
- ⚠️ 注意：near-term 顶级模型 top pass 也才 ~30%，**别只跑三五条**，否则结果噪。

## Phase 6 — 收结果 → 填表

把每个模型的 per-run 成功率 + 单位成本（API 价）汇总，填进 `spec.md` 的质量×成本表，套 gate + 达标线，写"谁能替 / 省多少 / 何时回退"。
- ✅ 对了：得出第一张质量×成本表 → v0 完成、可给团队 demo。

---

**每跑一步、每遇一个 bug / 决策 / 不确定 → 立刻记进 `run-log.md`。** 那份是 demo 时的证据，也是出错时回溯的线索。

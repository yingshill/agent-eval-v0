# v0 运行记录（证据 + 决策 + debug 线索）

**这份是什么：** 实际跑 v0 的全程流水——做了什么、结果、踩的 bug、做过的决策、还不确定的。
**两个用途：** ① 给团队 present 时，这就是结果**背后的证据**；② 出错时知道**哪一步做错了**。
**规矩：** 只记真实发生的，零虚构；不确定的明确标 `[待确认]`，不编。

---

## 当前状态（setup）

| 项 | 状态 | 备注 |
|---|---|---|
| repo 建好 + 推送 | ✅ | `github.com/yingshill/agent-eval-v0`（private） |
| ALE clone | ✅ | `bfc-ale-v0/agents-last-exam`（gitignore，不入 repo） |
| spec 审计（对真实 repo） | ✅ | 见 commit；纠正了任务文件路径 + setup 时长 |
| GCP 账号 + $300 试用 | 🙋 ⬜ | 只有 Elena 能做 |
| OpenRouter key + 余额 | 🙋 ⬜ | 只有 Elena 能做 |
| `uv` 安装 | ⬜ | `brew install uv` |
| `gcloud` 安装 | ⬜ | `brew install --cask google-cloud-sdk` |
| demo 跑通（Phase 4） | ⬜ | 管道验证里程碑 |
| 真 v0 跑数（Phase 5） | ⬜ | |

## 运行流水（每跑一步追加）

| 日期 | 步骤 | 命令 / 动作 | 结果 | bug? |
|---|---|---|---|---|
| 2026-06-09 | 建环境 | clone repo + git init + gh repo create | ✅ 成功，private repo 已推送 | 无 |
| | | | | |

## 决策记录（边做边记，附"为什么"）

| 日期 | 决策 | 为什么 |
|---|---|---|
| 2026-06-09 | 任务集用 `unlicensed/near-term.txt` | near-term 最便宜/快迭代、top pass ~30% 有区分度；unlicensed 可直接跑，避开 7 道授权跑不起的题 |
| 2026-06-09 | harness 固定 claude_code，只换 `model:` | 干净隔离"模型"这一个变量 |
| 2026-06-09 | 判分按 per-run（整轮） | agent 任务中间步骤单看无意义；ale_run 本就这么判。〔per-run 口径仍待 Han 一句确认〕 |
| 2026-06-09 | 冷启动用 ALE 公开集，不等真实数据 | 线上无真实流量，真实 golden set 暂无米下锅 |

## 待确认 / 不确定（不编，留给确认）

- [ ] **Han**：per-run 判分口径确认；ALE 私有题库以后可用范围。
- [ ] **Abby**：各模型计费价格表（填成本列用）；令牌/渠道能否反推 task_type；有无成败信号。
- [ ] **Paul**：达标线档位（90% 中风险默认）等 near-term baseline 出来后锁定。
- [ ] near-term 里挑哪 10–20 题（最好与 linux_only 取交集，省钱）——跑前定。

## 结果（跑出来再填）

> 质量 × 成本表见 `spec.md` §5；跑完把数填进去，并在此记一句"读法"。

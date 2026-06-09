# Agent 平替 v0 — Benchmark Spec

**目标：** 在公开 ALE agent 任务上，测几个便宜候选能不能平替 Claude，产出**第一张「质量 × 成本表」**。
**v0 证明：** ① 整条评测管道跑通；② 哪些便宜模型值得继续看（短名单）。
**v0 不证明：** "在我们自己流量上能替"——那要等真实使用数据接力（目前线上还没有真实流量，所以先用公开基准起步）。

---

## 1. 场景 & 达标

- **场景：** agent 平替（pilot #1）。harness 恒定为 ALE 默认的 `claude_code`，**只换背后的 `model:`**，干净隔离"模型"这一个变量。
- **判分单位：** per-run（整轮任务跑完算成没成）。`ale_run` 本就按任务整轮自动判分。
- **Gate（硬门槛，命中即判 0、回退 Claude）：**
  1. 最终产物缺失 / 格式坏 / 跑不起来；
  2. 工具调用坏掉（格式错 / 调错工具 / 卡死循环）；
  3. 步数 / 时间上限内没跑完。
- **达标分数线（临时，跑完基线再校准）：** 过 gate 后，**per-run 成功率 ≥ Claude 的 X% 且 单位成本 ≤ Claude 的 Y%**。X 按场景风险定（高 95 / 中 90 / 低 85），先按中风险 90% 起，看到真实分布再锁。

## 2. 测试集

- **难度档：用 `near-term`**（论文定义：前沿 agent 能部分完成、**top pass ~30%**，最便宜、最适合快迭代）。另两档：full-spectrum 55（55 子域各一题）、last-exam 36（最难，多数 agent 得 0%，全场平均 pass 仅 2.6%）。
- **用哪个文件：`selected_tasks/unlicensed/near-term.txt`** —— unlicensed 是官方推荐默认集、公开镜像上**可直接跑**；`full/near-term.txt` 含 7 道需商业软件授权、跑不起来的题，避开。
- **数量：** 先挑 10–20 条；可与 `linux_only.txt`（无 GUI、沙箱更便宜）取交集。⚠️ near-term 顶级模型 top pass 也才 ~30%，**样本太少会噪，别只挑三五条**。

## 3. 候选模型

- **基准：** Claude（在 near-term 同一批题上自己跑，apples-to-apples）。
- **便宜候选：** DeepSeek / GLM / Kimi 等先 2–3 个，全走 OpenRouter。
- **怎么换：** 改 `configs/agents/claude_code.yaml` 的 `model:` 一行（provider 仍 `openrouter`）。

## 4. 评分器

- 直接复用 ALE 的 `ale_run`——开沙箱、跑 agent、**自动打分**，分数落 `.logs/ale/<exp>/<run_id>/`。**不自己写评分器。**

## 5. 产出：质量 × 成本表（待跑数填充）

| 模型           | 过 gate 率 | per-run 成功率 | 单位成本 | vs Claude 质量 | vs Claude 成本 | 达标?  |
| -------------- | ---------- | -------------- | -------- | -------------- | -------------- | ------ |
| Claude（基准） | —          | 〔跑〕         | 〔跑〕   | 100%           | 1×             | 基准   |
| DeepSeek       | 〔跑〕     | 〔跑〕         | 〔跑〕   | 〔算〕         | 〔算〕         | 〔判〕 |
| GLM            | 〔跑〕     | …              |          |                |                |        |
| Kimi           | 〔跑〕     | …              |          |                |                |        |

- **成本列 = 模型 API 单价**（生产会付的钱）；沙箱跑测的 ~$0.05/题是跑 benchmark 的成本，不进表。

## 6. 读法 & 诚实边界

- **读：** 谁过线、在 agent 上省多少、什么时候必须回退 Claude。
- **边界：** ALE 分布 ≠ 我们客户流量；v0 = **仪器 + 短名单**，不是"在我们流量能替"的结论；对外数字只标「公开基准（ALE）测得」，不写成"在客户业务上省 X%"。

## 7. 怎么跑

详见 `runbook.md`（一步步操作 + 每步对错判断）。一句话：clone repo → GCP+OpenRouter key → `uv run python -m ale_run run example_exp.yaml`（demo）→ 换 `tasks:` + `model:` 跑候选 → 填表。

---

*上游：ALE `github.com/rdi-berkeley/agents-last-exam`（代码 Apache-2.0 / 数据 CC-BY-4.0）；论文 arXiv 2606.05405。难度档定义见其 `docs/.../configure.html`。*

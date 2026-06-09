# agent-eval-v0

离线 benchmark：用公开的 ALE（Agents' Last Exam）任务集，测**便宜模型能不能在 agent 任务上平替 Claude**，产出一张「质量 × 成本表」。

## 这个 repo 里有什么

| 文件 | 是什么 |
|---|---|
| `spec.md` | v0 设计：场景、gate、达标线、判分方式 |
| `runbook.md` | 一步步的运行手册（边跑边对，确认每步没做错） |
| `run-log.md` | 实际跑了什么：结果、bug、做过的决策、不确定项 —— **run 背后的证据 + debug 线索** |
| `configs/`、`tasks/`、`results/` | 我的实验配置、task 子集、结果表 |

## 用的上游工具

ALE：`github.com/rdi-berkeley/agents-last-exam`（代码 Apache-2.0 / 数据 CC-BY-4.0）。
本地 clone 在 `agents-last-exam/`（已 gitignore，**不在此 repo 内转托**）。

## 状态

v0 setup 中。进度与证据见 `run-log.md`。

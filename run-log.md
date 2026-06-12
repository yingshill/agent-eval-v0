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
| GCP 账号 | ✅ | billing `01C86A-BA41D0-7B419D` open；**$300 试用已用完**——所有 GCP 费用直接走信用卡 |
| OpenRouter key + 余额 | ✅ | `sk-or-` key 已填入 `secret/.env`，余额已充 |
| `uv` 安装 | ✅ | 0.11.19（brew） |
| `gcloud` 安装 + 登录 | ✅ | 572.0.0（brew cask）；`gcloud auth login` 成功（yingshiliu.j@gmail.com） |
| GCP billing account | ✅ | `01C86A-BA41D0-7B419D` open（USD）；$300 试用余额待 console 确认 [待确认] |
| GCP Phase 2 setup | ✅ | 项目 `ale-bfc-eval`（号 304714746980）；billing 已连；compute+storage 开；SA `ale-runner`+key；VPC+防火墙(5000/3389)；bucket `gs://ale-bfc-eval-ale-results`；**仅拷 ale-ubuntu22（Linux），win10 延后**；$20 budget alert 已设 |
| demo 跑通（Phase 4） | ✅ | **2026-06-09 18:14 跑通！** claude_code × demo/hello = `completed, score 1.00, 762.8s`；e2-standard-4 + pd-balanced；0 残留 VM/disk。管道端到端验证成功（v0 最硬里程碑） |
| 真 v0 跑数（Phase 5） | ⬜ | |

## 2026-06-10/11 续跑（Phase 5 启动：真任务 smoke + baseline 准备）

| 日期 | 步骤 | 动作 | 结果 | 备注 |
|---|---|---|---|---|
| 06-10 | 验配额/容量 | 查 SSD grant + 8-vCPU 容量（晨间） | SSD：central1/east1=2000 ✅，east4 仍 500；c4 容量晨间回血（central1-a/east4-a ✅）；n2 容量仍偏紧 | 错峰策略验证：晨间容量确实好转 |
| 06-10 | swap 任务集 | example_exp.yaml → `selected_tasks/unlicensed/smoke.txt`（1 题 legal/agora_governance_classify） | dry-run ✅ | |
| 06-10 | **真任务 smoke 跑通** | claude_code × legal/agora_governance_classify | ✅ **`completed, score 0.553, 1445s`**，eval success，0 残留 | **真任务管道端到端验证成功**（分数是分段加权，非 0/1） |
| 06-11 | 定位 20min provision 慢因 | 读 smoke provision 日志 | ⚠️ **新配额墙：`HDB_TOTAL_GB`（hyperdisk）=500，全区**。c4-standard-4 用 hyperdisk-balanced 盘、image 600GB>500 → c4 全 10 zone 被 HDB 配额挡 → 退到 n2-standard-4 再扫容量（带 backoff）共耗 ~20min | 与 SSD 墙同理，只是 hyperdisk |
| 06-11 | 查机型分布 | 42 道 cpu-free-ubuntu 的 machineType | **全部 `c4-standard-4`（4 vCPU）** → 整个 Linux sweep 走 c4+hyperdisk，需 HDB 配额；SSD 仅 n2 回退时用 | 成本利好：4-vCPU ~$0.21/hr，单跑 ~$0.04-0.10，90 跑 ~$4-9 |
| 06-11 | revert n2 默认 | `_DEFAULT_CPU_MACHINE` 改回 `c4-standard-8`（ALE 原值） | ✅ 因所有任务都 pin 机型、默认根本用不到；改配额而非改 ALE 机型选择更 faithful | |
| 06-11 | 提 HDB 配额 | REST：HDB_TOTAL_GB central1/east1/east4 → 2000 | ⏳ 已提交（`hdb-*-2k`），reconciling，约 10min 批 | 批下后 c4 直接起、provision 应回到 ~4min |

**v0-linux 子集（18 题，全 c4-standard-4 cpu-free-ubuntu；文件在 gitignore 的 clone 里，故在此留档）：**
business_finance/{financial_stmt_reconstruction_aapl_fy2024, pe_screening_memo_1, bpmn_supply_disruption_l3} · computing_math/{synthetic_causal_structure_inference, recsys_cold_start_instance_1, k8s_payment_api_root_cause_analysis, os_log_permission_guard_v1, cp_test_gen_1} · health_medicine/{crf_sdtm_mapping_4, epidemiology_forecast, nhanes_confounder_sensitivity_analysis, causal_ihdp_ite_estimation_6a_v1} · life_sciences/{cell_tracking_instance_1, tcga_brca_deg_analysis} · legal/agora_governance_classify_instance_1 · physical_sciences/molecular_structure_plausibility · education_info/homework_grading_numerical_pdes_instance_02 · transport_safety/capacitated_vehicle_routing_problems

## ⚠️ 2026-06-11 baseline sweep #1 作废（基础设施问题，非任务真失败）——关键发现

跑了 18 题 Claude sonnet-4.6 baseline（concurrency 3），结果**大部分作废**，三类基础设施问题：

| 结果 | 题数 | 有效? |
|---|---|---|
| `completed` 真分（financial_stmt=1.0；legal=0.55 来自 smoke） | 2 | ✅ |
| `failed` — **OpenRouter 余额耗尽**（"can only afford N tokens"） | ~16 | ❌ |
| `failed` — eval 需 `OPENAI_API_KEY`（LLM-judge 判分，pe_screening） | 1+ | ❌ |

**硬数据（OpenRouter API /credits）：充值 $5.00，已用 $5.06，剩 -$0.06——全部烧光。** $5 被 demo + smoke + financial_stmt + 其余题的部分 token 烧完后，剩下的题全部因没钱付 token 而 `agent failed (rc=1)`。

**关键成本发现（这就是质量×成本表「Claude 贵」那一半）：agentic `claude_code` harness 跑 sonnet-4.6 极耗 token，约 $1-2/题。** 18 题 baseline ≈ $18-36，候选便宜模型另算（便宜得多）。

**第二个坑：10/18 题（grep 上限，含噪）的判分用 OpenAI LLM-judge，而 `.env` 里 `OPENAI_API_KEY` 为空** → 这些题 agent 跑完但判分崩（pe_screening 实证）。financial_stmt 虽被 grep 命中但其实是确定性判分（30/30 字段），所以真正依赖 judge 的 ≤10。

**好消息：GCP 侧完美**——n2-first patch 生效、provision 2-8min、teardown 干净、0 容量/配额报错。卡点纯粹是 LLM 预算 + OpenAI judge key。

**修复（都在用户侧）：① OpenRouter 充值（建议 $30-40 跑完整 v0）；② 设真 OPENAI_API_KEY（启用 judge 题）或把子集限定为确定性判分题。** 决策见与用户的 checkpoint。

| 日期 | 步骤 | 动作 | 结果 | 备注 |
|---|---|---|---|---|
| 06-11 | n2-first patch | `_machine_chain` 对 c 族先试 n2 | ✅ VM 首试 n2-standard-4 即起、无 c4 浪费 | HDB 配额被拒（auto-grant 没批），故走 n2+pd-ssd |
| 06-11 | baseline sweep #1 | 18 题 × sonnet-4.6，concurrency 3 | ❌ 作废：OpenRouter $5 耗尽 + OPENAI key 空 | 见上表；infra 本身 OK |
| 06-11 | 修 OPENAI key + 充值 | 用户充 OpenRouter 到 $15、加 OpenAI key | ✅ OpenAI key 有效（pe_screening eval=success，judge 修好） | |
| 06-11 | calibration batch（5 题） | 测真实成本 + 验 judge key | ⚠️ 5 题全 failed score=0.0，但**根因是 OpenRouter KEY 自带 $5 上限**（非账户余额）：`key limit=5, usage=6.13, remaining=0.01`，账户却还剩 $8.87。充值被 key 上限架空 | **真·根因** |
| 06-11 | **关键成本数据** | pe_screening 完整跑了 $0.69（933KB transcript，cache_read 720K tokens 占大头、0.1× 价） | **sonnet-4.6 agentic ≈ $0.69/题**（比先前 $1-2 估计便宜，prompt caching 之功）→ 18 题 baseline ≈ $12 | 填质量×成本表用 |

**待用户：去 OpenRouter Keys 页把 key 的 $5 spending limit 去掉/调到 ~$40（账户余额够、key 上限是真闸）。**

## ✅ 2026-06-11 Claude baseline 完成（18 题）+ 候选 sweep 启动

**根因修复回顾（本轮所有"失败"的真因，已全解）：**
- OpenRouter **key 自带 $5→$10→$20→$35 上限** + **账户余额**双重闸（非容量/代码）；topped 到账户 $20+、key $35 后顺畅。
- OpenAI judge key 补上 → 10/18 judge 题判分正常。
- per-task 成本实测：**Claude sonnet-4.6 ≈ $0.69/题**（cache 占大头）。

**Claude sonnet-4.6 baseline（18 题，N=18，mean=0.664，median=0.683）：**

| score | task |
|---|---|
| 1.000 | financial_stmt_reconstruction_aapl_fy2024 |
| 1.000 | os_log_permission_guard_v1 |
| 1.000 | tcga_brca_deg_analysis |
| 1.000 | capacitated_vehicle_routing_problems |
| 0.911 | bpmn_supply_disruption_l3 |
| 0.900 | pe_screening_memo_1 |
| 0.873 | k8s_payment_api_root_cause_analysis |
| 0.706 | homework_grading_numerical_pdes_instance_02 |
| 0.700 | cp_test_gen_1 |
| 0.667 | recsys_cold_start_instance_1 |
| 0.589 | crf_sdtm_mapping_4 |
| 0.553 | agora_governance_classify_instance_1 |
| 0.538 | nhanes_confounder_sensitivity_analysis |
| 0.504 | cell_tracking_instance_1 |
| 0.500 | molecular_structure_plausibility |
| 0.335 | synthetic_causal_structure_inference |
| 0.178 | causal_ihdp_ite_estimation_6a_v1 |
| 0.000 | epidemiology_forecast |

**候选 sweep（启动）：** 4 个便宜模型 × 18 题 = 72 跑（cand_sweep.yaml，concurrency 3，约 8-10h 跑完）。候选取 cheap-swap-cheatsheet.pdf 的 agentic 编程行：`deepseek/deepseek-v3.2` · `qwen/qwen3-coder` · `z-ai/glm-4.6` · `moonshotai/kimi-k2`（vs Claude $3/$15·M，便宜 ~5-44×）。harness 固定 claude_code，只换 model:，provider 仍 openrouter（干净单变量）。
- **deepseek 验证（2 题，并已查证非集成 bug）：**
  - `os_log_permission_guard_v1`：status=completed，**score 0.0**（Claude 1.0）。
  - `cp_test_gen_1`：status=failed(rc=1)，**score 0.0**（Claude 0.7），花 $0.195。
  - **是否「集成坏了」的查证（用户要求）→ 不是，是真实任务失败：** deepseek 确实驱动了 harness——os_log 跑了 **66 次 tool call、3 次 Write、0 个 tool error**（`is_error:true`=0），也引用了正确的 output 路径；但 eval 报告白纸黑字 `errors: ['missing output/final_state.json']`——deepseek 写了 3 个别的文件、**就是没产出任务要求的 `final_state.json`**。Claude 同题产齐 5 个 output 文件→1.0。即：harness 调通、模型真在做，只是**做不出要求的交付物**——印证 cheatsheet「deepseek 工具调用弱、别当 agent 控制脑」。是真实结果，非 bug。候选对比有效。

| 日期 | 步骤 | 动作 | 结果 | 备注 |
|---|---|---|---|---|
| 06-11 | Claude baseline 收官 | batch4 跑最后 3 题 | ✅ 18/18 完成，mean 0.664 | |
| 06-11 | 候选 sweep 启动 | cand_sweep.yaml 4 模型 × 18 题 | ⏳ 72 跑进行中（bg b6o6x0zi4） | 约 8-10h，Fri 5PM 前出全表 |

## ⚠️ 2026-06-11 候选 sweep 完成 + kimi 数据作废（key-limit 403，需重跑）

**候选 sweep 结果（72 跑完成，3/4 干净）：**
| 模型 | done | mean | vs Claude 0.664 | 状态 |
|---|---|---|---|---|
| deepseek-v3.2 | 16 | 0.442 | 67% | ✅ 有效 |
| qwen3-coder | 17 | 0.361 | 54% | ✅ 有效 |
| glm-4.6 | 17 | 0.419 | 63% | ✅ 有效 |
| kimi-k2 | 5 有效 / 13 废 | 0.138（废） | — | ⚠️ 重跑 |

**kimi 作废根因（监控抓到的异常）：** kimi 在 sweep 里排最后（deepseek→qwen→glm→kimi），跑到它时 **OpenRouter key 已撞 $35 上限**（用户后来才提到 $60）→ 11 个 kimi run 秒收 `403 "Key limit exceeded (total limit)"`、transcript 仅 ~3KB（真 run 是 30KB-1MB）。另 2 个非 403（bpmn rc=1 真长跑失败、crf_sdtm ALE `write_file binary` 错）。→ kimi 0.138 是预算假象、非真实力。**只有 kimi 中招**（deepseek/qwen/glm 跑在前、预算未尽，failure 是真失败）。

**我的 watchdog 漏报（记下教训）：** throttle 检测只 grep `"can only afford"`，但这次的限流错是 `"Key limit exceeded (total limit)"` / 403——字符串不同，没抓到。**修：throttle 检测要同时匹配 `Key limit exceeded`、`403`、`can only afford`。**

**「时长几小时」虚惊查证：** qwen cell_tracking total_duration 408min，但拆事件看 **438min 全卡在 `provision_wait`（concurrency 3、72 单元排队），真 agent 只跑 19min**。非僵尸 VM、非 wall_time 失控，纯排队。

**成本现实：** 整个 v0（baseline+候选）已用 ~$60（key 两次撞 $35/$60 上限）。比先前 $50 估计高——印证便宜模型 token 低效。

| 日期 | 步骤 | 动作 | 结果 | 备注 |
|---|---|---|---|---|
| 06-11 | 候选 sweep 完成 | 72 跑（4 模型×18） | deepseek/qwen/glm 干净；kimi 13 废 | key-limit 403 |
| 06-11 | kimi 重跑（暂存） | cand_kimi.yaml，13 个失败题 | ⏳ 待 key 上限提到 ~$75 | account $14.99 够，key $0 headroom 是闸 |

## ✅✅ 2026-06-12 v0 质量×成本表（**已逐项 audit 修正**）

**成本口径：** 每个 run 真实 token 数 × 该模型**真实 OpenRouter 单价**（cache_read×0.1、cache_create×1.25），**不是** transcript 的 Claude 计价 total_cost_usd（那对便宜模型高估 7-14×：DeepSeek 13.9×、Qwen 13.4×、GLM 7.3×）。方法验证：Claude pe_screening 反算 $0.86 = CLI 自报 ✓。

**主表（apples-to-apples：4 模型都跑完的 14 道公共题）：**
| 模型 | quality | vs Claude | $/task | 便宜 |
|---|---|---|---|---|
| Claude sonnet-4.6 | 0.653 | 100% | $0.439 | 1× |
| **GLM-4.6** | **0.497** | **76%** | $0.052 | **8.4×** |
| DeepSeek V3.2 | 0.433 | 66% | $0.162 | 2.7× |
| Qwen3-Coder | 0.377 | 58% | $0.209 | 2.1× |
| Kimi K2 | 路由不可用，排除 | | | |

**关键发现（修正后）：**
1. 没有便宜模型追平 Claude——最高 GLM **76%**。
2. **GLM-4.6 两条线都最优**：76% 质量（候选最高）+ ~8× 便宜。杀手锏 = token 效率（bpmn 同题 GLM 67K input vs DeepSeek 3.3M，实测 49.8×）；DeepSeek 单价低但只省 2.7×。
3. **⚠️ audit 修正了三处错误**（定稿前抓出）：① **DeepSeek 假性领先**——全集它 66% 看似 > GLM 63%，但只因它跳过了两道做不出的难题被无形加分；公共 14 题上 GLM 76% 才真领先。② 一处**伪成本对账**（原写 $23+$37=$60 ✓ 是错的，实际账单 $67.35，差额是 demo/验证/重试 run，非"失败 run"）——已删。③ 倍数四舍五入（3×→实 2.7×；12×→实 8.4×/全集 11.6×）。
4. **Kimi K2 经 OpenRouter+claude_code 不可用**：限流(403)修复后仍撞 provider 400，完成的近 0 分。对 BFC gateway 有意义。
5. **方法学教训：** 跨模型比必须用「都跑完的公共题集」，否则跳题=假性加分；对 Han/对外尤其要守。

**全集数字（N 不等，不可直接比，仅附录）：** Claude 0.664(18) / DeepSeek 0.442(16) / GLM 0.419(17) / Qwen 0.361(17) / Kimi 0.053(15)。
**实际成本：** OpenRouter 账单 $67.35 + GCP ~$10-13（估）≈ $77-80。

| 日期 | 步骤 | 结果 |
|---|---|---|
| 06-12 | 编质量×成本表 + 逐项 audit | ✅ 主表用公共 14 题 apples-to-apples；audit 纠正 3 处错误后定稿；报告 `career-ops/projects/bfc/v0-results-zh.md` |

## 运行流水（每跑一步追加）

| 日期 | 步骤 | 命令 / 动作 | 结果 | bug? |
|---|---|---|---|---|
| 2026-06-09 | 建环境 | clone repo + git init + gh repo create | ✅ 成功，private repo 已推送 | 无 |
| 2026-06-09 | Phase 2 GCP setup | 分阶段跑 quickstart Step 3（project/billing/api/SA/image/vpc/bucket） | ✅ 全绿；project `ale-bfc-eval`，bucket+SA key 就位 | ⚠️ 见下方 bug：quickstart `--name="ALE"` 仅 3 字符，GCP 要求 display name ≥4 → project 没建成、后续全 cascade fail。改 `--name="ALE-eval"` 后通过 |
| 2026-06-09 | 设 budget alert | gcloud billing budgets create $20，scope 限 ale-bfc-eval | ✅ id 1cd73cf3… | 无 |
| 2026-06-09 | Phase 3 装依赖 | `uv sync --all-packages` ❌ → 改 `uv sync`（仅 root） | ✅ root runner 装好 | ⚠️ 见 bug：`--all-packages` 拉 `tasks` 的 torch==2.12，Intel Mac 无 wheel。claude_code agent 零 Python 依赖、tasks 跑在 VM 上不在本地，故 plain `uv sync` 即够 |
| 2026-06-09 | Phase 4 dry-run | `uv run python -m ale_run run example_exp.yaml --dry-run` | ✅ 配置校验过：1 unit = claude_code × demo/hello（Linux）；cleanup_mode=delete | 无 |
| 2026-06-09 | Phase 4 真跑①（后台） | `uv run python -m ale_run run example_exp.yaml`（bg bdhg4707h） | ❌ 71s 失败：us-central1-a 无 n2-standard-8 容量 | ⭐ 见下方 zone 容量分类 bug——非我们 setup 问题 |
| 2026-06-09 | 修 zone 分类 bug | 改 `gcloud.py` 2 处（空白折叠 + 加 pool_exhausted 模式）+ uv 单测验证 | ✅ 原始报错串现判为 retryable，auth 错仍 False | 无 |
| 2026-06-09 | Phase 4 真跑②（后台） | 同命令（bg bvxhctv2u），修复后重跑 | ❌ 103s 失败：报错变成 `failed for all machines/zones`——**证明 fix 生效**（确实跑完 6 组回退），但原 3 zone × 2 机型今天全无 c4/n2-standard-8 容量 | 非 bug，真容量荒 |
| 2026-06-09 | 查 quota | `gcloud compute regions describe` 4 区 | ✅ CPUS/N2_CPUS=200、usage 0、SSD=500——**配额充足，不是配额墙，是 zone 级 stockout** | 无 |
| 2026-06-09 | 扩 zone | `environment.yaml` cpu-free-ubuntu zones 3→10（central1/east1/east4 高配额区） | ✅ 改好 | 无 |
| 2026-06-09 | Phase 4 真跑③（后台） | 同命令（bg b9lhleb1m），10 zone × 2 机型 = 20 组合 | ❌ 374s 失败：**20 组合全 ZONE_RESOURCE_POOL_EXHAUSTED**——fix 彻底验证（确实全扫了一遍 + 0 残留 VM），但今晚 us-central1/east1/east4 **8-vCPU（c4/n2）全网缺货**（PT 晚高峰）。非代码问题，是真容量荒 | 外部容量 |
| 2026-06-09 | 容量探针 | 手动 create e2-standard-4 @ us-central1-a | ✅ 秒建成（已删，0 残留）——**只有 8-vCPU 荒；4-vCPU 的 e2 有货** | 无 |
| 2026-06-09 | 查 Docker | `docker info` | ⚠️ 装了（v29.1.5）但 **daemon 没开**（Docker Desktop 未启动）。Docker 路线（本地跑 Linux 题、$0、绕开 GCP 容量）可行但需先开 Desktop | 待用户开 |
| 2026-06-09 | demo 钉机型 | demo/hello card 加 `"machineType":"e2-standard-4"`（card 本就要 4vcpu/16GB） | ✅ 改好——demo 专用、与判分无关、不动全局默认 | 无 |
| 2026-06-09 | Phase 4 真跑④（后台） | 同命令（bg bvyd50k41），demo 钉 e2-standard-4 | ❌ 218s 失败——但报错变成 **`Quota 'SSD_TOTAL_GB' exceeded. Limit 500`**（不是容量！e2 有货） | 见下方真·根因 |
| 2026-06-09 | 定位真根因 | 查 image 大小 + disk 类型 + 配额 + 有无残留盘 | ✅ **`ale-ubuntu22` image baked 600GB，provider 强制 `pd-ssd`（`_boot_disk_type`，非 c4 都 pd-ssd），单台 VM 就要 600GB SSD > 新项目 SSD_TOTAL_GB=500 → 每台 VM 必崩**。无残留盘（usage=0）。这才是**全 v0 的总闸**——之前 8-vCPU 的 ZONE_RESOURCE_POOL_EXHAUSTED 是另一道独立的容量墙 | 总闸 |
| 2026-06-09 | 请求提配额 | Cloud Quotas REST：SSD_TOTAL_GB us-central1 500→2000 | ⏳ 已提交（pref `ssd-usc1-2k`），**granted 仍 500，reconciling=True（审批中，ETA 不定）** | 待批；真任务（pd-ssd）跑前需它批下来 |
| 2026-06-09 | patch e2→pd-balanced（仅 e2） | `_boot_disk_type` 加 `e2→pd-balanced`（绕 SSD 配额，counts against DISKS_TOTAL_GB 4096）；n2/c4 不变 | ✅ demo VM 首 zone 秒起 | 无 |
| 2026-06-09 | **Phase 4 真跑⑤** | demo（e2 + pd-balanced） | ✅ **`completed, score 1.00, 762.8s`**！boot 4min→agent 7.5min→eval 0.46s→teardown；0 残留 | **里程碑达成** |
| 2026-06-09 | SSD 配额批下 | 查 `ssd-usc1-2k` | ✅ us-central1 SSD granted=2000（~10min 自动批） | 无 |
| 2026-06-09 | 探 n2-standard-8 容量 | 3 zone 探针 | us-central1-a/-b ❌ 仍 EXHAUSTED；**us-east4-a ✅ 有货**——真任务今晚可跑（落 east4） | 无 |
| 2026-06-09 | 提 east4/east1 SSD 配额 | REST 各请 2000（因容量在 east4，但那边 SSD 仍 500） | ⏳ 已提交（`ssd-us-east4-2k`/`ssd-us-east1-2k`），reconciling，约 10min 批 | Phase 5 跑前需批下 |

## 决策记录（边做边记，附"为什么"）

| 日期 | 决策 | 为什么 |
|---|---|---|
| 2026-06-09 | 任务集用 `unlicensed/near-term.txt` | near-term 最便宜/快迭代、top pass ~30% 有区分度；unlicensed 可直接跑，避开 7 道授权跑不起的题 |
| 2026-06-09 | harness 固定 claude_code，只换 `model:` | 干净隔离"模型"这一个变量 |
| 2026-06-09 | 判分按 per-run（整轮） | agent 任务中间步骤单看无意义；ale_run 本就这么判。〔per-run 口径仍待 Han 一句确认〕 |
| 2026-06-09 | 冷启动用 ALE 公开集，不等真实数据 | 线上无真实流量，真实 golden set 暂无米下锅 |
| 2026-06-09 | 默认 VM = `e2-standard-4`（~$0.13/hr）→ 单题 ~$0.03-0.05 | 源码确认（`ale_run/environments/images/ale_ubuntu22.py:28`）；$300 试用已用完，费用直接走卡，故需 budget alert + 确认 VM 有 teardown |
| 2026-06-09 | Phase 2 后设 GCP billing budget alert（~$20，50/90/100% 邮件） | 无试用兜底，stuck VM 闲置 ~$3.2/天；budget alert 是免费保险 |
| 2026-06-09 | Phase 2 只拷 ale-ubuntu22，延后 ale-win10 | v0 Linux-first（42 道 cpu-free-ubuntu + demo 都是 Linux）；win10 仅 13 道 Windows 题需要，等决定跑 Windows 再拷，省时间 |
| 2026-06-09 | 项目名 `ale-bfc-eval`（非 ale-mac） | 全局唯一 + 项目语义清晰；display name 用 `ALE-eval`（≥4 字符，绕开 quickstart bug） |
| 2026-06-09 | 本地 patch ALE 的 zone 容量分类 bug（不等上游） | 否则每轮都受 us-central1-a 缺货摆布、跑不动；修的是重试 plumbing，不碰 task 执行/判分/agent → 对模型 pass/fail 零影响、不损 apples-to-apples。会披露（已记 log，拟告知 Han）。改的是 gitignore 的 ALE clone，可逆 |
| 2026-06-09 | cpu-free-ubuntu zones 3→10 | 8-vCPU 容量按 zone 波动大；ALE 官方给 GPU snapshot 配了 10 zone 正是此理，CPU 只给 3 太少。纯 infra，无成本/效度影响 |
| 2026-06-09 | **Phase 5 真任务跑数排到「美西早晨（~5-9am PT）」做** | 见下方「为什么等美西早晨」——8-vCPU 容量是 GCP zone 级共享物理库存、按时区潮汐波动；今晚（18:00 PT 晚高峰）central1/east1 全 stockout。早晨是低谷、各 zone 健康，多任务×多模型 sweep 才不会被容量荒拖垮 |

## 已知 bug / 上游问题（present 时是「真在跑、发现真问题」的证据）

- **quickstart.md:95 `--name="ALE"`**：GCP 要求 project display name ≥4 字符，`ALE` 仅 3 → `gcloud projects create` 报 `INVALID_ARGUMENT [display_name]`，project 没建成，后续 link billing / enable API 全 `permission denied` cascade。**修法**：display name 用 ≥4 字符（如 `ALE-eval`）。→ 可反馈给 Han（ALE 官方文档 bug）。

- **⭐ zone 容量错误分类 bug（`ale_run/environments/providers/gcloud.py`）—— 实跑 demo 才暴露，含金量最高。**
  - **现象**：Phase 4 demo 第一次跑（run id …231745）71s 失败：`ZONE_RESOURCE_POOL_EXHAUSTED — A n2-standard-8 VM instance is currently unavailable in the us-central1-a zone`。
  - **根因（读码 + 复现确认，非猜测）**：provider 本有「machine × zone」回退（`gcloud.py:808` 双层 for：c4-standard-8→n2-standard-8 × 3 个 zone），但只有 `_is_zone_capacity_error(stderr)` 判为 True 才会回退，否则 `gcloud.py:828` fail-fast。而该判定函数（`gcloud.py:406`）做纯子串匹配，**两处都匹配不上 GCP 最常见的这条容量错误**：① gcloud 把 YAML 错误**折行**，真实串是 `does not have enough\n  resources`，子串 `does not have enough resources`（单空格）匹配失败；② 错误码 `resource_pool_exhausted` 不含子串 `resource_exhausted`（中间多了 `pool_`）。→ 被误判为「非容量错」→ fail-fast → **3 zone 回退一个都没触发，zones[0] 一缺货整轮就死**。us-central1-a 是 GCP 最拥挤的 zone，长期缺 c4/n2-standard-8。
  - **本地修法（已打，2 处，纯重试 plumbing，不碰判分/agent，零影响 benchmark 效度）**：① `_is_zone_capacity_error` 先 `re.sub(r"\s+"," ",…)` 折叠空白再匹配；② `_GCP_RETRYABLE_ZONE` 加 `resource_pool_exhausted`、`currently unavailable`。**已 uv 单测**：用原始报错串验证 → True（可回退）；auth 错 → False（不误伤）。
  - **→ 给 Han 的高价值反馈/PR 候选**：这是「我们真跑 + 读了源码」的硬证据，对作者本人极具说服力。是否提 PR 见 DECISIONS / 待用户定。

- **成本口径修正（重要）**：cpu-free-ubuntu 实际用 `c4-standard-8`→`n2-standard-8`（8 vCPU，`gcloud.py:46 _DEFAULT_CPU_MACHINE`），**非** image 名义默认的 e2-standard-4。约 **$0.34-0.42/hr**。task card 的 `vcpus:4` 仅参考、不决定机型。→ demo（短，~5min）仍 ~$0.05 不变；但**真任务跑 20-120min → 单题 $0.13-0.40**，full near-term × 5 模型 ≈ **$15-40**，$20 budget 可能要提到 $30-50 或缩子集。

## 待确认 / 不确定（不编，留给确认）

- [ ] **Han**：per-run 判分口径确认；ALE 私有题库以后可用范围。
- [ ] **Abby**：各模型计费价格表（填成本列用）；令牌/渠道能否反推 task_type；有无成败信号。
- [ ] **Paul**：达标线档位（90% 中风险默认）等 near-term baseline 出来后锁定。
- [ ] near-term 里挑哪 10–20 题（最好与 linux_only 取交集，省钱）——跑前定。**已有数据：见下方 snapshot 分布，v0 优先取 42 道 `cpu-free-ubuntu`。**

## near-term snapshot 分布（2026-06-09 实测，决定成本与 OS）

| snapshot | OS / 类 | 题数 | 跑在哪 | 免费试用能跑? |
|---|---|---:|---|---|
| `cpu-free-ubuntu` | Linux 无 GPU | **42** | GCP Linux VM 或**本地 Docker（$0）** | 可（但 Docker 本就免费） |
| `cpu-free` | **Windows** 无 GPU | 13 | 仅 GCP Windows VM | ❌ 试用建不了 Windows VM |
| `gpu-license` | Windows+GPU | 3 | GCP GPU VM（贵） | ❌ |
| `gpu-free` | GPU | 1 | GCP GPU VM（贵） | ❌ |

**结论：** 另开 email 拿 $300 试用对本项目**无用**——① 试用建不了 Windows/GPU VM（17 道贵题它一道都跑不了）；② 42 道 Linux 题本地 Docker 本就 $0。且 Google 试用是「每人+每支付方式一次」，非每 email；同卡换 email 注册即被拒。**v0 成本杠杆 = 取 Linux 子集（Docker $0 或 Linux VM ~$0.05/题），Windows/GPU 抽样或延后。**

## 为什么 Phase 5 真任务要等「美西早晨」跑（容量时序）

**核心：8-vCPU 容量是 GCP「zone 级、全客户共享、有限的物理库存」，按时区潮汐波动——不是配额问题**（我们 `N2_CPUS` 配额 200，纹丝没动）。机理：

- **On-demand VM 从每个 zone 的物理库存池里取**，该池由该 zone 内所有 GCP 客户共享。池被抽干 → `ZONE_RESOURCE_POOL_EXHAUSTED`（今晚 central1/east1 全中招）。
- **`c4`/`n2-standard-8`（8-vCPU）家族热门、被抽干最快**；而 demo 用的小号 `e2-standard-4` 池深得多，所以那个有货。
- **需求按时区潮汐**：美区 zone 在美国上班+晚间高峰最满（美国公司的 CI、批处理、autoscaler 全在跑）。我们跑在 **18:00 PT = 接近峰值**，故 8-vCPU 池干了。
- **美西清晨（~5-9am PT）是低谷**：隔夜批处理收尾、白天负载没起来，池子回血，stockout 基本消失。

**实操规矩**：Phase 5 真 sweep（多任务 × 多模型，全要 8-vCPU `pd-ssd` VM）排在**美西早晨**跑，让**所有 zone 都健康**、fallback 顺滑、不把 wall-clock 浪费在 exhaustion 重试上。今晚 `us-east4` 只是恰好有一小块容量，单块不够撑干净的多轮 sweep。

> 注：这是 on-demand 行为。要彻底免疫容量荒可用 reservation/committed（要钱、要预定）或 spot（会被抢占）——v0 不必，错峰跑即可。

## 结果（跑出来再填）

> 质量 × 成本表见 `spec.md` §5；跑完把数填进去，并在此记一句"读法"。

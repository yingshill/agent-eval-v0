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

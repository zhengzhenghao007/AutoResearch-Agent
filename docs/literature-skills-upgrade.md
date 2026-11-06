# 文献研究能力升级实施清单

2026-11-06。审计基线 c238a99。范围为第一阶段的实现准备与关键调用链审计，安全审计及全仓逐行审查尚未完成。本文件中的新增模块均为计划。

## 已有能力与缺口

| 能力 | 实现依据 | 缺口与处理 | 验收标准 |
|---|---|---|---|
| 阅读与反思 | pipelines/reader_pipeline.py、agents/reviewer.py、agents/reflection.py | 旧 Reviewer 以字段长度和关键词评分。主工作台优先使用 services/evidence_review.py 和语义审核服务，保留旧调用兼容性 | 区分格式检查、原文匹配和语义支持三种结果 |
| PDF 阅读 | services/original_pdf.py、frontend/components/ReadingDesk.tsx | 已有原件、OCR、页面搜索、摘录跳页。后续补阅读位置持久化及原件视图体验 | 重开相同论文恢复页面，换论文位置隔离，失效原件显示可恢复入口 |
| 引用核验 | services/evidence_review.py、services/citation_registry.py、services/semantic_review.py | 已有页码原文核验与显式模型语义检查。外部 DOI、撤稿核验仍缺 | 伪造页码、错论文引用、未知证据 ID 被拒绝。外部未核验状态明确 |
| 可恢复执行 | services/research_tasks.py、schemas/research_tasks.py | 已有检查点、租约、取消、来源哈希和预算。工具枚举仅 lexical_retrieve、inspect_sources | 扩展工具仍满足重启恢复、并发去重、预算耗尽停止和旧任务读取 |
| 多论文比较 | services/literature_synthesis.py、frontend/components/ComparisonTable.tsx | 已有分类并排与选择过滤。建议按单篇局限生成，缺跨论文论证及相似工作检索 | 每个候选方向显示依据、反证、研究范围和下一项验证任务 |
| 科学质量评测 | evaluation/、examples/conformal-prediction/ | 有工程和公开材料基线，缺专家标注的空白分析评测 | 单独报告证据绑定正确率、覆盖、错误空白率及人工评审状态 |

已有防护值得沿用：精确引文核验、来源变更失效、显式模型调用同意和受限预算。当前未确认新的阻断级漏洞。上述能力缺口属于重要设计项，审计结论为继续增量开发。

## 第一阶段实施顺序

### 1. 统一技能契约并接入真实执行

新增 schemas/research_skills.py、services/skill_registry.py。每项技能声明 id、version、输入输出 schema、权限需求、执行预算和处理函数。先注册现有两个离线工具，执行器通过白名单 registry 调用。SKILL.md 提供说明，运行权限由服务端契约控制。

持久任务记录技能版本、输入来源哈希、执行结果、错误与预算使用。旧任务缺版本时映射到明确的 v1 处理器。保留当前 API，增加只读能力查询供界面显示可用状态。未知技能、版本不兼容、参数不合法必须在执行前失败。

必要回归包含旧任务恢复、重复注册拒绝、并发执行仅保存一次、来源变化后阻断、取消与预算恢复。以真实任务能完成为交付条件。

### 2. 统一证据核验结果

适配现有 citation registry 与 evidence review，输出逐项 source_id、evidence_id、page、原文匹配、OCR 来源、覆盖范围及语义审核状态。原文匹配成功仅更新对应检查状态。语义审核保持按需调用与版本绑定。

网页在阅读与比较共享核验详情入口，错误项直接定位论文和页面。测试引文跨页、错来源、OCR、空证据及旧缓存失效。无需重新实现引用系统。

### 3. 多论文候选研究问题

新增 schemas/research_gaps.py、services/research_gaps.py，结果保存所选论文与研究目标的哈希。候选项包含问题、作者报告的局限、支持证据、反证或已解决线索、适用范围、未验证事项和建议检索词。默认状态 candidate；用户可标记待查、保留或驳回并记录原因。

离线模式提供结构化局限清单。用户主动开启模型后生成跨论文候选问题，所有引用须落在所选证据中。没有足够证据时返回 insufficient_evidence。来源、选择范围或目标变化使旧报告失效。

比较页增加候选研究问题入口，支持回到原文。相似工作检索保存查询、时间、来源、候选结果和筛选理由。检索无结果时记录检索范围和未知状态。

验收使用相同主题的许可论文，加入已经被另一篇解决的局限、无实验论文、截断论文和冲突结果。必须覆盖取消选择论文、无效引用、模型 429、重复点击、结果保存失败以及刷新恢复。新颖性评分需要单独定义与校准后再引入。

### 4. 贯通计划与评测

候选方向由用户选择后写入研究目标和验证任务。规划显式支持中文问题，目前 _intent 的英文关键词路由需要改进。允许用户编辑子问题，保留选择与修改记录。

建立固定公开许可测试集及人工答案表，记录应找到的证据、已解决的候选问题、遗漏和错误。对比现有单篇局限提示与新结果，分别统计有效引用比例、应检证据召回、错误空白数量和成本。人工科学评测未执行时保持未评测状态。在线服务 429 时保留失败记录和离线结果。

## 外部方案核查与采用方式

2026-11-06 核查公开仓库首页。以下为功能思路适配，尚未引入第三方代码；复制代码前固定提交并检查 LICENSE、NOTICE 和依赖许可证。

| 来源 | 已确认范围 | 本项目采用思路 | 许可状态 |
|---|---|---|---|
| [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | 技能式科研工作流、独立审核 | 执行与审核分工、结构化交接和终止条件 | 首页标识 MIT，逐文件复用前复核 |
| [PaperSpine](https://github.com/WUBING2023/PaperSpine) | 资料驱动的写作、图表与交付流程 | 从研究资料到论证结构，绑定成果依据 | 首页标识 MIT，逐文件复用前复核 |
| [Supervisor-Skills](https://github.com/HKUSTDial/Supervisor-Skills) | 研究评估、导师追问、证据门控写作 | 候选问题的质疑和驳回理由 | 有 LICENSE，具体适配许可待核 |
| [Academic Research Skills](https://github.com/Imbad0202/academic-research-skills) | 研究、写作、审核与修订技能集合 | 明确阶段输入输出和交付要求 | 有 LICENSE、NOTICE、THIRD_PARTY，具体适配许可待核 |

Scientific Agent Skills、Auto-Empirical Research Skills、Academic Figure Generator、Nature Skills、Deep Research Skill 等名称无法仅凭所贴名称唯一确定来源，列为待核实，不计入可复用依赖。

## 交付边界

先完成注册执行、证据核验、候选问题、研究计划的完整入口，再扩展实验执行和论文交付。实验设计、科学计算和自主实验应复用已有数据、统计与执行记录；引入实际计算前补齐权限、成本与复现契约。

阶段结束需满足正常网页入口演示、旧数据回归、失败恢复及质量评测记录。工程测试通过与科学有效性分别记录。当前审计足以细化第一阶段，完整实验及交付模块的逐文件审计安排在对应阶段。

## 第一项交付进度

已接入版本化离线 Skill Registry，现有词面检索与来源核验通过白名单处理器执行。任务持久化 skill_version，旧任务默认 v1。按项目隔离的 GET /api/research/runs/{run_id}/tasks/skills 返回能力描述、权限和输出契约。注册和版本检查、恢复、并发取消、预算及报告回归共 35 项通过。此增量仍使用现有任务输入 schema；跨论文分析、模型技能和前端能力面板待后续实现。

# 科研工具比较与统一实施方案

核查日期 2026-11-06。来源为公开 GitHub 页面及仓库 API；pushed_at 仅说明最近推送，代码质量与可集成性需通过固定版本验证。本轮采用设计思路与官方接口，自行实现适配层。未复制第三方代码。

## 五类能力与来源

| 用户名称 | 找到的具体来源 | 许可证核查 | 采用方式 |
|---|---|---|---|
| Nature Academic Search | https://github.com/dragonadam/nature-skills | GitHub 标识 MIT，最近推送 2026-11-06 | 参考多库检索、去重、引用工作流；官方 API 自行适配 |
| Scientific Brainstorming | https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-brainstorming | MIT，最近推送 2026-11-02 | 参考假设、独立质疑、证据和决策记录 |
| Academic Research Suite | https://github.com/Imbad0202/academic-research-skills-codex | NOASSERTION，最近推送 2026-11-06；具体条款待核 | 参考阶段路由；复用本项目任务执行与 Registry |
| Literature Review | 名称无法唯一定位；评估 https://github.com/Future-House/paper-qa 作为功能替代参考 | Apache-2.0，最近推送 2026-10-26 | 参考科研文献检索和带引用回答；接入前评估模型成本与依赖 |
| Academic Paper Scraper | https://github.com/labrat-0/academic-paper-scraper | GitHub 未识别许可证，最近推送 2026-10-13 | API/MCP 获取思路可参考，代码复用待许可确认 |

同名替代 Academic Paper Scraper 还包括 GAO-pooh/paper-scraper，依赖机构访问和浏览器会话。当前采用开放元数据与获准全文获取。Academic Research Suite 同名仓库包括 weewrr/Academic-Research-Suite，不能仅凭名称判断用户指向哪一项。

## 额外参考仓库

| 项目 | 架构参考 | GitHub 许可标识 / 推送 / 状态 | 本项目决定 |
|---|---|---|---|
| https://github.com/assafelovic/gpt-researcher | 检索、研究和报告流程 | Apache-2.0 / 2026-10-10 / 未归档 | 参考报告与搜索任务交接；整体依赖评估待完成 |
| https://github.com/stanford-oval/storm | 多视角主题规划和引用长文 | MIT / 2025-09-30 / 未归档 | 参考问题展开及大纲；当前维护频率较低 |
| https://github.com/Future-House/paper-qa | 论文检索增强问答 | Apache-2.0 / 2026-10-26 / 未归档 | 参考证据检索与答案依据绑定 |
| https://github.com/SakanaAI/AI-Scientist | 想法、实验、写作循环 | NOASSERTION / 2025-12-19 / 未归档 | 后续实验阶段评估许可证、执行环境和成本 |
| https://github.com/langchain-ai/open_deep_research | 多阶段研究编排 | MIT / 2026-08-10 / 已归档 | 仅参考编排设计；维护替代方案待评估 |

这些状态由 GitHub API 实际返回。NOASSERTION 表示许可证尚未被识别；集成前需阅读完整条款。逐仓核心代码、完整依赖和固定提交复用审查尚未完成。

## 统一架构与现有模块复用

ResearchSupervisor 使用 ResearchTaskExecutor 的任务、租约、来源哈希、预算与事件；Registry 提供白名单版本化技能。MultiSourceSearch 负责标准元数据与检索批次；PaperAcquisition 复用 PaperProcessor、PDF 限制、OCR 和原件存储；Reader 复用证据提取与可选模型速读；Brainstorming 与 LiteratureReview 使用同一份经过校验的论文证据。Reviewer 保持独立。

已检查 agents/planner.py 的固定步骤计划、agents/researcher.py 的 arXiv 包装、workflow/evidence_workflow.py 的候选处理、pipelines/reader_pipeline.py 的 Reader/Reviewer/Reflection 调用，以及现有证据和语义审核入口。LLM Client 与下载器的多源扩展还需专项检查。

### 增量 A — 证据比较与研究问题

先交付所选论文的证据矩阵、局限调查清单、其他论文中的相关段落及缺失项。相关段落按明确词面规则检索，是否支持或反驳由阅读审核决定。来源页码和引用必须可跳转。记录所选范围和输入哈希；目标或来源变更后重新生成。提供可下载的带依据报告。

模型研究问题生成功能后续显式开启，限定引用集合、输出 schema、调用预算和失败行为。创新性保留待验证状态。候选方向须记录支持证据、反证检查、适用范围与下一次检索建议。

### 增量 B — 多源检索

新增标准元数据和检索批次 schema，来源包括 arXiv、Crossref、OpenAlex、Semantic Scholar。每源独立记录查询、时间、状态和错误。精确 DOI 或来源 ID 去重；标题相似仅作为人工核对线索。相关性排序说明依据。DOI 格式、外部登记和论文身份分别记录。

主工作台的既有候选仅接受规范 arXiv PDF URL，多源候选必须先通过新的标准契约，不能直接注入原列表。元数据缺全文时仍可保存。DOI 与引用导出复用现有 citation registry，跨数据库身份需验证后绑定。

官方参考 https://www.crossref.org/documentation/retrieve-metadata/rest-api/ 和 https://api.semanticscholar.org/api-docs/graph 。OpenAlex 当前密钥、配额和访问规则在实现适配器前再次核实。

### 增量 C — 可追溯综述

复用筛选报告和纳入排除记录；提供研究问题、方法、数据集、实验结果、局限的带引用矩阵。主题综述绑定证据集合。系统综述要求检索策略、日期范围、筛选标准、去重记录和排除原因，缺失时显示具体缺项。保存与导出遵守现有版本、批准和来源失效机制。

### 增量 D — Supervisor 与获取

支持用户修改目标并重建计划，旧计划及决策历史可查看。批量获取使用受限后台任务，逐项缓存、校验原件哈希、记录失败和重试。遵守官方服务速率及来源许可。后续实验分析覆盖异常、缺失、反常趋势与候选解释，并绑定数据和计算方法。

## 验收与交付

每个增量覆盖服务单元测试、API 隔离与网页入口；多源测试包括一源失败、限流、重复 DOI、无 DOI、非 OA、错误元数据和分页。跨论文测试包括错来源、相同局限已有解决、无可用证据、选择变化、过期响应和不支持的模型结论。任务测试覆盖暂停、重启、预算、并发取消与用户目标修改。

每次交付记录文件、功能、测试结果、已知限制和下一步。工程检查与科学质量人工评测分别记录。最小可运行版本按 A → B → C 推进，A 与已开始的跨论文分析共用一个实现。

## 增量 A 当前交付

已实现 API 和比较页的离线调查清单，可在选择至少两篇论文后按需生成，显示经过字面来源核验的局限及其他论文中的相关段落，并跳转原文、下载 JSON。报告包含研究目标、所选论文、输入哈希、覆盖及 OCR 提醒。最多展示 20 项局限，每项最多 3 段相关文字。匹配规则为至少两个英语词项重叠，中文词义匹配和模型推理待开发。

当前报告基于保存的论文即时计算，下载可留存本机；刷新页面后可重新生成。持久候选决策、中文分析、多源检索及系统综述生成尚未实现。服务/API 测试 4 项、前端调查与工作区测试 22 项通过。

## 增量 B 首个交付

新增文献库多数据库检索与独立批次历史，支持 arXiv、Crossref、OpenAlex、Semantic Scholar 适配器。每源获取首批最多 20 条，网页默认 5 条；保留查询、时间、来源排名、DOI 来源状态和全部原始元数据记录。精确 DOI 分组；无 DOI 使用来源 ID。跨源排序按源内排名，科学相关性需要用户筛选。

结果保存到项目存储中的 metadata_searches.sqlite3，重新打开后使用 Load saved searches 读取，支持 JSON 下载。每项目上限 100 批次，来源冷却及 Retry-After 记录防止立即重复请求。首次搜索中断时保留开始记录，用户可以稍后明确重试。

已用公开主题完成 Crossref 和 OpenAlex 真实检索，各返回 2 条。arXiv 与 Semantic Scholar 新适配路径尚待真实网络验收。OA 链接是来源报告的可用链接，全文授权、下载与解析仍沿用现有上传和 arXiv 流程。分页、跨库全文自动获取、单独 DOI 身份核对与格式化引用导出待后续补齐。当前 Crossref DOI 状态表示元数据登记，论文身份仍需核对。

可选环境变量 OPENALEX_API_KEY 和 SEMANTIC_SCHOLAR_API_KEY 从后端读取。错误记录不输出请求 URL 或凭据。

## 增量 C 首个交付

比较页新增 Build review material，按所选论文汇总已核验引文，复用现有 manuscript draft 与 screening report，附上多源检索历史和协议缺项。材料可导出 Markdown 与完整 JSON 溯源。预览每章前 5 条，下载包含全部对应引文。来源选择或目标变化会清除旧页面材料。

此增量提供按章节组织的引文材料；模型主题综合、综述协议编辑、跨源筛选决策整合和期刊排版尚待实现。输出保持科学质量未评测，并明确系统综述缺项。新增服务与 API 检查、现有调查测试共 6 项通过，前端综述与工作区 22 项通过。

## 综述协议增量

比较页的综述材料区增加 Review scope and eligibility criteria。用户可加载并编辑研究问题、纳入标准、排除标准、发表时间范围和检索策略。允许先保存不完整草稿；导出按实际空字段提示缺项。

协议单独保存为项目隔离的 SQLite 修订记录，最多 50 版。保存使用 expected_revision 防止旧页面覆盖，冲突返回 409。历史版本可展开查看。综述 JSON 和 Markdown 包含当前保存版本及时间，输入哈希纳入协议。加载或保存协议后清除旧页面材料，异步旧结果不会恢复为当前材料。只读用户可查看历史。

验证覆盖协议历史、项目隔离、冲突、导出哈希变化、正常网页加载保存及现有工作区。5 项后端/API 检查、23 项前端检查、类型检查与生产构建通过。多源元数据的纳入排除事件和已上传论文的统一筛选仍待后续接入。

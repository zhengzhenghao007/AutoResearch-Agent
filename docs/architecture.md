# Evidence-first 架构设计

日期：2026-09-17。设计依据：当前源码审计、GitHub 一手源码快照、同一 ChatGPT 项目中 `c2c_evidence` 的 PLAN。用户已授权方案确定后实现第一阶段。

## 取舍

1. **推荐：增量证据服务。** 保留现有 CLI、Streamlit、`/api/papers/search` 和 `/api/papers/analyze`；新增独立的 evidence workflow 与 `/api/research`。旧分析不是已验证证据，不自动升级旧数据的可信度。
2. 全面改成 LangGraph：可获得状态图，但当前同步小项目还不需要，迁移风险大。
3. 先引入向量库/知识图谱：对规模有帮助，却无法解决伪造引文和缺失实验数据的问题，推迟。

## MVP 与边界

主题 → 结构化研究计划 → arXiv 候选列表 → **显式用户选择** → PDF 获取 → 逐页解析 → problem / method / dataset / experiment / result / limitation / future_work 分类原文证据 → 持久化 → 多论文对照表、文献摘要、探索性问题/实验建议 → 来源校验。

本地 PDF 和在线论文共用 `PaperProcessor`，本地 CLI 接受路径，HTTP 只接受上传内容，不开放任意服务器文件路径。在线入口只接受 arXiv 的 HTTPS PDF，限制大小并拒绝重定向；未来通过 PaperSource 接口扩展其他来源。解析器为 pypdf，不提供 OCR；空白/扫描 PDF 明确报错，不用模型补造文本。

第一版是研究证据工作台，不是投稿级自动论文系统。规则提取器返回字面引文，准确性优先于召回率；显式 LLM 模式使用现有 LLMClient，模型只能选择原文片段和分类，伪造片段被拒绝。没有实验输入时不会生成用户实验结果。分类可能不精确，来源校验不等于科学结论正确。

## 数据契约

- `Source`：来源 ID、标题、类型（paper / user_data）、URI、文档 SHA-256、采集时间。
- `Document`：Source、逐页原文、总页数、已解析页数、truncated；页码从 1 开始。
- `Evidence`：ID、source_id、page、精确 quote；最少 12 字符，必须能在相应页定位。
- `Claim`：ID、text、category、type（paper_report / user_observation / synthesis / hypothesis / suggestion）、evidence_ids、created_by、UTC timestamp。论文报告必须有证据；用户观察必须绑定用户数据来源；假设/建议不能冒充 result 或 experiment。
- `PaperEvidence`：Document、Evidence、Claims、缺失字段、提取器版本。
- `Artifact`：类型、标题、内容、claim_ids/evidence_ids。`ResearchRun` 保存计划、候选、显式选择、论文分析、对照产物、review 和 schema_version。
- 引用由 source_id + 页码 + 原文证据构成，不虚构 DOI、作者或参考文献；ResearchNote 暂由带类型的 Claim 表示，不另建同义实体。

## 职责分配

| 层 | 职责 | 不负责 |
|---|---|---|
| EvidenceWorkflow | 编排阶段、选择校验、调用服务、保存 run | 生成科学事实 |
| Planner / SearchSource | 研究范围与检索；复用 arXiv 工具 | 自动决定纳入所有论文 |
| PaperProcessor | 安全获取与逐页解析 | 推理与写作 |
| Extractor | 分类可定位原文；LLM 是可替换适配器 | 补齐缺失实验 |
| EvidenceReviewer | 交叉引用、来源类型、页码、原文匹配、报告字面支持 | 判断实验是否真实或因果是否成立 |
| LiteratureSynthesis | 已支持证据的比较、缺失项、明确标注的建议 | 宣称全领域 research gap |
| ResearchStore | 版本化 JSON，原子替换，读取校验 | 多用户并发事务/向量检索 |
| FastAPI / CLI | 输入验证、可操作入口 | 另起一套科研逻辑 |

## 推荐结构

```text
schemas/research.py             # evidence-first typed contract
services/paper_processing.py    # shared PDF ingestion
services/evidence_extraction.py # rule and grounded LLM adapters
services/evidence_review.py     # deterministic provenance checks
services/literature_synthesis.py
services/research_validation.py # cross-object snapshot validation
services/research_store.py
workflow/evidence_workflow.py
backend/app/api/research.py     # additive routes
research_cli.py                 # local end-to-end entry point
prompts/evidence_extraction.txt
tests/test_evidence_*.py
```

## 失败与可信度

缺字段返回 missing_fields；读取截断显式保留；解析失败不保存伪造成功产物。LLM 返回错误证据不能静默成为 fact。没有证据不会有“通过”的报告。比较里的缺失仅代表所选论文已读取页面没有提取到内容，不能推出整个领域没有研究。citation support 与科学真实性分开表述，不把模型 confidence 当概率。所有新默认测试离线，真实网络/LLM smoke 明确 opt-in。

## 后续扩展

先引入结构化用户实验输入（数据文件哈希、实验协议、单位、统计方法），再做语义蕴含审查、跨论文矛盾检测和带 citation 的章节写作。全文检索、RAG 和向量索引是 Evidence 的派生索引，不是事实源。异步任务/数据库/多用户认证在服务部署阶段引入。

## 实现收敛说明

- `ResearchRun.generated_claims` 保存独立的 suggestion Claim，不能与 PaperEvidence.claims 混用。research_ideas Artifact 引用生成建议的 ID，建议通过 evidence_ids 回溯论文原文。当前不自动产生 hypothesis；未来增加时沿用这个分层。
- JSON 写入和重载都运行跨对象校验：选择、全局 ID、逐篇引文、review 结果，以及可确定性重建的建议和 artifacts。拒绝不一致快照，不把缓存的 approved 当作事实。该校验不提供防篡改签名，也不能仅凭保存的正文重新证明原 PDF 哈希。
- PDF 使用子进程、45 秒 deadline、20 MiB 输入和一百万提取字符上限。没有 OS 内存配额；HTTP multipart 可能在业务读取前落盘，因此仅限可信本地用户，公开部署还需要请求大小限制、隔离与身份验证。
- 本阶段只有 paper 输入，用户实验数据导入属于下一阶段。Source.kind 与 Claim.claim_type 预留边界并有错配测试；不声称已经实现实验数据分析。
- 研究产物为抽取式摘要和方法并列比较。gap 是已读页面的 evidence coverage gap；建议是基于作者 limitation/future_work 的探索性研究方向，不宣称创新性、因果关系或预测实验结果。

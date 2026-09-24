# 第一阶段实施计划与后续路线

**Goal:** 保留旧功能，新增可以运行、可追溯、不会补造实验结果的研究证据闭环。
**Architecture:** 采用 `architecture.md` 的增量 services + typed domain + workflow；不引入新的多 Agent 框架。
**Tech stack:** Python 3.11+、Pydantic 2、pypdf、FastAPI、pytest；复用 arxiv 和现有 LLMClient。
**Spec:** [architecture.md](architecture.md)

## 全局约束

- 保留用户现有 `frontend/` 和 `requirements-dev.txt` 改动。
- 已报告实验与用户数据必须有真实来源；AI 推测只可为 hypothesis/suggestion。
- 默认无 API key 也能离线运行；网络、付费模型调用只在显式入口发生。
- 原有 `/api/papers` 接口兼容。新增 HTTP API 不接受服务器任意文件路径。

## 实施顺序

### 1. 数据契约、PDF 与来源校验

- [x] 测试：构造两页 PDF，验证页码/截断/文档哈希；伪造 quote、错页、错来源、无证据 result 必须失败。
- [x] 实现 `schemas/research.py`、`services/paper_processing.py`、`services/evidence_review.py`。
- [x] 接口：`PaperProcessor.parse_bytes(data, title, uri) -> Document`；`review_paper(PaperEvidence) -> Review`。
- [x] 运行 `python -m pytest tests/test_evidence_core.py -q`，让 ChatGPT 读取新文件 review。

### 2. 提取、比较、持久化与编排

- [x] 测试：缺失实验保留为空；hypothesis 不能进 result；重载保留证据；未知选择 ID 拒绝；两篇同类证据有引用对照；截断缺失不是 research gap。
- [x] 实现 extractor、synthesis、store、workflow。
- [x] 接口：`EvidenceWorkflow.search(topic, max_results)`、`analyze(run_id, selected_ids)`、`import_pdf(data, title, run_id=None)`，所有入口产出同一 ResearchRun。
- [x] 规则提取优先；显式 LLM 模式复用 `LLMClient.structured_chat`，严格验证模型选出的引文。
- [x] 运行 core + workflow 测试，ChatGPT review 并修复。

### 3. API、CLI、兼容性与文档

- [x] 增加 `/api/research` 与 `research_cli.py`，完成 topic/search/select/import/get 全流程。
- [x] 将在线演示脚本从默认 pytest 收集中隔离，保留手动执行能力。
- [x] API 测试真实 service/store，mock 只限网络源；测试 malformed PDF、空主题、坏 ID、过大文件。
- [x] 全量离线测试（44 项通过）、CLI smoke、README 使用说明已完成；ChatGPT 最终 review 为 DONE。

## 后续里程碑

1. 人工标注提取评测集：分类精度、quote 定位率、missingness、支持率；不得只用“报告好看”衡量。
2. 语义审查器 + 有限反思：基于证据提出更正，不强迫填满字段；保留前后版本。
3. 用户实验数据模型：单位/协议/表格字段/样本量/统计方法；支持数据质量检查而非补造结果。
4. 引文注册表（DOI/arXiv/BibTeX）、多来源检索去重、撤稿信息、人类纳入排除记录。
5. 章节规划与写作：每句可回溯 Claim；无实验的章节呈现待补信息；人类审阅出口。
6. 上传 UI 与证据查看器、后台任务、权限控制和事务数据库，再评估 RAG/知识图谱。

## 当前交付限制

只生成结构化 suggestion，不主动生成 hypothesis；用户实验输入与完整写作在后续里程碑。保留旧前端功能，新增证据工作台接入搜索、选择、上传、历史和逐页查看；CLI/API 继续可用。JSON 为单用户快照，不支持并发修改同一个 run 的事务隔离。

## 后期实施顺序与验收门槛

以下为建议排期，以验收通过决定进入下一阶段，不承诺固定完成日期。先建立可评估的研究工作台，再扩展科研推理和写作。

| 阶段 | 交付物 | 验收标准 | 前置条件 |
|---|---|---|---|
| P0：可靠性基线 | 离线 CI、依赖版本策略、人工标注文献样本集 | 每次 PR 自动运行现有 44 项及新增测试；所有虚构引文负例拒绝；按类别报告精确率、召回率与缺失率 | 当前 MVP |
| P1：证据工作台 | 搜索选择、PDF 上传、研究历史、逐页证据查看、明确的失败/空状态 | 用户能在 UI 完成两篇论文比较，并从每条输出跳回原文；刷新后记录仍可读；不把来源通过显示成科学真实性通过 | P0 基线 |
| P2：文献与语义质量 | DOI/arXiv 引文注册表、去重、纳入/排除理由、语义支持审查、有限修订 | 每个 claim 可追溯；人工标注集能测量矛盾/不支持检测；修订有预算和历史，不能靠补造内容通过 | P0；可与 P1 分开交付 |
| P3：真实实验输入 | CSV/JSON 观测、协议、单位、样本量、数据哈希、缺失值和统计检查 | paper_report、user_observation、hypothesis、suggestion 严格分离；所有计算可从输入重现；缺失数据不生成结果 | P2 数据契约稳定 |
| P4：有证据的写作 | 章节规划、段落草稿、逐句引用、矛盾审查、修订记录和导出 | 事实句可定位到 evidence/真实计算；缺失实验明确占位；人工批准后导出，不宣称自动可投稿 | P2；实验章节还依赖 P3 |
| P5：规模与部署 | 后台任务、取消/重试、事务存储、认证授权、资源限额 | 并发修改无静默覆盖；上传大小在解析前限制；解析进程有内存/CPU限制；权限隔离测试通过 | 确认多人或大规模需求后 |

### 下一轮建议：P0 + P1 的最小闭环

**Goal:** 让研究者在页面里检查并纠正现有 evidence，而不是先增加更多 Agent。

**Architecture:** 复用 `/api/research` 和 ResearchRun；前端展示来源和研究状态，不另建推理流程。已有 frontend 属于独立未提交工作，实施前先读取其 AGENTS.md、依赖及页面结构并协调现有改动。

**涉及文件：** `.github/workflows/tests.yml`（新增离线 CI）；`tests/fixtures/evidence/` 与 `evaluation/`（授权样本和人工标签）；`backend/app/api/research.py`（按 UI 需求增加分页/历史读取）；`frontend/` 内实际页面、API client 和测试路径在检查当前结构后确定，不预先假设路由布局。

- [x] 建立 CI 配置：新环境安装明确的测试依赖；默认不注入 provider key，不运行 `--run-live`；失败时检查不通过；强制阻止合并还需仓库配置 required checks。
- [ ] 建立小型可再分发评测集，涵盖正常文字、扫描页、截断、未报告实验、计划实验及不支持的引用；保存人工标签和来源许可。当前已提供 7 个有许可的合成回归样本及评测工具，包含空文本和无文字层的图像型页面（非真实论文 OCR 基准）；全部标签为 pending_human_review，人工审核门槛仍未完成。
- [x] 用失败测试定义研究历史列表与详情契约，再增加最小实现；确认旧接口响应兼容。
- [x] 实现搜索 → 显式选择 → 分析的页面链路；长任务必须有可辨认的状态，不能把超时当成功。
- [x] 实现上传 → 同一研究记录 → 比较；加入文件重复、解析失败、空证据和刷新恢复测试。
- [x] 实现 evidence 面板：原文、页码、来源、claim_type、缺失类别、截断提示；建议与论文原话有独立标签。
- [ ] 合并验收：真实页面流程与独立代码审查已执行并修复发现；验证范围见 p0-p1-implementation.md。本轮仅推送开发分支，不执行合并；人工评测仍待完成。

每个任务按“失败测试 → 最小实现 → 回归 → 审查 → 单独提交”交付。采用 `superpowers:executing-plans` 逐项执行；这份规划本身不启动下一阶段实现。

### 暂缓事项

在没有检索规模或性能测量前不引入向量数据库/知识图谱；在没有标注评测前不堆叠反思 Agent；在没有真实实验输入前不生成实验结果章节。模型 confidence 不作为科学证据强度的替代品。

### P0 验收补充（2026-09-24）

- [x] 图像型 PDF：嵌入原创像素、没有文字层，验证明确拒绝无可读文本输入。
- [x] 样本生成器默认拒绝覆盖已有清单或 PDF，避免重生成抹去审核成果；使用新输出目录比较变更。
- [ ] 真实人工标注和有许可的代表性论文评测仍待完成；不得由自动化补写审核人。

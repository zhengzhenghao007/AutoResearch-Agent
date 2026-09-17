# GitHub Research Agent 工程调研

调研日期：2026-09-17 UTC。基于 GitHub REST 仓库元数据、递归树以及固定 tree SHA 的 README/关键源码。原始元数据见 [research_sources.json](research_sources.json)，已阅读源码的 URL、哈希与长度记录见 [research_code_samples.json](research_code_samples.json)。**Stars 不等于质量；updated_at 可因元数据变化更新，代码活跃度以 pushed_at 辅助判断。** 未运行这些项目的测试，测试存在性不代表通过。无 license/NOASSERTION 不是可自由复制许可。

## 快照与选择

| 项目 | Stars | 最近 push (UTC) | GitHub updated | License | 归档 |
|---|---:|---|---|---|---|
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | 12,682 | 2026-08-10 | 2026-09-16 | MIT | 是 |
| [langchain-ai/local-deep-researcher](https://github.com/langchain-ai/local-deep-researcher) | 9,348 | 2026-08-23 | 2026-09-17 | MIT | 否 |
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | 29,490 | 2026-08-27 | 2026-09-17 | Apache-2.0 | 否 |
| [Future-House/paper-qa](https://github.com/Future-House/paper-qa) | 9,208 | 2026-09-17 | 2026-09-17 | Apache-2.0 | 否 |
| [stanford-oval/storm](https://github.com/stanford-oval/storm) | 31,420 | 2025-09-30 | 2026-09-17 | MIT | 否 |
| [HKUDS/AI-Researcher](https://github.com/HKUDS/AI-Researcher) | 5,745 | 2025-10-16 | 2026-09-17 | 未识别 | 否 |
| [SakanaAI/AI-Scientist](https://github.com/SakanaAI/AI-Scientist) | 14,566 | 2025-12-19 | 2026-09-17 | NOASSERTION | 否 |
| [SakanaAI/AI-Scientist-v2](https://github.com/SakanaAI/AI-Scientist-v2) | 7,163 | 2025-12-19 | 2026-09-17 | NOASSERTION | 否 |
| [SciPhi-AI/R2R](https://github.com/SciPhi-AI/R2R) | 7,997 | 2025-11-07 | 2026-09-16 | MIT | 否 |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 90,872 | 2026-09-17 | 2026-09-17 | Apache-2.0 | 否 |

优先参考 PaperQA 的证据数据层、GPT Researcher 的工具适配和错误测试；STORM 的整理/写作分离次之。保留两个 AI Scientist 版本用于比较实验执行边界，不建议直接依赖。R2R/RAGFlow 是知识基础设施对照。

## langchain-ai/open_deep_research

- **目标与栈：** 多提供商深度研究；Python/LangGraph。
- **Agent / workflow / LLM：** clarify → brief → supervisor → researcher tools → 压缩 → final report；state.py 分离状态，init_chat_model 调用。
- **搜索 / PDF / RAG / memory / citation / review：** 网页检索/MCP；非专门 PDF reader。状态内 notes 是过程记忆，报告引用 URL；researcher 有工具迭代/压缩。
- **目录 / 配置 / prompt / 测试 / 前后端：** configuration.py + prompts.py；LangGraph Studio/OAP 前端；tests 是 benchmark/evaluators，不等于离线单测。
- **适用与不适用：** 借鉴阶段状态和预算限制；不要把 graph 框架引入小型 MVP。已归档，不作为新依赖。
- **源码证据：** [README.md](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/README.md), [src/open_deep_research/deep_researcher.py](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/deep_researcher.py), [src/open_deep_research/state.py](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/state.py).
- **抽样测试结构：** `src/legacy/tests/conftest.py`, `src/legacy/tests/run_test.py`, `src/legacy/tests/test_report_quality.py`, `tests/evaluators.py`

## langchain-ai/local-deep-researcher

- **目标与栈：** 本地模型研究；Python/LangGraph/Ollama/LMStudio。
- **Agent / workflow / LLM：** generate_query → web_research → summarize → reflect → 循环/结束；graph.py 可读性高。
- **搜索 / PDF / RAG / memory / citation / review：** DuckDuckGo/Tavily 等检索；引用来自状态中的 sources；无本次确认的专用论文 PDF/RAG 持久索引。
- **目录 / 配置 / prompt / 测试 / 前后端：** configuration.py、prompts.py、.env；Studio UI；快照未发现常规 tests 目录。
- **适用与不适用：** 借鉴有限反思、可替换本地 LLM；网页综述不能代替页码证据与实验输入。
- **源码证据：** [README.md](https://github.com/langchain-ai/local-deep-researcher/blob/a53b13c7022bb1352dc1ca994d07ade3cd3bd62e/README.md), [src/ollama_deep_researcher/graph.py](https://github.com/langchain-ai/local-deep-researcher/blob/a53b13c7022bb1352dc1ca994d07ade3cd3bd62e/src/ollama_deep_researcher/graph.py).
- **抽样测试结构：** 本次树快照未确认常规测试文件；不推断完全没有验证。

## assafelovic/gpt-researcher

- **目标与栈：** 通用研究报告；Python/Next.js/LangGraph。
- **Agent / workflow / LLM：** GPTResearcher 核心 facade；conduct_research 与 write_report 分离；可选多 Agent plan/review/revise。
- **搜索 / PDF / RAG / memory / citation / review：** retrievers 抽象，arXiv/OpenAlex 等；local/hybrid 文档与 RAG、embeddings、memory；引用和 fact-review。
- **目录 / 配置 / prompt / 测试 / 前后端：** config/ 与 prompts.py；backend/、frontend/nextjs/；tests/ 有引用顺序、retriever 异常、revision cap 测试。
- **适用与不适用：** 借鉴 provider/retriever 边界、引用校验和修订上限；不搬入整套全栈多 Agent 平台。
- **源码证据：** [README.md](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/README.md), [gpt_researcher/agent.py](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/agent.py), [gpt_researcher/retrievers/base.py](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/retrievers/base.py).
- **抽样测试结构：** `tests/__init__.py`, `tests/backend/test_report_chat_route_uniqueness.py`, `tests/backend/test_write_md_to_pdf_filename.py`, `tests/chat/test_chat_agent_rag_path.py`

## Future-House/paper-qa

- **目标与栈：** 科学文档问答；Python/Pydantic/LiteLLM。
- **Agent / workflow / LLM：** agentic retrieval → evidence contexts → answer with citations；Doc/Text 与 Settings 为清晰边界。
- **搜索 / PDF / RAG / memory / citation / review：** PDF parser 插件（pypdf/pymupdf/docling 等）；本地全文/向量检索；元数据与撤稿查询；证据缓存和引用键。
- **目录 / 配置 / prompt / 测试 / 前后端：** settings.py + prompts.py；Python library/CLI 为主；tests 与录制网络 cassettes 较完整。
- **适用与不适用：** 最优先借鉴 document/evidence/citation 分层；问答并非实验数据分析或整篇写作。
- **源码证据：** [README.md](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/README.md), [src/paperqa/types.py](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/types.py), [src/paperqa/settings.py](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/settings.py).
- **抽样测试结构：** `packages/paper-qa-docling/tests/test_paperqa_docling.py`, `packages/paper-qa-nemotron/tests/conftest.py`, `packages/paper-qa-nemotron/tests/test_api.py`, `packages/paper-qa-nemotron/tests/test_paperqa_nemotron.py`

## stanford-oval/storm

- **目标与栈：** 知识整理/百科长文；Python/DSPy。
- **Agent / workflow / LLM：** knowledge curation → outline → article generation → polishing；engine.py + interface.py 明确模块接口。
- **搜索 / PDF / RAG / memory / citation / review：** 可替换 retrieval；多视角问题/对话记忆、来源引用；不是默认科研 PDF 实验提取器。
- **目录 / 配置 / prompt / 测试 / 前后端：** lm/rm 配置、DSPy signatures；examples + frontend/demo_light；本次树未见完整常规 tests 套件。
- **适用与不适用：** 借鉴先知识整理后写作；近期代码活跃度弱，不能视为投稿质量保证。
- **源码证据：** [README.md](https://github.com/stanford-oval/storm/blob/fb951af7744dab086e34962e9bc6fe878e145f83/README.md), [knowledge_storm/storm_wiki/engine.py](https://github.com/stanford-oval/storm/blob/fb951af7744dab086e34962e9bc6fe878e145f83/knowledge_storm/storm_wiki/engine.py), [knowledge_storm/interface.py](https://github.com/stanford-oval/storm/blob/fb951af7744dab086e34962e9bc6fe878e145f83/knowledge_storm/interface.py).
- **抽样测试结构：** 本次树快照未确认常规测试文件；不推断完全没有验证。

## HKUDS/AI-Researcher

- **目标与栈：** 自主科研创新；Python/LiteLLM/Docker。
- **Agent / workflow / LLM：** research_agent/inno 的 MetaChain、registry 注册 agents/tools；paper_agent 分章节生成。
- **搜索 / PDF / RAG / memory / citation / review：** 检索/创新规划/代码实验/论文写作分离；有 benchmark；论文与任务上下文，不等同于强 claim provenance。
- **目录 / 配置 / prompt / 测试 / 前后端：** .env.template、constant.py、prompt 文件；research_agent/、paper_agent/、benchmark/；不是轻量现成网页应用。
- **适用与不适用：** 借鉴 registry 和阶段产物；GPU/容器自主实验超出 MVP；API 未识别 license，不复制代码。
- **源码证据：** [README.md](https://github.com/HKUDS/AI-Researcher/blob/f9a6f8480860c193afff600eeffe3defcee8a978/README.md), [research_agent/inno/core.py](https://github.com/HKUDS/AI-Researcher/blob/f9a6f8480860c193afff600eeffe3defcee8a978/research_agent/inno/core.py), [research_agent/inno/registry.py](https://github.com/HKUDS/AI-Researcher/blob/f9a6f8480860c193afff600eeffe3defcee8a978/research_agent/inno/registry.py).
- **抽样测试结构：** `examples/con_flowmatching/project/run_training_testing.py`, `examples/con_flowmatching/project/run_training_testing_v2.py`, `examples/con_flowmatching/project/testing/evaluator.py`, `examples/con_flowmatching/project/testing/scores.py`

## SakanaAI/AI-Scientist

- **目标与栈：** 自主实验到论文；Python/PyTorch/LLM SDK。
- **Agent / workflow / LLM：** idea → perform_experiments → plotting → writeup → review/reflection；模板化实验目录。
- **搜索 / PDF / RAG / memory / citation / review：** Semantic Scholar/OpenAlex 文献；PDF 审稿加载；保存实验结果供写作；不是通用多用户 RAG 系统。
- **目录 / 配置 / prompt / 测试 / 前后端：** ai_scientist/llm.py、prompt 字符串、templates/；CLI 主导；review_iclr_bench 为评测而非完整单测。
- **适用与不适用：** 借鉴真实运行结果与写作分离；不自动执行模型代码，不照搬 GPU 环境；license 为 NOASSERTION，须逐条审查。
- **源码证据：** [README.md](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/README.md), [ai_scientist/perform_experiments.py](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/ai_scientist/perform_experiments.py), [ai_scientist/perform_review.py](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/ai_scientist/perform_review.py).
- **抽样测试结构：** 本次树快照未确认常规测试文件；不推断完全没有验证。

## SakanaAI/AI-Scientist-v2

- **目标与栈：** 树搜索式自主科研；Python/多模型/GPU。
- **Agent / workflow / LLM：** AgentManager 分阶段与 checkpoint；best-first tree search 实验后写作/LLM review。
- **搜索 / PDF / RAG / memory / citation / review：** Semantic Scholar 辅助 novelty/citation；实验 journal 和结果分析；不把生成 idea 当测量值。
- **目录 / 配置 / prompt / 测试 / 前后端：** bfts_config.yaml、ideas/、treesearch/；CLI，未确认成熟独立前后端或全面单测。
- **适用与不适用：** 借鉴阶段检查点和预算；成本/沙箱/实验树复杂度不适合本 MVP；自定义 license。
- **源码证据：** [README.md](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/README.md), [ai_scientist/treesearch/agent_manager.py](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/ai_scientist/treesearch/agent_manager.py).
- **抽样测试结构：** 本次树快照未确认常规测试文件；不推断完全没有验证。

## SciPhi-AI/R2R

- **目标与栈：** 检索基础设施；Python/REST/SDK/Postgres。
- **Agent / workflow / LLM：** retrieval service + AgentFactory；ingest → hybrid retrieval/HyDE/fusion → RAG agent。
- **搜索 / PDF / RAG / memory / citation / review：** 多模态/PDF ingestion、graph/向量混合、citation spans、文档与 collection；不是专门实验 Reviewer。
- **目录 / 配置 / prompt / 测试 / 前后端：** TOML 配置、prompt provider；py/core/、py/sdk/、js/sdk/；CI light/full integration tests。
- **适用与不适用：** 借鉴 ingestion/service/API 分层；部署、权限和数据库成本高，当前只需 JSON run store。
- **源码证据：** [README.md](https://github.com/SciPhi-AI/R2R/blob/9c5a94d151f90876bd7eb860f300a8fd662dc481/README.md), [py/core/main/services/retrieval_service.py](https://github.com/SciPhi-AI/R2R/blob/9c5a94d151f90876bd7eb860f300a8fd662dc481/py/core/main/services/retrieval_service.py), [py/README.md](https://github.com/SciPhi-AI/R2R/blob/9c5a94d151f90876bd7eb860f300a8fd662dc481/py/README.md).
- **抽样测试结构：** `js/sdk/__tests__/ChunksIntegrationSuperUser.test.ts`, `js/sdk/__tests__/CollectionsIntegrationSuperUser.test.ts`, `js/sdk/__tests__/ConversationsIntegrationSuperUser.test.ts`, `js/sdk/__tests__/ConversationsIntegrationUser.test.ts`

## infiniflow/ragflow

- **目标与栈：** 文档解析与 Agent RAG；Python/Go/TypeScript。
- **Agent / workflow / LLM：** canvas DSL 编排 component/tools；ingestion → chunking → retrieval → agent/report。
- **搜索 / PDF / RAG / memory / citation / review：** DeepDoc PDF/OCR/布局；arXiv/PubMed/Scholar 工具；知识库/引用/记忆模块；有 reflective academic 模板。
- **目录 / 配置 / prompt / 测试 / 前后端：** agent/templates、conf、web、api/internal；大量 *_test.go 与 Python tests；可视化前后端。
- **适用与不适用：** 借鉴页/块溯源与工具接口；完整产品很重，OCR/向量检索以后按需要适配。
- **源码证据：** [README.md](https://github.com/infiniflow/ragflow/blob/aff4273476ee1662fe63107a1c9b8e50446ce897/README.md), [agent/tools/arxiv.py](https://github.com/infiniflow/ragflow/blob/aff4273476ee1662fe63107a1c9b8e50446ce897/agent/tools/arxiv.py), [agent/canvas.py](https://github.com/infiniflow/ragflow/blob/aff4273476ee1662fe63107a1c9b8e50446ce897/agent/canvas.py).
- **抽样测试结构：** `agent/sandbox/executor_manager/tests/conftest.py`, `agent/sandbox/executor_manager/tests/test_artifact_promotion.py`, `agent/sandbox/executor_manager/tests/test_run_endpoint_security.py`, `agent/sandbox/tests/__init__.py`

## 横向结论及对本项目的映射

| 需求 | 参考模式 | 我们的选择 |
|---|---|---|
| 文献出处 | PaperQA Doc/Text/context 与 citation | Source/Document/Evidence/Claim，逐页原文匹配 |
| 工作流 | Open Deep Research state，STORM staged engine | 先同步 EvidenceWorkflow，不新增调度框架 |
| 可替换外部系统 | GPT Researcher BaseRetriever，STORM interfaces | arXiv source、PDF parser、LLM extractor 小接口 |
| 缺失与反思 | local-deep-researcher 限次循环 | 缺失不强行补齐；规则失败清晰可见 |
| 真实实验 | AI Scientist 实验产物先于 writeup | 用户实验输入独立类型；本阶段不运行自动实验 |
| 可恢复与存储 | v2 checkpoints，R2R collection | 原子 JSON run store，保存来源和选择 |
| 文档质量 | RAGFlow DeepDoc | pypdf 起步；扫描件拒绝，后续 OCR 不伪造文本 |
| 可信输出 | citations + independent review | 校验来源与引用，不把模型自评作为科学真实性证明 |

## License 与调研限制

不复制任何第三方实现。MIT/Apache-2.0 仍需遵守相应通知条款；HKUDS 未识别 license、Sakana 自定义 license 的复用需要另行核对具体条款。此报告为代码结构抽样审查，不是漏洞审计或性能测评。持久记忆、完整论文写作、语义事实审查如在抽样文件中没有证据，均不因 README 营销词默认认定成熟。MVP 采用本项目自己实现的最小边界。

# 当前代码审计（实现前快照）

2026-09-17，基线 commit `c4b7ead`，分支 `feature/fullstack-web`。用户已有修改：`requirements-dev.txt` 和未跟踪 `frontend/`。本次不改这两处。审计通过直接读源码并让 ChatGPT 使用只读连接器独立检查完成，非依据 README 推断。

## 实际能力与成熟度

| 模块 | 代码证据 | 结论与处理 |
|---|---|---|
| Planner | `agents/planner.py:2` | 固定五步字符串模板，不是自适应研究规划；保留，新增结构化 plan |
| Researcher | `agents/researcher.py:5`, `tools/arxiv_search.py:4` | arXiv relevance 检索，含作者/摘要/entry_id；可用适配器，保留 |
| 工作流 | `workflow/research_workflow.py:135,173,306` | 搜索与选择后单篇分析已分离；按 index 选择、下载、读前5页，auto 模式回退；保留旧 API，新增 run-based 编排 |
| PDF | `tools/pdf_reader.py:7,26` | requests 整体下载；pypdf 逐页提取但拼成字符串。README 写 PyMuPDF 不符实现。下载无大小/目的地址约束，标题文件名可能覆盖 |
| LLM Reader | `agents/llm_reader.py:35,128` | 有结构化输出与禁止虚构 prompt；40k 字符截断；结果仍是无证据字符串。不可当作已验证事实 |
| 规则 Reader | `agents/reader.py:8` | 关键词选句、兜底文本；有明确缺失提示，但丢页码和 claim 级来源。保留 legacy 功能 |
| Reviewer | `agents/reviewer.py:96` | 检查字段、最短长度、泛化 limitations；没有源文本参数，无法验证来源。approval 不代表科学真实 |
| Reflection | `pipelines/reader_pipeline.py:50` | 有有限 retries、attempt history、token/latency 统计；值得保留，不应用来强行填齐缺失事实 |
| LLM 服务 | `services/llm_client.py:51,149` | OpenRouter/ChatOpenAI、structured fallback 和修复已集中；可复用，后续抽协议。日志/异常可能回显模型内容，应限制在本地 |
| 数据模型 | `schemas/paper_analysis.py:4` | 缺 experiment/result/future_work、source、evidence、citation；空值规范化为占位文本，不等于有信息 |
| API | `backend/app/api/papers.py`, `analysis.py` | 实际路由是 `/api/papers/search` 和 `/api/papers/analyze`，不是独立 `/api/analysis`。response 多处 Any；保持兼容 |
| 本地 PDF | `app.py:642` | Streamlit 已有上传和临时文件删除；FastAPI 没有上传接口。新闭环两类输入共用处理器 |
| 前端 | `frontend/lib/api.ts`, `frontend/types/paper.ts` | 已有独立 Next.js 工作目录，依赖旧接口；本次不覆盖用户修改 |
| memory/prompts | 目录存在但无已跟踪实现 | 缺长期存储和版本化 artifact；新增小型 run store 和独立 prompt |

## 测试基线

系统 Python 缺 `langchain_openai`，默认 pytest 收集出现4个导入错误。仓库 `.venv/Scripts/python.exe` 依赖齐全。实际离线测试只有 `test_json_parser.py` 中2个测试，均通过。其余4份 `test_*.py` 是模块顶层实例化模型并打印的在线演示，不应默认 CI 收集或无意消耗 API 额度。保留它们的手动运行能力，改成显式 opt-in 的 live tests；新增有断言的离线测试。

## 主要架构问题

- Workflow 构造时连同 provider 一起初始化，搜索 service 需指定 rule 才避免加载模型；新工作流采用按需构造。
- 传递 dict/Any，schema 与 ReaderResult 存在格式转换（list → string），不利于来源追踪。
- 在线/本地读取在 UI 与 workflow 重复，新增统一 processor，不强迫旧入口立即迁移。
- 缺“候选/选择/证据/对比/审查”持久状态，无法复现一次输出。
- 没有出处不代表没有研究；截断的文本不能支持全领域 novelty 断言。
- HTTP 下载路径缺限制，异常详情透传；本阶段新接口 fail-closed，旧接口的安全加固列为后续兼容性工作。

## 需要独立的模块

Provider 用协议适配，先包住现有 LLMClient；paper source 先 arXiv；parser 先 pypdf；citation/provenance 直接进入 typed contract。memory 首先是持久研究记录，不是给模型一段无限增长的聊天历史。实验数据是独立 Source kind，第一版不伪装已经支持 CSV 统计。保留模型级验证与 source-level reviewer 两道不同门。

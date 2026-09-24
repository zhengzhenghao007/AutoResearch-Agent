# AutoResearch-Agent

> A Multi-Agent Literature Review System powered by Large Language Models.

AutoResearch-Agent is a research-assistant prototype with an evidence-first literature MVP. It searches arXiv, processes selected papers or uploaded PDFs, preserves page-level quotations, and produces extractive comparisons with explicit evidence gaps. It does not generate or validate experimental results on behalf of a researcher.

The long-term goal is to build an autonomous research workflow similar to OpenAI Deep Research, but focused on academic literature analysis.

## Evidence-first MVP (2026-09)

The new workflow is additive: the existing Streamlit UI and `/api/papers/search` and `/api/papers/analyze` remain available. Their legacy review scores are **not** provenance certification. The new evidence workflow is available through the CLI and `/api/research`; the Next.js evidence workspace now connects to these endpoints alongside the legacy interface.

Read the [10-project engineering survey](docs/research_agent_landscape.md), [current-code audit](docs/current_architecture_audit.md), [architecture and data contracts](docs/architecture.md), and [implementation roadmap](docs/roadmap.md).

### Install and run (PowerShell, Python 3.11+)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest httpx

# Search returns a run ID and candidate IDs; it does not download all candidates.
.\.venv\Scripts\python.exe research_cli.py search "vision-language robot navigation" --max-results 5
.\.venv\Scripts\python.exe research_cli.py analyze RUN_ID CANDIDATE_ID_1 CANDIDATE_ID_2

# Local PDFs use the same page extraction, evidence, review and comparison services.
.\.venv\Scripts\python.exe research_cli.py import-pdf "C:\papers\paper.pdf"
.\.venv\Scripts\python.exe research_cli.py import-pdf "C:\papers\second.pdf" --run-id RUN_ID
.\.venv\Scripts\python.exe research_cli.py show RUN_ID
```

Replace the uppercase IDs with values from the previous JSON response. Outputs are persisted atomically in `data/research_runs/` (git ignored). `--store PATH` selects another directory. Default `--mode rule` needs no LLM key; it is deliberately conservative and may miss relevant information. `--mode llm` explicitly uses the existing OpenRouter configuration and may incur provider charges; the model can only select quotations and categories, and fabricated quotations are rejected. No live model is called by the default test suite.

Each paper records its content hash, parsed pages, total page count, truncation, source-linked evidence, typed claims and missing categories. Reports are literal paper quotations, not independently verified scientific facts. The comparison includes supported extracts, methods side by side, coverage gaps and explicitly labelled exploratory suggestions. No input experiment means no invented user result. Coverage gaps are not proof of novelty or gaps in the entire research field.

### HTTP API

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive request schemas:

| Method | Endpoint | Input |
|---|---|---|
| POST | `/api/research/search` | JSON `topic`, optional `max_results` (1–20) |
| POST | `/api/research/runs/{run_id}/analyze` | JSON `selected_ids` from that run |
| POST | `/api/research/upload` | multipart `file`, optional `run_id` |
| GET | `/api/research/runs` | `page` (default 1), `page_size` (1–50, default 10); summaries and total |
| GET | `/api/research/runs/{run_id}` | persisted research record |

The API uses rule extraction. Explicit LLM mode is currently a CLI capability. Uploads accept PDF bytes, never server filesystem paths. Parsing runs in a separate process with a 45-second timeout, a 20 MiB input limit, 50-page default and one-million-character extracted-text cap. Encrypted or unreadable/scanned PDFs fail explicitly; OCR is not implemented. Downloads accept canonical HTTPS arXiv PDF URLs only and reject redirects. The server is a **local single-user development service**, with no authentication, multi-writer transactions, or OS-enforced parser memory quota. Do not expose it as an untrusted public upload service.

### Offline tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

If Windows denies access to an old pytest temporary directory, use a fresh `--basetemp` path. Four legacy `test_*.py` provider demos run code at import time; they are excluded by default. `--run-live` explicitly opts into those demos and requires working provider credentials/network; they are not counted as deterministic unit tests. The offline suite tests real generated PDFs, fake network/provider adapters, citations, missing evidence, persistence and API behavior.

Next: actual human review of the evaluation corpus, structured user experimental inputs, and semantic claim support review. Full paper writing and automatic experiment execution remain outside this MVP.

### Evidence workspace

Start the API above, then in a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. Search creates a record; select candidates explicitly before choosing **Analyze selected papers**. Add multiple PDFs to the same record for comparison, or choose **New record** first. History reopens saved records and the `?run=` URL survives refresh. Evidence and claim links lead to quotations and extracted pages; canonical arXiv sources also link to the original PDF page. Suggestions remain separate from reported claims. Source support means literal provenance, not scientific validity.

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://127.0.0.1:8000`; set it before building if needed. A request timeout does not cancel server work: refresh history and reopen the record before retrying. The legacy interface remains below the evidence workspace.

### Reproducible checks and evaluation

```powershell
python -m pip install -r requirements-ci.txt
$env:PYTHON_DOTENV_DISABLED='1'
python -m pytest tests -q -p no:cacheprovider --allow-hosts=127.0.0.1,::1
python -m evaluation.evaluate_evidence
cd frontend
npm ci
npm test
npm run lint
npm run typecheck
npm run build
```

Windows allows loopback solely for the async test event loop; Linux CI uses `--disable-socket --allow-unix-socket` and no provider keys. CI runs on Python 3.11/3.12 and Node 22 for pushes and pull requests. Required status checks must be enabled separately in repository branch protection. Python direct dependencies are pinned in `requirements-ci.txt`; transitive dependencies are resolved by pip. Frontend installation uses its committed lockfile. Upgrade dependencies with these checks.

The [redistributable synthetic corpus](tests/fixtures/evidence/README.md) tests text extraction, blank and raster-only pages/no OCR, truncation, missing/planned experiments and rejected quotes. All seven records are `pending_human_review`: the evaluator reports `reviewed_count: 0` and `metrics: null`. Only records with actual human-review provenance enter category precision/recall/missingness and quotation/support metrics. Synthetic regressions are not a scientific accuracy benchmark.

For isolated browser QA, run `python -m uvicorn --app-dir tests ui_fixture_server:app --port 8000` instead of the normal API. This replaces only the external search/download source with clearly labelled synthetic papers, uses real PDF processing and temporary storage, and never changes production research records.

---

# Features

## Current

- Research topic planning
- arXiv paper search
- Automatic PDF download
- PDF text extraction
- Structured LLM Paper Reader
- Rule-based Reader fallback
- Reviewer Agent
- Reader evaluation pipeline
- Modular workflow architecture
- OpenRouter integration
- Pydantic structured output

---

# Project Architecture

```

User Research Topic
│
▼
Planner Agent
│
▼
Paper Searcher
│
▼
PDF Downloader
│
▼
PDF Reader
│
▼
LLM Reader
│
▼
Reviewer
│
▼
Research Report

```

Current workflow:

```

Topic
→ Planner
→ arXiv Search
→ Download PDF
→ Extract Text
→ Structured LLM Reader
→ Reviewer

```

---

# Example Output

```

Paper Analysis

Reader Model:
nvidia/nemotron-nano-9b-v2:free

Research Problem

Current robotic systems lack privacy-aware navigation capabilities...

Methodology

The framework combines A* path planning with Vision Language Models...

Datasets

• S3DIS Dataset

Main Contributions

• Privacy-aware navigation framework
• Gaussian privacy distance metric
• Real robot deployment

Limitations

• Limited real-world evaluation
• Static environment assumption

```

---

# Repository Structure

```

AutoResearch-Agent
│
├── agents/
│   ├── planner.py
│   ├── researcher.py
│   ├── reader.py
│   ├── llm_reader.py
│   └── reviewer.py
│
├── schemas/
│   ├── paper_analysis.py
│   └── reflection_result.py
│
├── services/
│   └── llm_client.py
│
├── workflow/
│   └── research_workflow.py
│
├── evaluation/
│
├── tools/
│
└── main.py

```

---

# Technology Stack

- Python 3.11+
- LangChain
- OpenRouter
- Pydantic
- arXiv API
- pypdf
- LLM Structured Output

---

# Current Milestones

## Milestone 1

- Planner Agent
- Paper Search
- PDF Reader
- Rule-based Reader
- Reviewer

Completed

---

## Milestone 2

- OpenRouter Integration
- Structured LLM Reader
- Pydantic Output
- Automatic Rule-based Fallback

Completed

---

## Milestone 3 (In Progress)

Reflection Agent

---

## Future Roadmap

### Reflection Agent

Automatically improve low-quality paper analyses.

### Memory Agent

Remember previous papers to avoid repeated analysis.

### Multi-paper Reading

Read multiple papers simultaneously.

### Literature Review Generator

Automatically generate survey papers.

### Citation Graph

Analyze citation relationships.

### Web UI

Interactive browser interface.

### Local Model Support

Support Ollama and local LLM deployment.

---

# Installation

Clone the repository.

```bash
git clone https://github.com/zhengzhenghao007/AutoResearch-Agent.git

cd AutoResearch-Agent
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate the environment.

Windows

```bash
.venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Create a `.env` file.

```env
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=openrouter/free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Run the project.

```bash
python main.py
```

---

# Future Vision

AutoResearch-Agent is designed as a modular multi-agent research platform.

Eventually it will support:

- Autonomous literature review
- Reflection-based self-improvement
- Long-term memory
- Multi-paper reasoning
- Survey generation
- Knowledge graph construction
- Research planning
- Local and cloud LLMs

The objective is to create an AI research assistant capable of supporting the complete academic literature review workflow.

---

# License

MIT License

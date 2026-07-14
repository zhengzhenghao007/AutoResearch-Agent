# AutoResearch-Agent

> A Multi-Agent Literature Review System powered by Large Language Models.

AutoResearch-Agent is an AI research assistant that automatically searches academic papers, downloads PDFs, extracts key information, reviews the analysis, and progressively generates high-quality literature reviews.

The long-term goal is to build an autonomous research workflow similar to OpenAI Deep Research, but focused on academic literature analysis.

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
- PyMuPDF
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

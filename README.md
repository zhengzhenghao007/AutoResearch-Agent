# AutoResearch-Agent

An extensible Multi-Agent system for automated literature review.

## Overview

AutoResearch-Agent is an AI research assistant that automatically:

- Generates a research plan
- Searches relevant papers from arXiv
- Downloads research papers
- Extracts PDF content
- Analyzes paper structure
- Reviews analysis quality
- Prepares for automatic literature review generation

The project is designed with a modular multi-agent architecture and can be extended with LLMs, memory systems, and workflow engines.

---

## Current Architecture

```text
User
 │
 ▼
Planner Agent
 │
 ▼
Researcher Agent
 │
 ▼
arXiv Search
 │
 ▼
PDF Downloader
 │
 ▼
PDF Reader
 │
 ▼
Rule-Based Reader
 │
 ▼
Reviewer Agent
```

---

## Current Features

### Planner Agent

Generate a structured research plan from a research topic.

Example:

- Define research scope
- Search papers
- Compare methods
- Generate literature review

---

### Researcher Agent

Search papers directly from arXiv.

Features:

- Keyword search
- Relevance ranking
- PDF link retrieval
- Metadata extraction

---

### PDF Reader

Automatically:

- Download PDFs
- Extract text
- Prepare documents for analysis

---

### Rule-Based Reader

Extracts:

- Research Problem
- Methodology
- Datasets
- Main Contributions
- Limitations

---

### Reviewer Agent

Evaluate extraction quality.

Checks include:

- Missing fields
- Duplicate information
- Placeholder content
- Background mixed into limitations
- Dataset quality

---

### Workflow Engine

Coordinates all agents in a unified pipeline.

---

## Project Structure

```text
AutoResearch-Agent
│
├── agents/
│   ├── planner.py
│   ├── researcher.py
│   ├── reader.py
│   ├── reviewer.py
│   └── reader_result.py
│
├── workflow/
│   └── research_workflow.py
│
├── tools/
│   ├── arxiv_search.py
│   └── pdf_reader.py
│
├── evaluation/
│   └── evaluate_reader.py
│
├── data/
│
├── memory/
│
├── tests/
│
└── main.py
```

---

## Current Pipeline

```
Research Topic
      │
      ▼
Planner
      │
      ▼
Researcher
      │
      ▼
Search arXiv
      │
      ▼
Download PDF
      │
      ▼
Extract Text
      │
      ▼
Reader
      │
      ▼
Reviewer
```

---

## Technologies

- Python 3.12
- arXiv API
- pypdf
- requests

Future:

- OpenRouter
- GPT-4.1
- Claude
- Gemini
- ChromaDB
- LangGraph

---

## Roadmap

### Phase 1

- [x] Planner Agent
- [x] Researcher Agent
- [x] PDF Reader
- [x] Rule-Based Reader
- [x] Reviewer
- [x] Workflow
- [x] Evaluation

### Phase 2

- [ ] LLM Reader
- [ ] Reflection Loop
- [ ] Memory
- [ ] Literature Review Generator

### Phase 3

- [ ] Web Interface
- [ ] Multi-Paper Review
- [ ] Knowledge Graph
- [ ] Benchmark Experiments

---

## Author

Zheng Sihan

"""Run a fresh bounded research task using the application's registered services."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from schemas.multi_source_search import SearchRequest
from schemas.paper_acquisition import AcquisitionRequest, AcquisitionSelection
from schemas.research_tasks import ResearchTaskCreate
from services.arxiv_identity import canonical_arxiv_pdf_url
from services.paper_acquisition import acquire, import_acquired
from services.research_store import ResearchStore
from services.research_tasks import ResearchTaskExecutor, TERMINAL
from services.search_history import search_and_save
from workflow.evidence_workflow import EvidenceWorkflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="AI-generated video detection")
    args = parser.parse_args()
    store = ResearchStore(ROOT / ".verification/live-study")
    flow = EvidenceWorkflow(store=store, search=lambda *args, **kwargs: [])
    run = flow.create(args.query, project_name=args.query, research_goal=args.query)
    out = store.root / "reports" / run.id
    out.mkdir(parents=True)
    print(f"Run directory: {out}", flush=True)
    batch = search_and_save(store, run.id, SearchRequest(query=args.query, limit=20,
                            sources=["arxiv", "openalex", "crossref", "semantic_scholar"]))
    (out / "search.json").write_text(batch.model_dump_json(indent=2), encoding="utf-8")
    terms = set(re.findall(r"[a-z0-9]+", args.query.lower()))
    candidates = []
    seen = set()
    for group in batch.groups:
        for hit in group.records:
            url = canonical_arxiv_pdf_url(hit.pdf_url)
            overlap = terms.intersection(re.findall(r"[a-z0-9]+", hit.title.lower()))
            if url.startswith('https://arxiv.org/pdf/') and url not in seen and overlap:
                candidates.append((-len(overlap), hit.rank, hit.title, hit))
                seen.add(url)
    sources = []
    screening = []
    attempts = 0
    for score, rank, title, hit in sorted(candidates, key=lambda row: row[:3]):
        record = dict(title=title, source=hit.source, url=hit.url, title_term_matches=-score, rank=rank)
        screening.append(record)
        if attempts == 5 or len(sources) == 3:
            record["decision"] = "outside acquisition budget"
            continue
        attempts += 1
        selection = AcquisitionSelection(batch_id=batch.id, source=hit.source, source_id=hit.source_id)
        item, = acquire(store, run.id, AcquisitionRequest(selections=[selection]))
        record.update(decision=item.status, error=item.error)
        if item.status in ("downloaded", "cached"):
            run = import_acquired(flow, run.id, item.id)
            sources.append((run.papers[-1], hit))
    (out / "screening.json").write_text(json.dumps(screening, indent=2), encoding="utf-8")
    if not sources:
        raise SystemExit("No readable paper acquired. Inspect search.json and screening.json.")
    executor = ResearchTaskExecutor(store)
    task = executor.create(run.id, ResearchTaskCreate(question=args.query, mode="research"))
    while task.status not in TERMINAL:
        task = executor.next(run.id, task.id)
    (out / "task.json").write_text(task.model_dump_json(indent=2), encoding="utf-8")
    receipt = {
        "query": args.query, "run_id": run.id, "searched_at": batch.created_at.isoformat(),
        "providers": [{ "name": s.source, "status": s.status, "hits": len(s.hits),
                        "error": s.error} for s in batch.sources],
        "download_attempts": attempts,
        "sources": [{"title": hit.title, "url": hit.url, "sha256": paper.document.source.sha256,
                     "pages": len(paper.document.pages), "candidate_spans": len(paper.claims)}
                    for paper, hit in sources],
        "steps": [{"skill": step.tool, "status": step.status,
                   "summary": step.result.summary if step.result else None}
                  for step in task.steps],
        "status": task.status, "reason": task.stop_reason,
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    lines = ["# " + args.query, f"Task status: {task.status}", task.stop_reason or "", "## Sources"]
    anchors = {}
    for paper, hit in sources:
        lines.append(f"- [{hit.title}]({hit.url})")
        for anchor in paper.evidence:
            anchors[anchor.id] = f"[{hit.title}, p. {anchor.page}]({canonical_arxiv_pdf_url(hit.pdf_url)}#page={anchor.page})"
    for step in task.steps:
        if step.result is None:
            continue
        lines.extend(["## " + step.tool, step.result.summary])
        for artifact in step.result.artifacts:
            lines.extend([f"### {artifact.title} ({artifact.status})", artifact.text,
                          " · ".join(anchors[key] for key in artifact.evidence_ids if key in anchors)])
        lines.extend(step.result.gaps)
    (out / "report.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print(f"{task.status}: {out / 'report.md'}")
    return 0 if all(step.status == "completed" for step in task.steps) else 1


if __name__ == "__main__":
    sys.exit(main())

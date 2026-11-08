"""Replay the bounded research task on local full-text PDFs, publishing only metadata."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from schemas.research_tasks import ResearchTaskCreate
from services.academic_humanizer import humanize
from services.evidence_review import normalized, review_paper
from services.humanizer_policy import set_profile
from services.research_store import ResearchStore
from services.research_tasks import ResearchTaskExecutor, TERMINAL
from workflow.evidence_workflow import EvidenceWorkflow

QUESTION = "How do detectors distinguish AI-generated video under unseen generators and compression?"
D3_SOURCE = "https://openaccess.thecvf.com/content/ICCV2025/papers/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.pdf"


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_case(pdf_dir, private_store):
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise ValueError("Supply a directory containing full-text PDFs")
    if private_store.resolve().is_relative_to((ROOT / "examples").resolve()):
        raise ValueError("Keep the private store outside the published examples")
    os.environ["AUTORESEARCH_HUMANIZER_POLICY_FILE"] = str(private_store / "humanizer.json")
    set_profile("standard")
    store = ResearchStore(private_store)
    workflow = EvidenceWorkflow(store=store, search=lambda *args, **kwargs: [])
    calls, changes = Counter(), Counter()

    def trace(frame, event, result):
        if event == "return" and frame.f_code is humanize.__code__:
            caller = frame.f_back
            name = caller.f_globals["__name__"] + "." + caller.f_code.co_name
            calls[name] += 1
            if result != frame.f_locals["text"]:
                changes[name] += 1

    sources = []
    previous = sys.getprofile()
    sys.setprofile(trace)
    try:
        run = workflow.create(QUESTION, project_name="AI-generated video detection", research_goal=QUESTION)
        for path in pdfs:
            data = path.read_bytes()
            run = workflow.import_pdf(data, path.stem, run.id)
            paper = run.papers[-1]
            doc = paper.document
            checked = review_paper(paper)
            if not checked.approved or doc.source.sha256 != hashlib.sha256(data).hexdigest():
                raise ValueError(f"Source verification failed for {path.name}: {checked.issues}")
            pages = {page.number: normalized(page.text) for page in doc.pages}
            anchors = []
            for item in paper.evidence:
                quote = normalized(item.quote)
                offset = pages[item.page].index(quote)
                anchors.append(dict(id=item.id, page=item.page, normalized_offset=offset,
                                    normalized_length=len(quote), normalized_quote_sha256=digest(quote)))
            arxiv = re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", path.stem)
            source_url = f"https://arxiv.org/abs/{path.stem}" if arxiv else None
            if path.name == "d3-iccv2025.pdf":
                source_url = D3_SOURCE
            sources.append(dict(file=path.name, url=source_url,
                                sha256=doc.source.sha256, total_pages=doc.total_pages,
                                parsed_pages=len(doc.pages), nonblank_pages=sum(bool(t) for t in pages.values()),
                                truncated=doc.truncated, ocr_pages=doc.ocr_pages, extractor=paper.extractor,
                                checked_claims=len(paper.claims), category_counts=dict(Counter(c.category for c in paper.claims)),
                                missing_fields=paper.missing_fields, anchors=anchors))
        executor = ResearchTaskExecutor(store)
        task = executor.create(run.id, ResearchTaskCreate(question=QUESTION, mode="research"))
        while task.status not in TERMINAL:
            task = executor.next(run.id, task.id)
    finally:
        sys.setprofile(previous)
    if any(step.status != "completed" for step in task.steps):
        raise ValueError(f"Task stopped early: {task.status}, {task.stop_reason}")
    probe = "It is worth noting that the detector may degrade under compression [1]."
    return dict(question=QUESTION, run_id=run.id, task_id=task.id, source_snapshot_sha256=task.source_sha256,
                status=task.status, stop_reason=task.stop_reason, usage=task.usage.model_dump(), sources=sources,
                steps=[dict(skill=s.tool, version=s.skill_version, status=s.status, evidence_ids=s.result.evidence_ids,
                            gaps=s.result.gaps, artifact_counts=dict(Counter(a.kind for a in s.result.artifacts)))
                       for s in task.steps], humanizer=dict(profile="standard", workflow_calls=dict(calls),
                       workflow_text_changes=dict(changes), separate_edit_probe=dict(input=probe, output=humanize(probe))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--private-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_case(args.pdf_dir, args.private_store)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['status']} | {len(result['sources'])} sources | {len(result['steps'])} steps")

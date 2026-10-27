"""Reproduce a real offline research case, or install its checked-in snapshot.

Run from the repository root. Downloads require the explicit --download flag.
No model calls, fabricated observations, or human attestations are made.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from schemas.research import ResearchRun
from services.research_store import ResearchStore
from services.research_validation import validate_run
from services.citation_registry import build_citation_registry
from services.manuscript_draft import build_manuscript_draft
from services.manuscript import get_manuscript, save_revision
from workflow.evidence_workflow import EvidenceWorkflow

HERE = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-dir', type=Path, default=ROOT / '.verification/case-pdfs')
    parser.add_argument('--output', type=Path, default=ROOT / '.verification/conformal-case')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--install', action='store_true', help='Install checked-in snapshot as a new local JSON record; no download')
    parser.add_argument('--store', type=Path, default=ROOT / 'data/research_runs')
    args = parser.parse_args()
    manifest = json.loads((HERE / 'sources.json').read_text(encoding='utf-8'))
    if args.install:
        run = ResearchRun.model_validate_json((HERE / 'outputs/run.json').read_bytes())
        validate_run(run)
        run.id = uuid4().hex
        store = ResearchStore(args.store)
        store.save(run)
        print(f'Installed a new example record. Open http://127.0.0.1:3000/?run={run.id}')
        return
    if args.output.exists():
        raise ValueError('Output already exists. Choose a new --output directory; previous results are never overwritten.')
    inputs = []
    for item in manifest['papers']:
        path = args.pdf_dir / item['filename']
        if not path.exists() and args.download:
            import requests
            path.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(item['pdf_url'], timeout=(10, 90), stream=True) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 20 * 1024 * 1024:
                        raise ValueError('PDF exceeds 20 MiB')
                    chunks.append(chunk)
                data = b''.join(chunks)
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError(f'Publisher bytes changed for {item["key"]}; inspect before updating the manifest.')
            path.write_bytes(data)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f'Hash mismatch: {path}')
        inputs.append((item, data))
    args.output.mkdir(parents=True)
    flow = EvidenceWorkflow(store=ResearchStore(args.output / 'records'))
    run = flow.create(manifest['topic'])
    steps = [{'operation': 'create', 'run_id': run.id}]
    for item, data in inputs:
        run = flow.import_pdf(data, item['title'], run.id)
        paper = run.papers[-1]
        steps.append({'operation':'import_pdf','source':item['key'],'sha256':item['sha256'],
                      'pages':len(paper.document.pages),'total_pages':paper.document.total_pages,
                      'quotes':len(paper.evidence),'missing_fields':paper.missing_fields})
    validate_run(run)
    draft = build_manuscript_draft(run)
    state = get_manuscript(flow.store, run.id)
    saved = save_revision(flow.store,run.id,None,state.current_input_sha256,
                          'Initial extractive case draft; not human reviewed or approved.',None)
    # Persist the real manuscript revision as well as the read-only outline.
    write_json(args.output / 'manuscript-state.json', saved.model_dump(mode='json'))
    write_json(args.output / 'run.json', run.model_dump(mode='json'))
    write_json(args.output / 'citations.json', build_citation_registry(run).model_dump(mode='json'))
    write_json(args.output / 'draft.json', draft.model_dump(mode='json'))
    write_json(args.output / 'execution.json', {'mode':'rule','model_calls':0,'human_approval':False,'steps':steps,
        'literal_source_support':run.review.approved,'scope':'Case reproduction, not a scientific-quality benchmark.'})
    text = ['# Extractive review draft', '', '> Automatically assembled quotations. Not human approved. Not a publishable synthesis.', '',
            'Attribution and CC BY 4.0 license: see ../sources.json and ../README.md.', '']
    for section in draft.sections:
        text += ['## '+section.title, '']
        for block in section.blocks:
            text += [block.text, '']
            if block.paper:
                text += [f'Source: {block.paper.source.title}; PDF page(s): '+', '.join(str(e.page) for e in block.paper.evidence), '']
    (args.output / 'draft.md').write_text('\n'.join(text),encoding='utf-8')
    comparison = next(a for a in run.artifacts if a.kind=='method_comparison')
    (args.output / 'comparison.md').write_text('# '+comparison.title+'\n\n'+comparison.content+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.output),'papers':len(run.papers),'quotes':sum(len(p.evidence) for p in run.papers),
                      'human_approval':False},indent=2))


if __name__ == '__main__':
    main()

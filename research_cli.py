"""Run with python research_cli.py --help. Default extraction is offline."""
import argparse
import sys
from pathlib import Path
from services.evidence_extraction import EvidenceExtractor
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow
from services.citation_registry import build_citation_registry
from services.bibtex_export import build_bibtex_export
from services.source_identity import build_source_identities
from services.source_duplicates import build_source_duplicates


def main():
    parser = argparse.ArgumentParser(description='Evidence-first literature research')
    parser.add_argument('--store', type=Path, help='Research JSON directory')
    parser.add_argument('--mode', choices=['rule', 'llm'], default='rule')
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('topic')
    search.add_argument('--max-results', type=int, default=5)
    analyze = commands.add_parser('analyze')
    analyze.add_argument('run_id')
    analyze.add_argument('selected_ids', nargs='+')
    upload = commands.add_parser('import-pdf')
    upload.add_argument('path', type=Path)
    upload.add_argument('--run-id')
    show = commands.add_parser('show')
    show.add_argument('run_id')
    citations = commands.add_parser('citations')
    citations.add_argument('run_id')
    bibtex = commands.add_parser('bibtex', help='Export BibTeX; skipped-source diagnostics go to stderr')
    bibtex.add_argument('run_id')
    identities = commands.add_parser('source-identities', help='Read user-supplied DOI state and conflicts')
    identities.add_argument('run_id')
    duplicates = commands.add_parser('source-duplicates', help='Read exact duplicate clues without merging')
    duplicates.add_argument('run_id')
    source_doi = commands.add_parser('source-doi', help='Append unverified DOI annotation history')
    source_doi.add_argument('run_id')
    source_doi.add_argument('source_id')
    source_doi.add_argument('action', choices=['set', 'clear'])
    source_doi.add_argument('--doi')
    source_doi.add_argument('--reason', required=True)
    decision = commands.add_parser('candidate-decision', help='Append a screening annotation; analysis selection is unchanged')
    decision.add_argument('run_id')
    decision.add_argument('candidate_id')
    decision.add_argument('decision', choices=['include', 'exclude'])
    decision.add_argument('--reason', required=True)
    args = parser.parse_args()
    flow = EvidenceWorkflow(store=ResearchStore(args.store), extractor=EvidenceExtractor(args.mode))
    try:
        if args.command == 'search':
            result = flow.search(args.topic, args.max_results)
        elif args.command == 'analyze':
            result = flow.analyze(args.run_id, args.selected_ids)
        elif args.command == 'import-pdf':
            with args.path.open('rb') as stream:
                data = stream.read(flow.processor.max_bytes + 1)
            result = flow.import_pdf(data, args.path.name, args.run_id)
        elif args.command == 'citations':
            result = build_citation_registry(flow.store.load(args.run_id))
        elif args.command == 'source-identities':
            result = build_source_identities(flow.store.load(args.run_id))
        elif args.command == 'source-duplicates':
            result = build_source_duplicates(flow.store.load(args.run_id))
        elif args.command == 'source-doi':
            result = flow.record_source_identity(args.run_id, args.source_id, args.action, args.doi, args.reason)
        elif args.command == 'bibtex':
            result = build_bibtex_export(flow.store.load(args.run_id))
            for skipped in result.skipped_sources:
                print(f'Skipped source {skipped.source_id}: {skipped.reason}', file=sys.stderr)
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', newline='\n')
            print(result.bibtex, end='')
            return 0
        elif args.command == 'candidate-decision':
            result = flow.record_candidate_decision(args.run_id, args.candidate_id, args.decision, args.reason)
        else:
            result = flow.store.load(args.run_id)
        print(result.model_dump_json(indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(f'Research failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

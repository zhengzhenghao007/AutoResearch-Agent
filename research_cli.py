"""Run with python research_cli.py --help. Default extraction is offline."""
import argparse
import sys
from pathlib import Path
from services.evidence_extraction import EvidenceExtractor
from services.research_store import ResearchStore
from workflow.evidence_workflow import EvidenceWorkflow


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
        else:
            result = flow.store.load(args.run_id)
        print(result.model_dump_json(indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(f'Research failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

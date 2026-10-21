"""Disposable job process. Writes only to its private staging directory."""
import json
import sys
from pathlib import Path


def main():
    if sys.platform.startswith('linux'):
        import resource
        import signal
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
        resource.setrlimit(resource.RLIMIT_CPU, (120, 121))
        signal.alarm(300)
    from schemas.research_jobs import JobRequest
    from schemas.research import ResearchRun
    from services.research_store import ResearchStore
    from workflow.evidence_workflow import EvidenceWorkflow
    directory = Path(sys.argv[1])
    data = json.loads((directory / 'input.json').read_text(encoding='utf-8'))
    request = JobRequest.model_validate(data['request'])
    store = ResearchStore(directory / 'stage')
    if data['baseline']:
        store.save(ResearchRun.model_validate_json(data['baseline']))
    flow = EvidenceWorkflow(store=store)
    result = (flow.search(request.topic, request.max_results) if request.kind == 'search'
              else flow.analyze(request.run_id, request.selected_ids))
    output = result.model_dump_json().encode('utf-8')
    if len(output) > 64 * 1024 * 1024:
        raise ValueError('Job result exceeds limit')
    (directory / 'result.json').write_bytes(output)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Do not copy provider messages or credentials to parent-visible output.
        sys.exit(1)

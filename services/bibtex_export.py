"""Conservative, deterministic BibTeX from validated provenance; no external lookup."""
from schemas.bibtex_export import BibtexExport, SkippedBibtexSource
from schemas.research import ResearchRun
from services.arxiv_identity import recognized_arxiv_identifier
from services.citation_registry import build_citation_registry

_ESCAPES = {
    '\\': r'\textbackslash{}', '{': r'\textbraceleft{}', '}': r'\textbraceright{}', '&': r'\&',
    '%': r'\%', '#': r'\#', '_': r'\_', '$': r'\$',
    '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
}


def _escape_title(title: str) -> str:
    return ''.join(_ESCAPES.get(char, char) for char in ' '.join(title.split()))


def build_bibtex_export(run: ResearchRun) -> BibtexExport:
    registry = build_citation_registry(run)
    entries, skipped = [], []
    for source in registry.sources:
        identifier = recognized_arxiv_identifier(source.uri) if source.kind == 'paper' else None
        if identifier is None:
            skipped.append(SkippedBibtexSource(source_id=source.source_id))
            continue
        # Encode rather than sanitize: distinct legacy IDs cannot collapse to one key.
        key = 'source_' + source.source_id.encode('utf-8').hex()
        entries.append(
            f'@misc{{{key},\n'
            f'  title = {{{{{_escape_title(source.title)}}}}},\n'
            f'  eprint = {{{identifier}}},\n'
            '  archivePrefix = {arXiv},\n'
            f'  url = {{https://arxiv.org/abs/{identifier}}}\n'
            '}\n'
        )
    return BibtexExport(run_id=run.id, bibtex='\n'.join(entries), skipped_sources=skipped)

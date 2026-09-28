'use client';

import { useEffect, useRef, useState } from 'react';
import { researchApi } from '@/lib/research-api';
import type { BibtexExport, CitationRegistry } from '@/types/citations';

function download(text: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  // Keep the object URL alive until the browser has started consuming it.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// A key resets data synchronously when the caller switches records or revisions.
export default function ResearchExports({ runId, revision = 0 }: { runId: string; revision?: number }) {
  return <ExportPanel key={`${runId}:${revision}`} runId={runId} />;
}

function ExportPanel({ runId }: { runId: string }) {
  const active = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  const [citations, setCitations] = useState<CitationRegistry | null>(null);
  const [bibtex, setBibtex] = useState<BibtexExport | null>(null);
  const [citationBusy, setCitationBusy] = useState(false);
  const [bibtexBusy, setBibtexBusy] = useState(false);
  const [citationError, setCitationError] = useState('');
  const [bibtexError, setBibtexError] = useState('');

  async function load(kind: 'citations' | 'bibtex') {
    const setBusy = kind === 'citations' ? setCitationBusy : setBibtexBusy;
    const setError = kind === 'citations' ? setCitationError : setBibtexError;
    setBusy(true); setError('');
    if (kind === 'citations') setCitations(null); else setBibtex(null);
    try {
      if (kind === 'citations') {
        const result = await researchApi.citations(runId);
        if (result.run_id !== runId) throw new Error('Export returned a different research record. Reload the record and try again.');
        if (active.current) setCitations(result);
      } else {
        const result = await researchApi.bibtex(runId);
        if (result.run_id !== runId) throw new Error('Export returned a different research record. Reload the record and try again.');
        if (active.current) setBibtex(result);
      }
    } catch (error) {
      if (active.current) setError(error instanceof Error ? error.message : 'Export could not be loaded. Try again.');
    } finally { if (active.current) setBusy(false); }
  }
  const filenameId = /^[a-f0-9]{32}$/.test(runId) ? runId : 'record';
  return <section className="research-exports" aria-label="Research exports">
    <h3>Export references</h3>
    <p className="research-meta">Inspect saved provenance or download references. Source support is not scientific verification.</p>
    <div className="research-export-grid">
      <section aria-label="Citation provenance">
        <h4>Citation provenance</h4>
        <div className="research-row"><button disabled={citationBusy} onClick={() => void load('citations')}>Load citation JSON</button>
          {citations && <button onClick={() => download(JSON.stringify(citations, null, 2) + '\n', `citations-${filenameId}.json`, 'application/json;charset=utf-8')}>Download citation JSON</button>}</div>
        {citationBusy && <p role="status">Loading citation JSON…</p>}
        {citationError && <p role="alert" className="research-error">{citationError}</p>}
        {citations && <>{citations.sources.length === 0 && <p className="research-empty">No processed sources are available for citation export.</p>}
          <pre tabIndex={0} aria-label="Citation JSON" className="research-export-code">{JSON.stringify(citations, null, 2)}</pre></>}
      </section>
      <section aria-label="BibTeX references">
        <h4>BibTeX references</h4>
        <div className="research-row"><button disabled={bibtexBusy} onClick={() => void load('bibtex')}>Load BibTeX</button>
          {bibtex?.bibtex && <button onClick={() => download(bibtex.bibtex, `references-${filenameId}.bib`, 'application/x-bibtex;charset=utf-8')}>Download BibTeX</button>}</div>
        {bibtexBusy && <p role="status">Loading BibTeX…</p>}
        {bibtexError && <p role="alert" className="research-error">{bibtexError}</p>}
        {bibtex && <>{bibtex.bibtex ? <pre tabIndex={0} aria-label="BibTeX text" className="research-export-code">{bibtex.bibtex}</pre> :
          <p className="research-empty">{bibtex.skipped_sources.length ? 'No sources could be exported to BibTeX.' : 'No processed sources are available for BibTeX export.'}</p>}
          {bibtex.skipped_sources.length > 0 && <div className="research-notice"><p>Sources skipped from BibTeX</p><ul>{bibtex.skipped_sources.map(source => <li key={source.source_id}>{source.source_id}: Missing bibliographic identity. Uploads and unrecognized source links are not exported.</li>)}</ul></div>}</>}
      </section>
    </div>
  </section>;
}

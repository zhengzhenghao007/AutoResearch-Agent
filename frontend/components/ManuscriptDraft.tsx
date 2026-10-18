'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ManuscriptDraftData} from '@/types/manuscript-draft';

export default function ManuscriptDraft({runId,revision}:{runId:string;revision:number}) {
  return <DraftPanel key={`${runId}:${revision}`} runId={runId}/>;
}
function DraftPanel({runId}:{runId:string}) {
  const [draft,setDraft]=useState<ManuscriptDraftData|null>(null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const active=useRef(false);const inFlight=useRef(false);
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  async function load() {
    if(inFlight.current)return;inFlight.current=true;setBusy(true);setError('');setDraft(null);
    try {
      const value=await researchApi.manuscriptDraft(runId);
      if(value.run_id!==runId)throw new Error('Draft returned a different record. Reopen the record and try again.');
      if(active.current)setDraft(value);
    }catch(e){if(active.current)setError(e instanceof Error?e.message:'Unable to load chapter draft.');}
    finally{inFlight.current=false;if(active.current)setBusy(false);}
  }
  return <section className="research-exports research-draft" aria-label="Evidence-linked chapter draft">
    <h3>Evidence-linked chapter draft</h3>
    <p>Preview saved quotations and user-data summaries in a chapter outline. No model calls or automatic rewriting. Missing material stays explicit.</p>
    <button disabled={busy} onClick={()=>void load()}>Preview chapter draft</button>
    {busy&&<p role="status">Preparing chapter material…</p>}{error&&<p role="alert">{error}</p>}
    {draft&&<><p>{draft.scope}</p><p>Contradiction review: not assessed · Scientific validation: not assessed · Human approval: not requested</p>
      <p>Input hash: {draft.input_sha256}</p>
      {draft.omitted_legacy_observation_claims>0&&<p>Legacy observation claims omitted: {draft.omitted_legacy_observation_claims}. This preview uses structured experiment datasets for user results.</p>}
      <details><summary>Calculation scope and precision</summary><p>{draft.statistics_scope}</p></details>
      {draft.sections.map(section=><article key={section.id}><h4>{section.title}</h4><p>{section.purpose}</p>
        {section.blocks.map(block=><div className="research-evidence" key={block.id}>
          <strong>{block.kind==='paper_claim'?'Attributed paper quotation':block.kind==='user_statistics'?'User-data descriptive summary':'Missing material'}</strong>
          <p className="research-prose">{block.text}</p>
          {block.paper&&<details><summary>Paper evidence: {block.paper.source.title}</summary>
            <p>Claim {block.paper.claim_id} · Source {block.paper.source.id}</p>
            <p>Hash: {block.paper.source.sha256}</p><p>{block.paper.source.uri}</p>
            <p>Parsed {block.paper.parsed_pages}/{block.paper.total_pages} pages{block.paper.truncated?' (truncated)':''}. Selected evidence does not establish whole-paper coverage.</p>
            {block.paper.evidence.map(e=><blockquote key={e.id}>Page {e.page} · {e.id}: {e.quote}</blockquote>)}
          </details>}
          {block.computation&&<details><summary>Calculation and input references</summary>
            <p>Dataset {block.computation.dataset_id} · Column {block.computation.column.name} · {block.computation.algorithm}</p>
            {block.computation.column.warnings.map(w=><p key={w}>{w}</p>)}
            <p>Showing up to 100 of {block.computation.column.references.length} nonmissing references. The User experiment observations panel provides the full statistics/reference JSON.</p>
            <ul>{block.computation.column.references.slice(0,100).map(ref=><li key={ref.sample_id}>{ref.sample_id} / {ref.column}: {ref.value}</li>)}</ul>
          </details>}
        </div>)}
      </article>)}
      <p>This preview is not saved as a manuscript revision. Narrative editing, linked contradiction review and approved publication export are later P4 work.</p>
    </>}
  </section>;
}

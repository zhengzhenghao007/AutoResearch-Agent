'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { researchApi } from '@/lib/research-api';
import type { ResearchHistory, ResearchRun } from '@/types/research';
import EvidenceViewer, { sourcePdf } from './EvidenceViewer';
import './research.css';

const message = (error: unknown) => error instanceof Error ? error.message : 'The request failed. Check the record state before continuing.';
function setUrl(id?: string) { const url=new URL(window.location.href); if(id) url.searchParams.set('run',id); else url.searchParams.delete('run'); url.hash=''; window.history.pushState({},'',url); }

export default function EvidenceWorkspace() {
  const [run,setRun]=useState<ResearchRun|null>(null);
  const [topic,setTopic]=useState(''); const [selection,setSelection]=useState<string[]>([]);
  const [file,setFile]=useState<File|null>(null); const fileInput=useRef<HTMLInputElement>(null);
  const [pending,setPending]=useState(''); const [loading,setLoading]=useState(false); const [error,setError]=useState('');
  const [history,setHistory]=useState<ResearchHistory|null>(null); const [page,setPage]=useState(1); const [historyBusy,setHistoryBusy]=useState(false); const [historyError,setHistoryError]=useState('');
  const currentUrlRun=useRef<string|null>(null);
  const generation=useRef(0); const historyGeneration=useRef(0); const mutation=useRef(false);
  const accept=useCallback((value: ResearchRun)=>{setRun(value);setTopic(value.topic);setSelection(value.selected_ids);setFile(null);if(fileInput.current)fileInput.current.value='';},[]);
  const refreshHistory=useCallback(async (target: number)=>{
    const ticket=++historyGeneration.current;setHistoryBusy(true);setHistoryError('');
    try { const result=await researchApi.list(target);if(ticket===historyGeneration.current){setHistory(result);setPage(target);} }
    catch(error){if(ticket===historyGeneration.current)setHistoryError(message(error));}
    finally{if(ticket===historyGeneration.current)setHistoryBusy(false);}
  },[]);
  const open=useCallback(async(id: string|null)=>{
    currentUrlRun.current=id;
    const ticket=++generation.current;setError('');setRun(null);setSelection([]);setTopic('');setFile(null);if(fileInput.current)fileInput.current.value='';setLoading(Boolean(id));
    if(!id)return;
    if(!/^[a-f0-9]{32}$/.test(id)){setError('Invalid research record ID in the URL. Choose a record from history.');setLoading(false);return;}
    try {const value=await researchApi.get(id);if(ticket===generation.current)accept(value);}
    catch(error){if(ticket===generation.current)setError(message(error));}
    finally{if(ticket===generation.current)setLoading(false);}
  },[accept]);
  const invalidate=useCallback(()=>{generation.current++;historyGeneration.current++;},[]);
  useEffect(()=>{
    let active=true;
    const restore=()=>{const id=new URL(window.location.href).searchParams.get('run');if(id!==currentUrlRun.current)void open(id);};
    queueMicrotask(()=>{if(active){void open(new URL(window.location.href).searchParams.get('run'));void refreshHistory(1);}});
    window.addEventListener('popstate',restore);
    return()=>{active=false;invalidate();window.removeEventListener('popstate',restore);};
  },[open,refreshHistory,invalidate]);
  async function mutate(label: string,operation:()=>Promise<ResearchRun>) {
    if(mutation.current||loading)return;
    mutation.current=true;const ticket=++generation.current;setPending(label);setError('');
    try {const value=await operation();if(ticket===generation.current){accept(value);setUrl(value.id);currentUrlRun.current=value.id;}void refreshHistory(page);}
    catch(error){if(ticket===generation.current)setError(message(error));}
    finally{mutation.current=false;setPending('');}
  }
  const busy=Boolean(pending)||loading;
  return <section className="research-workspace" aria-labelledby="research-title">
    <header className="research-header"><div><h1 id="research-title">Evidence workspace</h1><p>Read the source. Trace the claim. Keep the research record.</p></div><button disabled={busy} onClick={()=>{setUrl();void open(null);}}>New record</button></header>
    <div className="research-layout"><aside className="research-history" aria-label="Research history"><div className="research-row"><h2>History</h2><button disabled={historyBusy} onClick={()=>void refreshHistory(page)}>Refresh history</button></div>
      {historyBusy && <p role="status">Loading history…</p>}{historyError && <p role="alert">{historyError}</p>}
      {history && history.items.length===0 && <p className="research-meta">No saved records on this page.</p>}
      <ul>{history?.items.map(item=><li key={item.id}><button disabled={busy} aria-current={run?.id===item.id?'page':undefined} onClick={()=>{setUrl(item.id);void open(item.id);}}><strong>{item.topic}</strong><span>{item.paper_count} papers / {item.candidate_count} candidates</span><span>{item.source_support_passed?'Source support passed':'Source support pending'}</span></button></li>)}</ul>
      <nav aria-label="History pages" className="research-row"><button aria-label="Previous history page" disabled={historyBusy||page<=1} onClick={()=>void refreshHistory(page-1)}>Previous</button><span>Page {page}{history ? ` of ${Math.max(1,Math.ceil(history.total/history.page_size))}`:''}</span><button aria-label="Next history page" disabled={historyBusy||!history||page*history.page_size>=history.total} onClick={()=>void refreshHistory(page+1)}>Next</button></nav>
    </aside><div className="research-main">
      <form className="research-search" onSubmit={event=>{event.preventDefault();if(topic.trim())void mutate('Finding papers…',()=>researchApi.search(topic.trim()));}}><label htmlFor="research-topic">Research topic</label><div className="research-row"><input id="research-topic" maxLength={2000} required value={topic} disabled={busy} onChange={e=>setTopic(e.target.value)} placeholder="e.g. vision language robot navigation"/><button className="research-primary" disabled={busy||!topic.trim()}>Find papers</button></div><p className="research-meta">A search creates a new record. Choose papers before analysis.</p></form>
      <form className="research-upload" onSubmit={event=>{event.preventDefault();if(file)void mutate('Adding PDF…',()=>researchApi.upload(file,run?.id));}}><label htmlFor="research-pdf">PDF file</label><div className="research-row"><input ref={fileInput} id="research-pdf" type="file" accept=".pdf,application/pdf" disabled={busy} onChange={event=>setFile(event.target.files?.[0]??null)}/><button disabled={busy||!file}>Add PDF</button></div><p className="research-meta">{run?'Adds evidence to the current record. Use New record to start separately.':'Creates a record from a text-based PDF.'}</p></form>
      {pending && <p role="status" className="research-notice">{pending} Keep this page open while the request completes.</p>}{loading && <p role="status">Opening research record…</p>}{error && <p role="alert" className="research-error">{error}</p>}
      {!run&&!loading&&!error && <p className="research-empty">Start with a research topic, add a PDF, or reopen a saved record.</p>}
      {run && <><div className="research-record-title"><h2>{run.topic}</h2><p className="research-meta">Record {run.id}</p></div>
        {run.plan.length>0 && <details className="research-plan"><summary>Research plan</summary><ol>{run.plan.map((step,i)=><li key={i}>{step}</li>)}</ol></details>}
        <section aria-label="Candidate papers"><div className="research-row"><h3>Candidate papers</h3><span className="research-meta">{selection.length} selected</span></div>
          {run.candidates.length===0 ? <p className="research-empty">No candidate papers found. Try another topic or add a PDF.</p> : <ul className="research-candidates">{run.candidates.map(candidate=><li key={candidate.id}><label><input type="checkbox" aria-label={`Select ${candidate.title}`} disabled={busy} checked={selection.includes(candidate.id)} onChange={event=>setSelection(current=>event.target.checked?[...current,candidate.id]:current.filter(id=>id!==candidate.id))}/><strong>{candidate.title}</strong></label><p className="research-meta">{candidate.authors.join(', ')}</p>{candidate.summary && <p>{candidate.summary}</p>}{sourcePdf(candidate.pdf_url) && <a href={sourcePdf(candidate.pdf_url)!} target="_blank" rel="noopener noreferrer">Source PDF</a>}</li>)}</ul>}
          <button className="research-primary" disabled={busy||selection.length===0} onClick={()=>void mutate('Analyzing selected papers…',()=>researchApi.analyze(run.id,selection))}>Analyze selected papers</button>
        </section><EvidenceViewer run={run}/></>}
    </div></div>
  </section>;
}

'use client';
import ResearchJobs from './ResearchJobs';
import SemanticReview from './SemanticReview';
import ManuscriptDraft from './ManuscriptDraft';
import ManuscriptEditor from './ManuscriptEditor';
import Experiments from './Experiments';
import CategoryRevisions from './CategoryRevisions';
import ClaimReview from './ClaimReview';
import ScreeningReport from './ScreeningReport';

import { useCallback, useEffect, useRef, useState } from 'react';
import { researchApi } from '@/lib/research-api';
import type { ResearchHistory, ResearchRun } from '@/types/research';
import { sourcePdf } from './EvidenceViewer';
import ReadingDesk from './ReadingDesk';
import ResearchOverview from './ResearchOverview';
import ComparisonTable from './ComparisonTable';
import ResearchExports from './ResearchExports';
import SourceDuplicateClues from './SourceDuplicateClues';
import CandidateScreening from './CandidateScreening';
import SourceIdentities from './SourceIdentities';
import './research.css';

const message = (error: unknown) => error instanceof Error ? error.message : 'The request failed. Check the record state before continuing.';
function urlStage(){const value=new URL(window.location.href).searchParams.get('stage');return value&&['library','reading','compare','writing'].includes(value)?value:'library';}
function historyIndex():number|null {const index=window.history.state?.researchIndex;return Number.isSafeInteger(index)?index:null;}
function setUrl(id?: string,stage='library',replace=false) { const url=new URL(window.location.href); if(id) url.searchParams.set('run',id); else url.searchParams.delete('run'); if(id&&stage!=='library')url.searchParams.set('stage',stage);else url.searchParams.delete('stage'); url.hash=''; const index=(historyIndex()??0)+(replace?0:1);window.history[replace?'replaceState':'pushState']({...window.history.state,researchIndex:index},'',url);return index; }

export default function EvidenceWorkspace({jobsEnabled=false,readOnly=false,onLeaveBlockedChange}:{jobsEnabled?:boolean;readOnly?:boolean;onLeaveBlockedChange?:(value:boolean)=>void}) {
  const [stage,setStage]=useState('library');
  const stageRef=useRef('library');
  const activeHistoryIndex=useRef<number|null>(null);
  const currentUrlRun=useRef<string|null>(null);
  function navigateStage(value:string){stageRef.current=value;setStage(value);if(value==='writing')setWritingVisited(true);const id=run?.id??currentUrlRun.current;if(id)activeHistoryIndex.current=setUrl(id,value);}
  const [focusEvidence,setFocusEvidence]=useState('');
  const [focusSource,setFocusSource]=useState('');
  const [readingVisit,setReadingVisit]=useState(0);
  const [writingVisited,setWritingVisited]=useState(false);
  const [historyOpen,setHistoryOpen]=useState(false);
  function showEvidence(id:string,sourceId=''){setFocusEvidence(id);setFocusSource(sourceId);setReadingVisit(n=>n+1);navigateStage('reading');}
  const [run,setRun]=useState<ResearchRun|null>(null);
  const [revision,setRevision]=useState(0);
  const [screeningPending,setScreeningPending]=useState(false);
  const [manuscriptPending,setManuscriptPending]=useState(false);
  const manuscriptLock=useRef(false);
  const manuscriptBusy=useCallback((value:boolean)=>{manuscriptLock.current=value;setManuscriptPending(value);},[]);
  const [topic,setTopic]=useState(''); const [selection,setSelection]=useState<string[]>([]);
  const [file,setFile]=useState<File|null>(null); const fileInput=useRef<HTMLInputElement>(null);
  const [pending,setPending]=useState(''); const [loading,setLoading]=useState(false); const [error,setError]=useState('');
  const [history,setHistory]=useState<ResearchHistory|null>(null); const [page,setPage]=useState(1); const [historyBusy,setHistoryBusy]=useState(false); const [historyError,setHistoryError]=useState('');
  const generation=useRef(0); const historyGeneration=useRef(0); const mutation=useRef(false);
  const accept=useCallback((value: ResearchRun)=>{setRun(value);setRevision(current=>current+1);setTopic(value.topic);setSelection(value.selected_ids);setFile(null);if(fileInput.current)fileInput.current.value='';},[]);
  const refreshHistory=useCallback(async (target: number)=>{
    const ticket=++historyGeneration.current;setHistoryBusy(true);setHistoryError('');
    try { const result=await researchApi.list(target);if(ticket===historyGeneration.current){setHistory(result);setPage(target);} }
    catch(error){if(ticket===historyGeneration.current)setHistoryError(message(error));}
    finally{if(ticket===historyGeneration.current)setHistoryBusy(false);}
  },[]);
  const open=useCallback(async(id: string|null)=>{
    const nextStage=id?urlStage():'library';stageRef.current=nextStage;
    activeHistoryIndex.current=historyIndex();
    currentUrlRun.current=id;setStage(nextStage);setFocusEvidence('');setWritingVisited(nextStage==='writing');
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
    const restore=()=>{
      const id=new URL(window.location.href).searchParams.get('run');
      if(id!==currentUrlRun.current){
        // A browser Back action bypasses disabled in-app record buttons.
        if(manuscriptLock.current){
          const targetIndex=historyIndex();
          if(targetIndex!==null&&activeHistoryIndex.current!==null&&targetIndex!==activeHistoryIndex.current)window.history.go(activeHistoryIndex.current-targetIndex);
          else activeHistoryIndex.current=setUrl(currentUrlRun.current??undefined,stageRef.current);
          setError('Save or discard manuscript changes and wait for manuscript requests before leaving this record.');return;
        }
        void open(id);
      }else{activeHistoryIndex.current=historyIndex();const nextStage=id?urlStage():'library';stageRef.current=nextStage;setStage(nextStage);if(nextStage==='writing')setWritingVisited(true);}
    };
    queueMicrotask(()=>{if(active){if(historyIndex()===null)window.history.replaceState({...window.history.state,researchIndex:0},'',window.location.href);void open(new URL(window.location.href).searchParams.get('run'));void refreshHistory(1);}});
    window.addEventListener('popstate',restore);
    return()=>{active=false;invalidate();window.removeEventListener('popstate',restore);};
  },[open,refreshHistory,invalidate]);
  async function mutate(label: string,operation:()=>Promise<ResearchRun>) {
    if(readOnly||manuscriptLock.current||mutation.current||loading)return;
    mutation.current=true;const ticket=++generation.current;setPending(label);setError('');
    try {const value=await operation();if(ticket===generation.current){accept(value);activeHistoryIndex.current=setUrl(value.id,stageRef.current);currentUrlRun.current=value.id;}void refreshHistory(page);}
    catch(error){if(ticket===generation.current)setError(message(error));}
    finally{mutation.current=false;setPending('');}
  }
  async function recordAnnotation(operation: (id: string)=>Promise<ResearchRun>): Promise<boolean> {
    if(readOnly||manuscriptLock.current||mutation.current||loading||!run)return false;
    mutation.current=true;setScreeningPending(true);
    const ticket=++generation.current;
    const runId=run.id;
    // Serialize snapshot writes, but preserve unsaved topic, file and analysis selection.
    try {
      const value=await operation(runId);
      if(ticket!==generation.current)return false;
      if(value.id!==runId)throw new Error('The response belongs to another record. Reopen this record to check its state.');
      setRun(value);setRevision(current=>current+1);void refreshHistory(page);
      return true;
    } finally {mutation.current=false;setScreeningPending(false);}
  }
  const runBusy=Boolean(pending)||loading||screeningPending;
  const busy=runBusy||manuscriptPending;
  useEffect(()=>{onLeaveBlockedChange?.(busy);return()=>onLeaveBlockedChange?.(false);},[busy,onLeaveBlockedChange]);
  return <section className="research-workspace" aria-labelledby="research-title">
    <header className="research-header"><div><h1 id="research-title">Literature workbench</h1><p>From papers to a draft you can trace back to the source.</p></div><button disabled={busy} onClick={()=>{setUrl();void open(null);}}>New record</button></header>
    <div className="research-layout"><aside className="research-history" aria-label="Research history"><div className="research-row"><h2>Your research</h2><button className="history-toggle" aria-expanded={historyOpen} aria-controls="history-content" onClick={()=>setHistoryOpen(value=>!value)}>{historyOpen?'Hide records':'Show records'}</button><button className="history-refresh" disabled={historyBusy} onClick={()=>void refreshHistory(page)}>Refresh history</button></div>
      <div id="history-content" className="history-content" data-expanded={historyOpen}>
      {historyBusy && <p role="status">Loading history…</p>}{historyError && <p role="alert">{historyError}</p>}
      {history && history.items.length===0 && <p className="research-meta">No saved records on this page.</p>}
      <ul>{history?.items.map(item=><li key={item.id}><button disabled={busy} aria-current={run?.id===item.id?'page':undefined} onClick={()=>{setUrl(item.id);void open(item.id);}}><strong>{item.topic}</strong><span>{item.paper_count} papers / {item.candidate_count} candidates</span><span>{item.source_support_passed?'Source support passed':'Source support pending'}</span></button></li>)}</ul>
      <nav aria-label="History pages" className="research-row"><button aria-label="Previous history page" disabled={historyBusy||page<=1} onClick={()=>void refreshHistory(page-1)}>Previous</button><span>Page {page}{history ? ` of ${Math.max(1,Math.ceil(history.total/history.page_size))}`:''}</span><button aria-label="Next history page" disabled={historyBusy||!history||page*history.page_size>=history.total} onClick={()=>void refreshHistory(page+1)}>Next</button></nav>
      </div>
    </aside><div className="research-main">
      <nav className="workflow-nav" aria-label="Research workflow">{[['library','Library'],['reading','Reading & evidence'],['compare','Compare'],['writing','Writing']].map(([id,label],i)=><button key={id} aria-current={stage===id?'step':undefined} aria-controls={`stage-${id}`} disabled={id!=='library'&&!run} onClick={()=>navigateStage(id)}><span aria-hidden="true">{i+1}</span>{label}</button>)}</nav>
      {error&&<p role="alert" className="research-error">{error}</p>}
      {run&&<div className="research-record-title"><h2>{run.topic}</h2><p className="research-meta">{run.papers.length} papers · {run.papers.reduce((n,p)=>n+p.evidence.length,0)} quotations · {run.review.approved?'Literal source checks passed':'Source checks pending'}</p></div>}
      <div id="stage-library" hidden={stage!=='library'}>
      {run&&<ResearchOverview run={run} onStage={navigateStage} onSource={id=>showEvidence('',id)}/>}
      <div className="stage-intro"><h3>Build your reading list</h3><p>Search for papers or add PDFs you already have. Each research record keeps its own sources, evidence and drafts.</p></div>
      {jobsEnabled&&<ResearchJobs topic={topic} runId={run?.id} selectedIds={selection} blocked={busy} readOnly={readOnly} onOpen={id=>{setUrl(id);void open(id);void refreshHistory(page);}}/>}
      <fieldset disabled={readOnly} style={{border:0,padding:0,minWidth:0}}><form className="research-search" onSubmit={event=>{event.preventDefault();if(!jobsEnabled&&topic.trim())void mutate('Finding papers…',()=>researchApi.search(topic.trim()));}}><label htmlFor="research-topic">Research topic</label><div className="research-row"><input id="research-topic" maxLength={2000} required value={topic} disabled={busy} onChange={e=>setTopic(e.target.value)} placeholder="e.g. vision language robot navigation"/>{!jobsEnabled&&<button className="research-primary" disabled={busy||!topic.trim()}>Find papers</button>}<button type="button" disabled={busy||!topic.trim()} onClick={()=>void mutate('Creating offline record…',()=>researchApi.create(topic.trim()))}>Create offline record</button></div><p className="research-meta">A search creates a new record. Choose papers before analysis.</p></form>
      <form className="research-upload" onSubmit={event=>{event.preventDefault();if(file)void mutate('Adding PDF…',()=>researchApi.upload(file,run?.id));}}><label htmlFor="research-pdf">PDF file</label><div className="research-row"><input ref={fileInput} id="research-pdf" type="file" accept=".pdf,application/pdf" disabled={busy} onChange={event=>setFile(event.target.files?.[0]??null)}/><button disabled={busy||!file}>Add PDF</button></div><p className="research-meta">{run?'Adds evidence to the current record. Use New record to start separately.':'Creates a record from a text-based PDF.'}</p></form>
      </fieldset>{pending && <p role="status" className="research-notice">{pending} Keep this page open while the request completes.</p>}{loading && <p role="status">Opening research record…</p>}
      {!run&&!loading&&!error && <p className="research-empty">Start with a research topic, add a PDF, or reopen a saved record.</p>}
      {run && <>
        {run.plan.length>0 && <details className="research-plan"><summary>Research plan</summary><ol>{run.plan.map((step,i)=><li key={i}>{step}</li>)}</ol></details>}
        <section aria-label="Candidate papers" hidden={run.candidates.length===0&&run.papers.length>0}><div className="research-row"><h3>Candidate papers</h3><span className="research-meta">{selection.length} selected</span></div>
          {run.candidates.length===0 ? <p className="research-empty">No candidate papers found. Try another topic or add a PDF.</p> : <ul className="research-candidates">{run.candidates.map(candidate=><li key={candidate.id}><label><input type="checkbox" aria-label={`Select ${candidate.title}`} disabled={busy} checked={selection.includes(candidate.id)} onChange={event=>setSelection(current=>event.target.checked?[...current,candidate.id]:current.filter(id=>id!==candidate.id))}/><strong>{candidate.title}</strong></label><p className="research-meta">{candidate.authors.join(', ')}</p>{candidate.summary && <p>{candidate.summary}</p>}{sourcePdf(candidate.pdf_url) && <a href={sourcePdf(candidate.pdf_url)!} target="_blank" rel="noopener noreferrer">Source PDF</a>}{<details className="candidate-review"><summary>Screening decision</summary><CandidateScreening key={`${run.id}:${candidate.id}`} candidate={candidate} events={(run.candidate_decisions??[]).filter(event=>event.candidate_id===candidate.id)} disabled={busy||readOnly} onRecord={(decision,reason)=>recordAnnotation(id=>researchApi.candidateDecision(id,{candidate_id:candidate.id,decision,reason}))}/></details>}</li>)}</ul>}
          {!jobsEnabled&&<button className="research-primary" disabled={busy||readOnly||selection.length===0} onClick={()=>void mutate('Analyzing selected papers…',()=>researchApi.analyze(run.id,selection))}>Analyze selected papers</button>}
        </section>
        {run.papers.length>0&&<section className="library-sources" aria-label="Imported papers"><h3>In this record</h3>{run.papers.map(p=><article key={p.document.source.id}><div><h4>{p.document.source.title}</h4><p className="research-meta">{p.document.pages.length}/{p.document.total_pages} pages · {p.evidence.length} quotations</p></div><button onClick={()=>showEvidence(p.evidence[0]?.id??'',p.document.source.id)}>Read paper</button></article>)}</section>}
        <details className="research-advanced"><summary>Library tools: references, duplicates and screening</summary>{!busy&&<><ResearchExports runId={run.id} revision={revision}/><SourceDuplicateClues runId={run.id} revision={revision}/><ScreeningReport runId={run.id} revision={revision}/></>}<fieldset disabled={readOnly} className="research-fieldset"><SourceIdentities key={run.id} run={run} revision={revision} busy={busy} onRecord={request=>recordAnnotation(id=>researchApi.sourceIdentity(id,request))}/></fieldset></details>
      </>}
      </div>
      {run&&<>
       <div id="stage-reading" hidden={stage!=='reading'}><ReadingDesk key={`${run.id}:${readingVisit}`} run={run} focusEvidence={focusEvidence} focusSource={focusSource} onFocus={setFocusEvidence}/>
        <details className="research-advanced"><summary>Advanced review: source checks and claim categories</summary><p>{run.review.scope}</p>{run.review.issues.map((issue,i)=><p key={i}>{issue}</p>)}{!busy&&<ClaimReview runId={run.id} revision={revision}/>}<fieldset disabled={readOnly} className="research-fieldset"><SemanticReview key={`semantic:${run.id}`} run={run} revision={revision} blocked={busy}/><CategoryRevisions key={`categories:${run.id}`} run={run} busy={busy} onSave={(claim,category,reason)=>recordAnnotation(id=>researchApi.reviseCategory(id,claim,category,reason))}/></fieldset></details>
       </div>
       <div id="stage-compare" hidden={stage!=='compare'}><ComparisonTable run={run} onEvidence={showEvidence}/><details className="research-advanced"><summary>Optional: your experimental observations</summary><fieldset disabled={readOnly} className="research-fieldset"><Experiments key={`experiments:${run.id}`} run={run} revision={revision} busy={busy} onImport={(file,format,metadata)=>recordAnnotation(id=>researchApi.importExperiment(id,file,format,metadata))}/></fieldset></details></div>
       <div id="stage-writing" hidden={stage!=='writing'}><h3>Write from your evidence</h3><p className="research-meta">Start with an attributed outline, then save revisions. Missing evidence stays visible; approval is a separate, explicit step.</p>{!busy&&<ManuscriptDraft runId={run.id} revision={revision}/>}<fieldset disabled={readOnly} className="research-fieldset">{writingVisited&&<ManuscriptEditor runId={run.id} revision={revision} blocked={runBusy} onBusyChange={manuscriptBusy}/>}</fieldset></div>
      </>}

    </div></div>
  </section>;
}

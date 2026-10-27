'use client';
import {useEffect,useRef,useState,type ReactNode} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ManuscriptDraftData} from '@/types/manuscript-draft';
import type {ManuscriptState,ManuscriptSection,ManuscriptSentence,SentenceKind} from '@/types/manuscript';
interface Props {runId:string;revision:number;blocked?:boolean;onBusyChange?:(busy:boolean)=>void}
export default function ManuscriptEditor(props:Props) {return <Editor key={`${props.runId}:${props.revision}`} {...props}/>;}
function Editor({runId,blocked=false,onBusyChange}:Props) {
 const [state,setState]=useState<ManuscriptState|null>(null),[sections,setSections]=useState<ManuscriptSection[]>([]);
 const [error,setError]=useState(''),[pending,setPending]=useState('Loading manuscript…'),[reason,setReason]=useState('');
 const [consent,setConsent]=useState(false),[confirm,setConfirm]=useState(false),[reviewer,setReviewer]=useState(''),[note,setNote]=useState('');
 const alive=useRef(true),lock=useRef(false);
 const latest=state?.revisions.at(-1);
 const dirty=Boolean(latest&&JSON.stringify(sections)!==JSON.stringify(latest.sections));
 useEffect(()=>{
  if(!dirty)return;
  const warn=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue='';};
  window.addEventListener('beforeunload',warn);
  return()=>window.removeEventListener('beforeunload',warn);
 },[dirty]);
 const stale=Boolean(latest&&latest.input_sha256!==state?.current_input_sha256);
 const busy=blocked||Boolean(pending);
 const ready=Boolean(latest&&!dirty&&!stale&&!busy);
 const reviews=state?.reviews.filter(r=>r.revision_id===latest?.id&&r.content_sha256===latest?.content_sha256&&r.input_sha256===latest?.input_sha256)??[];
 const approved=state?.approvals.some(a=>a.revision_id===latest?.id&&a.content_sha256===latest?.content_sha256&&a.input_sha256===latest?.input_sha256&&a.review_count===reviews.length);
 function accept(value:ManuscriptState,replace:boolean) {if(value.run_id!==runId)throw new Error('Response belongs to a different record.');setState(value);if(replace)setSections(value.revisions.at(-1)?.sections??[]);setConfirm(false);setConsent(false);}
 useEffect(()=>{
  alive.current=true;researchApi.manuscript(runId).then(value=>{if(alive.current){if(value.run_id!==runId)throw new Error('Response belongs to a different record.');setState(value);setSections(value.revisions.at(-1)?.sections??[]);}}).catch(e=>{if(alive.current)setError(e instanceof Error?e.message:'Could not load manuscript.');}).finally(()=>{if(alive.current)setPending('');});
  return()=>{alive.current=false;onBusyChange?.(false);};
 },[runId,onBusyChange]);
 async function action(label:string,operation:()=>Promise<void>){if(lock.current||busy)return;lock.current=true;setPending(label);setError('');onBusyChange?.(true);try{await operation();}catch(e){if(alive.current)setError(e instanceof Error?e.message:'Manuscript request failed.');}finally{lock.current=false;if(alive.current){setPending('');onBusyChange?.(false);}}}
 function edit(next:ManuscriptSection[]){onBusyChange?.(true);setSections(next);setConfirm(false);setConsent(false);}
 function sentence(sectionId:string,id:string,patch:Partial<ManuscriptSentence>){edit(sections.map(s=>s.id===sectionId?{...s,sentences:s.sentences.map(t=>t.id===id?{...t,...patch}:t)}:s));}
 function move(index:number,offset:number){const next=[...sections];[next[index],next[index+offset]]=[next[index+offset],next[index]];edit(next);}
 function save(reset:boolean){if(!state)return;if(reset&&dirty&&!window.confirm('Replace unsaved manuscript changes with the current evidence preview?'))return;void action('Saving manuscript…',async()=>{const value=await researchApi.saveManuscript(runId,{expected_revision:latest?.id??null,expected_input_sha256:state.current_input_sha256,reason:reason.trim(),sections:reset?null:sections});if(alive.current){accept(value,true);setReason('');setNote('');}});}
 useEffect(()=>{onBusyChange?.((Boolean(pending)&&pending!=='Loading manuscript…')||dirty);},[pending,dirty,onBusyChange]);
 const blocks=latest?.source.sections.flatMap(s=>s.blocks)??[];
 return <section className="research-panel" aria-label="Manuscript editor"><h3>Manuscript editor</h3>
 <p>Develop your draft chapter by chapter. Check each factual sentence against its references. Missing observations remain visible; scientific review is still needed.</p>
 {pending&&<p role="status">{pending}</p>}{error&&<p role="alert" className="research-error">{error}</p>}
 {!state&&!pending&&<button disabled={busy} onClick={()=>void action('Loading manuscript…',async()=>{const value=await researchApi.manuscript(runId);if(alive.current)accept(value,true);})}>Retry manuscript load</button>}
 {state&&<><label>Revision reason<input aria-label="Revision reason" maxLength={10000} value={reason} disabled={busy} onChange={e=>setReason(e.target.value)}/></label>
 <button disabled={busy||!reason.trim()||state.revisions.length>=20} onClick={()=>save(true)}>{latest?'Reset from current preview':'Initialize from current preview'}</button>
 {latest&&<><p className="research-meta">Revision {latest.number} · {latest.created_at} · {latest.reason}</p>{stale&&<p className="research-notice">Source data changed. Reset from the current preview to refresh references, or save a new revision after correcting references. Approval and export are blocked.</p>}{dirty&&<p>Unsaved manuscript changes. Save before review or approval.</p>}
 <fieldset disabled={busy}><legend>Chapters and typed sentences</legend>{sections.map((s,index)=><DeferredDetails key={s.id} initiallyOpen={index===0} summary={`${s.title} (${s.sentences.length} sentences)`}>{()=> <div className="research-plan"><label>Chapter title<input aria-label={`Chapter ${s.id} title`} maxLength={200} value={s.title} onChange={e=>edit(sections.map(t=>t.id===s.id?{...t,title:e.target.value}:t))}/></label><div className="research-row"><button disabled={busy||index===0} onClick={()=>move(index,-1)} aria-label={`Move ${s.title} up`}>Move up</button><button disabled={busy||index===sections.length-1} onClick={()=>move(index,1)} aria-label={`Move ${s.title} down`}>Move down</button></div>
 {s.sentences.map(t=><div className="manuscript-sentence" key={t.id}><label>Sentence {t.id}<textarea aria-label={`Sentence ${t.id}`} maxLength={10000} value={t.text} onChange={e=>sentence(s.id,t.id,{text:e.target.value})}/></label><label>Sentence type<select aria-label={`Type ${t.id}`} value={t.kind} onChange={e=>sentence(s.id,t.id,{kind:e.target.value as SentenceKind})}>{(['paper_report','user_observation','hypothesis','suggestion','placeholder'] as const).map(k=><option key={k} value={k}>{k}</option>)}</select></label>
 <DeferredDetails summary={`References for ${t.id} (${t.reference_ids.length} selected)`}>{()=> <fieldset><legend>Choose reference blocks</legend>{blocks.map(b=><label key={b.id} className="manuscript-reference"><input type="checkbox" checked={t.reference_ids.includes(b.id)} onChange={e=>sentence(s.id,t.id,{reference_ids:e.target.checked?[...t.reference_ids,b.id]:t.reference_ids.filter(id=>id!==b.id)})}/>{b.id} · {b.kind}: {b.text}</label>)}{t.reference_ids.filter(id=>!blocks.some(b=>b.id===id)).map(id=><label key={id}><input type="checkbox" checked onChange={()=>sentence(s.id,t.id,{reference_ids:t.reference_ids.filter(x=>x!==id)})}/>Missing reference: {id}</label>)}{!blocks.length&&<p>No evidence references available in this snapshot.</p>}</fieldset>}</DeferredDetails>
 <button onClick={()=>edit(sections.map(x=>x.id===s.id?{...x,sentences:x.sentences.filter(y=>y.id!==t.id)}:x))}>Remove sentence {t.id}</button></div>)}
 <button disabled={busy||s.sentences.length>=200} onClick={()=>edit(sections.map(x=>x.id===s.id?{...x,sentences:[...x.sentences,{id:`sentence-${crypto.randomUUID()}`,text:'',kind:'hypothesis',reference_ids:[]}]}:x))}>Add sentence to {s.title}</button></div>}</DeferredDetails>)}</fieldset>
 <div className="manuscript-save-bar"><span role="status">{dirty?'Unsaved changes':`Saved revision ${latest.number}`}</span><button disabled={busy||!reason.trim()||state.revisions.length>=20} onClick={()=>save(false)}>Save manuscript revision</button>{dirty&&<button disabled={busy} onClick={()=>{if(window.confirm('Discard unsaved manuscript changes and return to the saved revision?')){setSections(latest.sections);setReason('');setConfirm(false);setConsent(false);setError('');}}}>Discard unsaved changes</button>}</div>
 <details className="research-advanced"><summary>Review and export</summary><EvidenceSnapshot source={latest.source}/><h4>Current revision findings</h4>{reviews.length===0?<p>No model review for this revision. Human assessment can proceed offline.</p>:reviews.map(r=><article key={r.id}><p>{r.model} · {r.created_at} · Scientific validation: {r.scientific_validation}</p><ul>{r.findings.map(f=><li key={f.sentence_id}>{f.sentence_id}: {f.status} — {f.rationale}</li>)}</ul><h5>Potential contradictions</h5>{r.contradictions.length?r.contradictions.map((c,i)=><p key={i}>{c.sentence_ids.join(' / ')}: {c.rationale}</p>):<p>No potential contradictions reported. This does not prove consistency.</p>}</article>)}
 <label><input type="checkbox" checked={consent} disabled={!ready} onChange={e=>setConsent(e.target.checked)}/>Send this manuscript and referenced evidence to the configured model (may incur cost).</label><button disabled={!ready||!consent} onClick={()=>void action('Reviewing manuscript…',async()=>{const value=await researchApi.reviewManuscript(runId,latest.id);if(alive.current){accept(value,false);setNote('');}})}>Review manuscript with model</button>
 <h4>Human approval</h4><p>Inspect the current text, evidence, missing results and any findings above. Approval records your assessment of this exact revision; it does not establish scientific validity.</p>
 <label>Reviewer<input aria-label="Manuscript reviewer" value={reviewer} maxLength={10000} disabled={!ready} onChange={e=>{setReviewer(e.target.value);setConfirm(false);}}/></label><label>Assessment note<textarea aria-label="Manuscript approval note" value={note} maxLength={10000} disabled={!ready} onChange={e=>{setNote(e.target.value);setConfirm(false);}}/></label><label><input type="checkbox" checked={confirm} disabled={!ready} onChange={e=>setConfirm(e.target.checked)}/>I have reviewed this revision and its current findings and approve export.</label>
 <button disabled={!ready||!confirm||!reviewer.trim()||!note.trim()} onClick={()=>void action('Recording human approval…',async()=>{const value=await researchApi.approveManuscript(runId,latest.id,reviewer.trim(),note.trim(),reviews.length);if(alive.current)accept(value,false);})}>Approve current manuscript</button>
 <button disabled={!ready||!approved} onClick={()=>void action('Preparing approved export…',async()=>{const value=await researchApi.exportManuscript(runId,latest.id);if(!alive.current)return;if(value.revision_id!==latest.id||value.content_sha256!==latest.content_sha256)throw new Error('Export does not match current revision.');const url=URL.createObjectURL(new Blob([value.markdown],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=value.filename;a.click();URL.revokeObjectURL(url);})}>Download approved manuscript</button></details>
 </>}
 <details><summary>Manuscript revision history ({state.revisions.length}/20)</summary>{state.revisions.map(r=><details key={r.id}><summary>Revision {r.number}: {r.reason} · {r.created_at}</summary><p>Content hash: {r.content_sha256}</p><EvidenceSnapshot source={r.source}/>{r.sections.map(s=><article key={s.id}><h4>{s.title}</h4>{s.sentences.map(t=><p key={t.id}>[{t.kind}] {t.text} <small>References: {t.reference_ids.join(', ')||'none'}</small></p>)}</article>)}{state.approvals.filter(a=>a.revision_id===r.id).map((a,i)=><p key={i}>Approved by {a.reviewer} · {a.created_at}: {a.note}</p>)}</details>)}</details></>}
 </section>;
}


function EvidenceSnapshot({source}:{source:ManuscriptDraftData}) {
 return <details><summary>Saved evidence snapshot</summary><p>Input hash: {source.input_sha256}</p><p>{source.scope} {source.statistics_scope}</p>{source.sections.flatMap(s=>s.blocks).map(b=><details key={b.id}><summary>{b.id} · {b.kind}</summary><p>{b.text}</p>{b.paper&&<><p>{b.paper.source.title} · {b.paper.source.uri}</p><p>Source SHA-256: {b.paper.source.sha256}</p><p>Claim: {b.paper.claim_id} · Parsed pages: {b.paper.parsed_pages}/{b.paper.total_pages} · Truncated: {String(b.paper.truncated)}</p>{b.paper.evidence.map(e=><blockquote key={e.id}>{e.quote}<footer>{e.id} · Source {e.source_id} · Page {e.page}</footer></blockquote>)}</>}{b.computation&&<><p>Dataset: {b.computation.title} ({b.computation.dataset_id})</p><p>SHA-256: {b.computation.sha256} · Algorithm: {b.computation.algorithm}</p><pre>{JSON.stringify(b.computation.column,null,2)}</pre></>}</details>)}</details>;
}

function DeferredDetails({summary,initiallyOpen=false,children}:{summary:string;initiallyOpen?:boolean;children:()=>ReactNode}) {
 const [open,setOpen]=useState(initiallyOpen);
 return <details className="manuscript-disclosure" open={open} onToggle={event=>setOpen(event.currentTarget.open)}><summary>{summary}</summary>{open&&children()}</details>;
}

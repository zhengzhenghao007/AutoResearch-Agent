'use client';
import {useEffect,useId,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
import type {CurrentSourceIdentity,SourceIdentitiesView,SourceIdentityAnnotation,SourceIdentityRequest} from '@/types/source-identities';
type Save=(request:SourceIdentityRequest)=>Promise<boolean>;

function IdentityCard({identity,events,disabled,current,onRecord}:{identity:CurrentSourceIdentity;events:SourceIdentityAnnotation[];disabled:boolean;current:boolean;onRecord:Save}) {
  const id=useId();const [action,setAction]=useState<'set'|'clear'>('set');
  const [doi,setDoi]=useState('');const [reason,setReason]=useState('');const [error,setError]=useState('');const [pending,setPending]=useState(false);
  const alive=useRef(true);const submitting=useRef(false);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  async function submit(){
    if(disabled||submitting.current||!reason.trim()||(action==='set'&&!doi.trim()))return;
    submitting.current=true;setPending(true);setError('');
    try{
      const request:SourceIdentityRequest=action==='set'?{source_id:identity.source.id,action,doi:doi.trim(),reason:reason.trim()}:{source_id:identity.source.id,action,reason:reason.trim()};
      if(await onRecord(request)&&alive.current){setDoi('');setReason('');}
    }catch(error){if(alive.current)setError(error instanceof Error?error.message:'Unable to save annotation.');}
    finally{submitting.current=false;if(alive.current)setPending(false);}
  }
  return <fieldset className="research-screening" aria-label={`DOI for ${identity.source.title}`}>
    <legend>{identity.source.title}</legend><p className="research-meta">Source {identity.source.id}</p>
    {current && <><p>{identity.active?'Current processed source':'Historical source: absent from the current processed-paper set; read-only.'}</p><p>{identity.doi?`User-supplied DOI (not verified): ${identity.doi}`:'No current DOI.'}</p></>}
    {events.length>0 && <details><summary>DOI history ({events.length})</summary><ol>{events.map((event,index)=><li key={index}>{event.action==='clear'?'Cleared DOI':`Set DOI: ${event.doi}`} — {event.reason}<time dateTime={event.recorded_at}>{event.recorded_at}</time></li>)}</ol></details>}
    {identity.active && <form onSubmit={event=>{event.preventDefault();void submit();}}>
      <label htmlFor={`${id}-action`}>DOI action</label><select id={`${id}-action`} value={action} disabled={disabled||pending} onChange={event=>setAction(event.target.value as 'set'|'clear')}><option value="set">Set DOI</option><option value="clear">Clear DOI</option></select>
      {action==='set' && <><label htmlFor={`${id}-doi`}>DOI</label><input id={`${id}-doi`} value={doi} maxLength={2048} required disabled={disabled||pending} onChange={event=>setDoi(event.target.value)} placeholder="10.1234/example or https://doi.org/10.1234/example"/></>}
      <label htmlFor={`${id}-reason`}>DOI reason</label><textarea id={`${id}-reason`} value={reason} maxLength={2000} required disabled={disabled||pending} onChange={event=>setReason(event.target.value)}/>
      <button disabled={disabled||pending||!reason.trim()||(action==='set'&&!doi.trim())}>Record DOI annotation</button>
    </form>}
    {pending && <p role="status">Recording DOI annotation…</p>}
    {error && <p role="alert" className="research-error">{error} Reopen the saved record before submitting again; repeated submissions add history entries.</p>}
  </fieldset>;
}
export default function SourceIdentities({run,revision,busy,onRecord}:{run:ResearchRun;revision:number;busy:boolean;onRecord:Save}){
  const [requested,setRequested]=useState(false);const [refresh,setRefresh]=useState(0);
  const [loaded,setLoaded]=useState<{view:SourceIdentitiesView;history:SourceIdentityAnnotation[];revision:number;refresh:number}|null>(null);
  const [error,setError]=useState('');const [loading,setLoading]=useState(false);
  useEffect(()=>{
    let active=true;
    if(requested&&!busy){
      queueMicrotask(()=>{if(active){setLoading(true);setError('');}});
      Promise.all([researchApi.sourceIdentities(run.id),researchApi.get(run.id)]).then(([view,snapshot])=>{
        if(!active)return;
        if(view.run_id!==run.id||snapshot.id!==run.id)throw new Error('Identity response belongs to another record.');
        setLoaded({view,history:snapshot.source_identity_annotations??[],revision,refresh});
      }).catch(error=>{if(active)setError(error instanceof Error?error.message:'Unable to load DOI annotations.');})
        .finally(()=>{if(active)setLoading(false);});
    }
    return()=>{active=false;};
  },[run.id,revision,busy,requested,refresh]);
  const current=Boolean(loaded&&loaded.revision===revision&&loaded.refresh===refresh&&!busy&&!loading&&!error);
  return <section aria-label="Source DOI annotations" className="research-exports">
    <h3>Source DOI annotations</h3><p className="research-meta">User-provided associations, not externally verified. These annotations do not enrich citation or BibTeX exports.</p>
    <button disabled={busy||loading} onClick={()=>{setRequested(true);setRefresh(value=>value+1);}}>{requested?'Refresh DOI annotations':'Load DOI annotations'}</button>
    {requested&&!current&&!error && <p role="status">{busy?'DOI information is unavailable during a record update.':'Loading current DOI annotations…'}</p>}
    {error && <p role="alert" className="research-error">{error}</p>}
    {current&&loaded?.view.sources.length===0 && <p>No processed sources or DOI history.</p>}
    {current&&loaded?.view.conflicts.map(conflict=><p key={conflict.doi} className="research-notice">Duplicate user-supplied DOI {conflict.doi}: {conflict.source_ids.map(id=>loaded.view.sources.find(item=>item.source.id===id)?.source.title+' ('+id+')').join(', ')}. Sources remain separate.</p>)}
    {loaded?.view.sources.map(identity=><IdentityCard key={identity.source.id} identity={identity} events={loaded.history.filter(event=>event.source_id===identity.source.id)} current={current} disabled={!current||busy||!identity.active} onRecord={onRecord}/>)}
  </section>;
}

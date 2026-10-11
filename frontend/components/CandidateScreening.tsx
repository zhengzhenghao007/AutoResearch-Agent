'use client';

import { useEffect, useId, useRef, useState } from 'react';
import type { Candidate, CandidateDecision } from '@/types/research';

export default function CandidateScreening({candidate, events, disabled, onRecord}: {
  candidate: Candidate;
  events: CandidateDecision[];
  disabled: boolean;
  onRecord: (decision: CandidateDecision['decision'], reason: string) => Promise<boolean>;
}) {
  const id=useId();
  const [decision,setDecision]=useState<CandidateDecision['decision']>('include');
  const [reason,setReason]=useState('');
  const [error,setError]=useState('');
  const [pending,setPending]=useState(false);
  const alive=useRef(true);
  const submitting=useRef(false);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  const latest=events.at(-1);
  async function submit() {
    if(disabled||submitting.current||!reason.trim())return;
    submitting.current=true;setPending(true);setError('');
    try { if(await onRecord(decision,reason.trim()) && alive.current)setReason(''); }
    catch(error) { if(alive.current)setError(error instanceof Error?error.message:'Unable to record screening. Reopen the record to check its state.'); }
    finally {submitting.current=false;if(alive.current)setPending(false);}
  }
  return <fieldset className="research-screening" aria-label={`Screening for ${candidate.title}`}>
    <legend>Screening annotation</legend>
    <p className="research-meta">Annotations do not change analysis selection or certify scientific validity.</p>
    {latest ? <p>Latest: <strong>{latest.decision==='include'?'Include':'Exclude'}</strong> — {latest.reason} <time dateTime={latest.decided_at}>{latest.decided_at}</time></p> : <p className="research-meta">No screening annotation.</p>}
    {events.length>0 && <details><summary>Screening history ({events.length})</summary><ol>{events.map((event,index)=><li key={index}><strong>{event.decision==='include'?'Include':'Exclude'}</strong> — {event.reason} <time dateTime={event.decided_at}>{event.decided_at}</time></li>)}</ol></details>}
    <form onSubmit={event=>{event.preventDefault();void submit();}}>
      <label htmlFor={`${id}-decision`}>Screening decision</label>
      <select id={`${id}-decision`} value={decision} disabled={disabled||pending} onChange={event=>setDecision(event.target.value as CandidateDecision['decision'])}><option value="include">Include</option><option value="exclude">Exclude</option></select>
      <label htmlFor={`${id}-reason`}>Screening reason</label>
      <textarea id={`${id}-reason`} required maxLength={2000} value={reason} disabled={disabled||pending} onChange={event=>setReason(event.target.value)}/>
      <button disabled={disabled||pending||!reason.trim()}>Record screening decision</button>
    </form>
    {pending && <p role="status">Recording screening decision…</p>}
    {error && <p role="alert" className="research-error">{error} Check the saved record before submitting again; repeated submissions add history entries.</p>}
  </fieldset>;
}

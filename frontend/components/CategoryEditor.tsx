'use client';

import { useEffect, useId, useRef, useState } from 'react';
import type { Claim, Category } from '@/types/research';

export default function CategoryEditor({claim,disabled,onSave}:{claim:Claim;disabled:boolean;onSave:(claim:Claim,category:Category,reason:string)=>Promise<boolean>}) {
  const id=useId();
  const [decision,setDecision]=useState<Category>(claim.category);
  const [reason,setReason]=useState('');
  const [error,setError]=useState('');
  const [pending,setPending]=useState(false);
  const alive=useRef(true);
  const submitting=useRef(false);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);

  async function submit() {
    if(disabled||submitting.current||(!reason.trim()||decision===claim.category))return;
    submitting.current=true;setPending(true);setError('');
    try { if(await onSave(claim,decision,reason.trim()) && alive.current)setReason(''); }
    catch(error) { if(alive.current)setError(error instanceof Error?error.message:'Unable to save category revision. Reopen the record to check its state.'); }
    finally {submitting.current=false;if(alive.current)setPending(false);}
  }
  return <fieldset className="research-screening" aria-label={`Revise ${claim.id}`}>
    <legend>Claim category</legend><blockquote>{claim.text}</blockquote><p>Current: {claim.category}</p>
    <form onSubmit={event=>{event.preventDefault();void submit();}}>
      <label htmlFor={`${id}-category`}>New category</label>
      <select id={`${id}-category`} value={decision} disabled={disabled||pending} onChange={e=>setDecision(e.target.value as Category)}>{['problem','method','dataset','experiment','result','limitation','future_work'].map(value=><option key={value} value={value}>{value}</option>)}</select>
      <label htmlFor={`${id}-reason`}>Revision reason</label><textarea id={`${id}-reason`} required maxLength={2000} value={reason} disabled={disabled||pending} onChange={e=>setReason(e.target.value)}/>
      <button disabled={disabled||pending||!reason.trim()||decision===claim.category}>Save category revision</button>
    </form>
    {pending&&<p role="status">Saving category revision…</p>}{error&&<p role="alert">{error} Reopen the saved record before retrying an uncertain write.</p>}
  </fieldset>;
}
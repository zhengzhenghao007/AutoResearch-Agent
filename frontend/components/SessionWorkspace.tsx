'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {researchApi,setResearchToken,type ResearchSession} from '@/lib/research-api';
import EvidenceWorkspace from './EvidenceWorkspace';

export default function SessionWorkspace({onMode,showWorkspace=true}:{onMode?:(mode:'local'|'deployment'|null)=>void;showWorkspace?:boolean}) {
 const [session,setSession]=useState<ResearchSession|null>(null);
 const [token,setToken]=useState(''),[error,setError]=useState(''),[pending,setPending]=useState(true);
 const [needsAuth,setNeedsAuth]=useState(false);
 const [leaveBlocked,setLeaveBlocked]=useState(false);
 const generation=useRef(0);
 const [epoch,setEpoch]=useState(0);
 const invalidate=useCallback(()=>{generation.current++;},[]);
 useEffect(()=>{
  const current=++generation.current;
  researchApi.session().then(value=>{if(current===generation.current){setSession(value);onMode?.(value.mode);}})
   .catch(e=>{if(current===generation.current){setError(e.message);setNeedsAuth(e.status===401||e.status===403);}})
   .finally(()=>{if(current===generation.current)setPending(false);});
  return invalidate;
 },[onMode,invalidate]);
 function clearRecord(){const url=new URL(window.location.href);url.searchParams.delete('run');url.searchParams.delete('stage');window.history.replaceState({},'',url);}
 async function connect(){
  if(leaveBlocked)return;
  const current=++generation.current;
  setNeedsAuth(true);
  setEpoch(value=>value+1);setSession(null);onMode?.(null);clearRecord();setError('');setPending(true);
  setResearchToken(token);setToken('');
  try{const value=await researchApi.session();if(current===generation.current){setSession(value);onMode?.(value.mode);}}
  catch(e){if(current===generation.current){setResearchToken('');setError(e instanceof Error?e.message:'Connection failed');}}
  finally{if(current===generation.current)setPending(false);}
 }
 function disconnect(){if(leaveBlocked)return;generation.current++;setResearchToken('');setSession(null);setToken('');setError('');setPending(false);setNeedsAuth(true);onMode?.(null);clearRecord();}
 return <><section className="research-workspace research-session" aria-label="Session">
  {!pending&&(needsAuth||session?.mode==='deployment')&&session?.mode!=='local'&&<form onSubmit={e=>{e.preventDefault();void connect();}}>
   <label htmlFor="session-token">Access token</label>{' '}
   <input id="session-token" type="password" autoComplete="off" value={token} disabled={pending} onChange={e=>setToken(e.target.value)}/>{' '}
   <button disabled={pending||leaveBlocked||!token.trim()}>Connect</button>{' '}
   {session&&<button type="button" disabled={leaveBlocked} onClick={disconnect}>Disconnect</button>}
  </form>}
  {pending&&<p role="status">Checking session…</p>}
  {error&&<p role="alert">{error}</p>}
  {!pending&&!session&&!needsAuth&&<p>Start the research API, then <button onClick={()=>window.location.reload()}>Retry connection</button>.</p>}
  {session&&<p>{session.mode==='local'?'Local workspace · Saved on this computer':`${session.user_id} · ${session.role==='reader'?'Read-only access':'Editing access'}`}</p>}
  {leaveBlocked&&session?.mode==='deployment'&&<p>Save or discard writing changes and wait for active requests before switching sessions.</p>}
  {!pending&&(needsAuth||session?.mode==='deployment')&&session?.mode!=='local'&&<p>Credentials stay in memory for this tab. Reloading requires reconnecting in deployment mode.</p>}
 </section>{session&&showWorkspace&&<EvidenceWorkspace key={epoch} jobsEnabled={session.jobs_enabled} readOnly={session.role==='reader'} onLeaveBlockedChange={setLeaveBlocked}/>}</>;
}

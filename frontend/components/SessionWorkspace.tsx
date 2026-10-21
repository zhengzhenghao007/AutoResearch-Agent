'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {researchApi,setResearchToken,type ResearchSession} from '@/lib/research-api';
import EvidenceWorkspace from './EvidenceWorkspace';

export default function SessionWorkspace({onMode}:{onMode?:(mode:'local'|'deployment'|null)=>void}) {
 const [session,setSession]=useState<ResearchSession|null>(null);
 const [token,setToken]=useState(''),[error,setError]=useState(''),[pending,setPending]=useState(true);
 const generation=useRef(0);
 const [epoch,setEpoch]=useState(0);
 const invalidate=useCallback(()=>{generation.current++;},[]);
 useEffect(()=>{
  const current=++generation.current;
  researchApi.session().then(value=>{if(current===generation.current){setSession(value);onMode?.(value.mode);}})
   .catch(e=>{if(current===generation.current)setError(e.message);})
   .finally(()=>{if(current===generation.current)setPending(false);});
  return invalidate;
 },[onMode,invalidate]);
 function clearRecord(){const url=new URL(window.location.href);url.searchParams.delete('run');window.history.replaceState({},'',url);}
 async function connect(){
  const current=++generation.current;
  setEpoch(value=>value+1);setSession(null);onMode?.(null);clearRecord();setError('');setPending(true);
  setResearchToken(token);setToken('');
  try{const value=await researchApi.session();if(current===generation.current){setSession(value);onMode?.(value.mode);}}
  catch(e){if(current===generation.current){setResearchToken('');setError(e instanceof Error?e.message:'Connection failed');}}
  finally{if(current===generation.current)setPending(false);}
 }
 function disconnect(){generation.current++;setResearchToken('');setSession(null);setToken('');setError('');setPending(false);onMode?.(null);clearRecord();}
 return <><section className="research-workspace" aria-label="Session">
  <form onSubmit={e=>{e.preventDefault();void connect();}}>
   <label htmlFor="session-token">Access token</label>{' '}
   <input id="session-token" type="password" autoComplete="off" value={token} disabled={pending} onChange={e=>setToken(e.target.value)}/>{' '}
   <button disabled={pending||!token.trim()}>Connect</button>{' '}
   {session&&<button type="button" onClick={disconnect}>Disconnect</button>}
  </form>
  {pending&&<p role="status">Checking session…</p>}
  {error&&<p role="alert">{error}</p>}
  {session&&<p>{session.mode} · {session.user_id} · {session.role}{session.role==='reader'?' — Read-only access':''}</p>}
  <p>Credentials stay in memory for this tab. Reloading requires reconnecting in deployment mode.</p>
 </section>{session&&<EvidenceWorkspace key={epoch} jobsEnabled={session.jobs_enabled} readOnly={session.role==='reader'}/>}</>;
}

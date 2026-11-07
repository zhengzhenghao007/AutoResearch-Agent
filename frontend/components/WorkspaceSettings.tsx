'use client';
import {useState} from 'react';
import {researchApi,type EditingProfile,type EditingPolicy} from '@/lib/research-api';
function AcademicEditingSettings(){
 const [policy,setPolicy]=useState<EditingPolicy|null>(null);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 async function load(profile?:EditingProfile){
  setLoading(true);setError('');
  try{setPolicy(await (profile?researchApi.updateEditingPolicy(profile):researchApi.editingPolicy()));}
  catch(failure){setError(failure instanceof Error?failure.message:'Could not load the editing policy.');}
  finally{setLoading(false);}
 }
 return <details onToggle={event=>{if(event.currentTarget.open&&!policy&&!loading)void load();}}>
  <summary>Academic Humanizer</summary>
  <p>Academic editing runs automatically on generated prose in English and Chinese. It runs locally and uses no model tokens.</p>
  {policy&&<label>Cleanup profile<select value={policy.profile} disabled={loading||!policy.editable} onChange={event=>void load(event.target.value as EditingProfile)}><option value="minimal">Remove introductory filler</option><option value="standard">Also simplify introductory conjunctions</option></select></label>}
  {policy&&!policy.editable&&<p>Your deployment administrator manages this setting.</p>}
  {loading&&<p role="status">Loading editing policy…</p>}
  {error&&<p role="alert">{error} <button onClick={()=>void load()}>Retry</button></p>}
 </details>;
}
export default function WorkspaceSettings({runId,onTasks}:{runId?:string;onTasks:()=>void}) {
 const [skills,setSkills]=useState<{id:string;version:number;description:string;permissions:string[]}[]>([]);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 async function load(){if(!runId)return;setBusy(true);setError('');try{const result=await researchApi.researchSkills(runId);setSkills(result.items);}catch(failure){setError(failure instanceof Error?failure.message:'Could not load skills.');}finally{setBusy(false);}}
 return <details className="workspace-settings" onKeyDown={event=>{if(event.key==='Escape')event.currentTarget.open=false;}}><summary>Settings</summary><div className="settings-content">
  <h2>Workspace settings</h2><AcademicEditingSettings/>
  <details><summary>Agent and model configuration</summary><p>Research tasks choose the available evidence tools from the plan. Review the plan and adjust task limits before continuing.</p><button disabled={!runId} onClick={event=>{event.currentTarget.closest('details.workspace-settings')?.removeAttribute('open');onTasks();}}>Open execution controls</button><p>Model, API credentials and prompts are managed by the backend configuration. Model analysis is enabled explicitly in the reading and review tools.</p></details>
  <details><summary>Available research skills</summary><p>Skills are versioned on the server. Manual tool assignment is not available in this workspace.</p><button disabled={!runId||busy} onClick={()=>void load()}>{busy?'Loading skills…':'Load skill directory'}</button>{!runId&&<p>Open a project to inspect its capabilities.</p>}{error&&<p role="alert">{error}</p>}{skills.map(skill=><article key={skill.id}><strong>{skill.id.replaceAll('_',' ')} · v{skill.version}</strong><p>{skill.description}</p></article>)}</details>
  <details><summary>Developer tools</summary><p>Execution history and source bindings are available inside each research task.</p><a href="/legacy">Open legacy interface</a></details>
 </div></details>;
}

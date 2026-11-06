'use client';
import {useState} from 'react';
import {researchApi} from '@/lib/research-api';
export default function WorkspaceSettings({runId,onTasks}:{runId?:string;onTasks:()=>void}) {
 const [skills,setSkills]=useState<{id:string;version:number;description:string;permissions:string[]}[]>([]);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 async function load(){if(!runId)return;setBusy(true);setError('');try{const result=await researchApi.researchSkills(runId);setSkills(result.items);}catch(failure){setError(failure instanceof Error?failure.message:'Could not load skills.');}finally{setBusy(false);}}
 return <details className="workspace-settings" onKeyDown={event=>{if(event.key==='Escape')event.currentTarget.open=false;}}><summary>Settings</summary><div className="settings-content">
  <h2>Workspace settings</h2>
  <details><summary>Agent and model configuration</summary><p>Research tasks choose the available evidence tools from the plan. Review the plan and adjust task limits before continuing.</p><button disabled={!runId} onClick={event=>{event.currentTarget.closest('details.workspace-settings')?.removeAttribute('open');onTasks();}}>Open execution controls</button><p>Model, API credentials and prompts are managed by the backend configuration. Model analysis is enabled explicitly in the reading and review tools.</p></details>
  <details><summary>Available research skills</summary><p>Skills are versioned on the server. Manual tool assignment is not available in this workspace.</p><button disabled={!runId||busy} onClick={()=>void load()}>{busy?'Loading skills…':'Load skill directory'}</button>{!runId&&<p>Open a project to inspect its capabilities.</p>}{error&&<p role="alert">{error}</p>}{skills.map(skill=><article key={skill.id}><strong>{skill.id.replaceAll('_',' ')} · v{skill.version}</strong><p>{skill.description}</p></article>)}</details>
  <details><summary>Developer tools</summary><p>Execution history and source bindings are available inside each research task.</p><a href="/legacy">Open legacy interface</a></details>
 </div></details>;
}

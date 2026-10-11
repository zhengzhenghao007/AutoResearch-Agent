'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {SourceDuplicateReport} from '@/types/source-duplicates';

const descriptions={
  exact_arxiv_identifier:{title:'Exact arXiv identifier',detail:'Literal identifiers only. Unspecified versions, v1 and v2 remain distinct.'},
  same_pdf_bytes:{title:'Matching stored PDF hash',detail:'Stored SHA-256 metadata matches; original PDF bytes are not revalidated.'},
  shared_user_supplied_doi:{title:'Shared user-supplied DOI',detail:'Not externally verified. A user association does not establish that these are the same paper.'},
};
export default function SourceDuplicateClues({runId,revision}:{runId:string;revision:number}){
  return <DuplicatePanel key={`${runId}:${revision}`} runId={runId}/>;
}
function DuplicatePanel({runId}:{runId:string}){
  const active=useRef(false);const inFlight=useRef(false);
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  const [report,setReport]=useState<SourceDuplicateReport|null>(null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  async function load(){
    if(inFlight.current)return;
    inFlight.current=true;setBusy(true);setError('');setReport(null);
    try{const result=await researchApi.sourceDuplicates(runId);
      if(result.run_id!==runId)throw new Error('Report returned a different research record. Reopen the record and try again.');
      if(active.current)setReport(result);
    }catch(error){if(active.current)setError(error instanceof Error?error.message:'Unable to load duplicate clues.');}
    finally{inFlight.current=false;if(active.current)setBusy(false);}
  }
  function download(){
    if(!report)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json;charset=utf-8'}));
    const anchor=document.createElement('a');anchor.href=url;
    anchor.download=`source-duplicates-${/^[a-f0-9]{32}$/.test(runId)?runId:'record'}.json`;
    document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="research-exports research-duplicate-clues" aria-label="Duplicate clues">
    <h3>Duplicate clues</h3><p className="research-meta">Read-only clues, not verified paper equivalence. Sources remain separate and analysis selection is unchanged.</p>
    <div className="research-row"><button disabled={busy} onClick={()=>void load()}>Load duplicate clues</button>{report&&<button onClick={download}>Download duplicate clues JSON</button>}</div>
    {busy&&<p role="status">Loading duplicate clues…</p>}{error&&<p role="alert" className="research-error">{error}</p>}
    {report&&<><section aria-label="Duplicate groups"><h4>Duplicate groups</h4>{report.groups.length===0&&<p className="research-empty">No duplicate groups found.</p>}
      {report.groups.map((group,index)=><article key={index}><h5>{descriptions[group.kind].title}</h5><p>{descriptions[group.kind].detail}</p><p className="research-prose">{group.identity_value}</p><ul>{group.members.map(member=><li key={`${member.entity_type}:${member.entity_id}`}><strong>{member.title}</strong><p className="research-meta">{member.entity_type==='candidate'?'Candidate':'Processed source'}: {member.entity_id}</p><p className="research-prose">{member.uri}</p></li>)}</ul></article>)}
    </section><section aria-label="Candidate-source links"><h4>Candidate-source links</h4><p className="research-meta">A candidate and its processed source are not counted as two duplicate papers.</p>
      {report.candidate_source_links.length===0?<p className="research-empty">No candidate-source links found.</p>:<ul>{report.candidate_source_links.map((link,index)=><li key={index}>Candidate {link.candidate_id} → source {link.source_id}; arXiv {link.arxiv_identifier}</li>)}</ul>}
    </section></>}
  </section>;
}

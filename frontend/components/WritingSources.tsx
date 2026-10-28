'use client';
import {useState} from 'react';
import type {DraftBlock} from '@/types/manuscript-draft';
import type {ManuscriptSection} from '@/types/manuscript';
import type {ResearchRun} from '@/types/research';
import ResearchAssetPreview from './ResearchAssetPreview';
import {sourcePdf} from './EvidenceViewer';

type Props={blocks:DraftBlock[];sections:ManuscriptSection[];run?:ResearchRun;disabled:boolean;onInsert:(sectionId:string,block:DraftBlock)=>void};
export default function WritingSources({blocks,sections,run,disabled,onInsert}:Props) {
 const [query,setQuery]=useState(''),[filter,setFilter]=useState('all'),[selectedId,setSelectedId]=useState(''),[target,setTarget]=useState(''),[limit,setLimit]=useState(15);
 const usable=blocks.filter(b=>b.kind!=='placeholder');
 const matches=usable.filter(b=>(filter==='all'||b.kind===filter)&&`${b.text} ${b.paper?.source.title??''} ${b.computation?.title??''} ${b.asset?.title??''}`.toLowerCase().includes(query.trim().toLowerCase()));
 const selected=usable.find(b=>b.id===selectedId);
 const section=sections.find(s=>s.id===target)??sections[0];
 const paper=selected?.paper;
 const document=paper?run?.papers.find(p=>p.document.source.id===paper.source.id&&p.document.source.sha256===paper.source.sha256)?.document:undefined;
 const title=(b:DraftBlock)=>b.paper?.source.title??b.asset?.title??b.computation?.title??'Source material';
 return <aside className="writing-sources" aria-label="Writing source drawer">
  <h3>Sources beside your draft</h3><p className="research-meta">Read, then insert with its saved reference. These sources belong to the current manuscript snapshot.</p>
  <label>Search writing sources<input type="search" value={query} onChange={e=>{setQuery(e.target.value);setLimit(15);}} placeholder="Paper, quotation or dataset"/></label>
  <label>Source type<select value={filter} onChange={e=>{setFilter(e.target.value);setLimit(15);}}><option value="all">All source material</option><option value="paper_claim">Paper quotations</option><option value="user_statistics">Data statistics</option><option value="research_asset">Saved figures and tables</option></select></label>
  <p className="research-meta">{matches.length} matching references</p>
  <div className="writing-source-list">{matches.slice(0,limit).map(b=><button key={b.id} aria-label={`Inspect source: ${title(b)}`} aria-pressed={b.id===selectedId} onClick={()=>setSelectedId(b.id)}><strong>{title(b)}</strong><span>{b.paper?`PDF page ${b.paper.evidence.map(e=>e.page).join(', ')}`:b.asset?'Saved research material':'Computed user observations'}</span><p>{b.text}</p></button>)}{!matches.length&&<p>No matching source material.</p>}{matches.length>limit&&<button onClick={()=>setLimit(n=>n+15)}>Show more sources</button>}</div>
  {selected&&<div className="writing-source-detail"><h4>{title(selected)}</h4>
   {paper?<>{paper.evidence.map(e=><blockquote key={e.id}><p>{e.quote}</p><footer>PDF page {e.page}</footer></blockquote>)}{paper.truncated&&<p className="research-notice">This paper was only partially extracted.</p>}{sourcePdf(paper.source.uri,paper.evidence[0]?.page)&&<a href={sourcePdf(paper.source.uri,paper.evidence[0]?.page)!} target="_blank" rel="noopener noreferrer">Open original source PDF</a>}
    {document?<details><summary>Read surrounding source pages</summary>{[...new Set(paper.evidence.map(e=>e.page))].map(page=><article key={page}><h5>Page {page}</h5><p className="research-prose">{document.pages.find(p=>p.number===page)?.text??'Page unavailable in the saved extraction.'}</p></article>)}</details>:<p className="research-meta">Saved quotation snapshot. Full page context is unavailable here; inspect the original paper.</p>}
   </>:selected.asset?<ResearchAssetPreview asset={selected.asset}/>:<p>{selected.text}</p>}
   <label>Insert into chapter<select value={section?.id??''} disabled={disabled} onChange={e=>setTarget(e.target.value)}>{sections.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label>
   <button className="research-primary" disabled={disabled||!section||section.sentences.length>=200||sections.reduce((n,s)=>n+s.sentences.length,0)>=500} onClick={()=>{if(section)onInsert(section.id,selected);}}>Insert with reference</button>
   <p className="research-meta">Adds a new paragraph at the end of the selected chapter. Save the revision to keep it.</p>
  </div>}
 </aside>;
}

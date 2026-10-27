'use client';
import {useState} from 'react';
import type {PaperEvidence,ResearchRun} from '@/types/research';
import {sourcePdf} from './EvidenceViewer';

export default function ReadingDesk({run,focusEvidence,focusSource='',onFocus}:{run:ResearchRun;focusEvidence:string;focusSource?:string;onFocus:(id:string)=>void}) {
 const [sourceId,setSourceId]=useState(focusSource);
 const paper=run.papers.find(p=>p.evidence.some(e=>e.id===focusEvidence))??run.papers.find(p=>p.document.source.id===sourceId)??run.papers[0];
 return <section aria-label="Reading and evidence"><h3>Read with the source beside you</h3><p className="research-meta">Select a paper and an extract. Check the quotation against the surrounding page before using it.</p>
 {!paper?<p className="research-empty">No evidence extracted. Add a text-based PDF in Library, or analyze selected papers.</p>:<><label htmlFor="reading-source">Paper</label><select id="reading-source" value={paper.document.source.id} onChange={e=>{setSourceId(e.target.value);onFocus('');}}>{run.papers.map(p=><option key={p.document.source.id} value={p.document.source.id}>{p.document.source.title}</option>)}</select><PaperReader key={paper.document.source.id} paper={paper} focusEvidence={focusEvidence} onFocus={onFocus}/></>}
 </section>;
}
function PaperReader({paper,focusEvidence,onFocus}:{paper:PaperEvidence;focusEvidence:string;onFocus:(id:string)=>void}) {
 const [query,setQuery]=useState(''),[category,setCategory]=useState('all'),[limit,setLimit]=useState(12);
 const [browsedPage,setBrowsedPage]=useState(0);
 const selected=paper.evidence.find(e=>e.id===focusEvidence)??paper.evidence[0];
 const page=paper.document.pages.find(p=>p.number===(browsedPage||selected?.page))??paper.document.pages[0];
 const claims=paper.claims.filter(c=>(category==='all'||c.category===category)&&c.text.toLowerCase().includes(query.toLowerCase()));
 const pdf=sourcePdf(paper.document.source.uri,page?.number);
 return <><div className="reading-meta"><span>{paper.document.pages.length} of {paper.document.total_pages} pages extracted</span><span>{paper.evidence.length} quotations</span>{paper.document.truncated&&<strong>Truncated document</strong>}</div>
 <div className="reading-desk"><div className="reading-extracts"><label htmlFor="extract-search">Find in extracts</label><input id="extract-search" type="search" value={query} onChange={e=>{setQuery(e.target.value);setLimit(12);}} placeholder="Search a method, dataset or phrase"/><label htmlFor="extract-category">Category</label><select id="extract-category" value={category} onChange={e=>{setCategory(e.target.value);setLimit(12);}}><option value="all">All categories</option>{['problem','method','dataset','experiment','result','limitation','future_work'].map(c=><option key={c} value={c}>{c.replaceAll('_',' ')}</option>)}</select><p className="research-meta">{claims.length} matching extracts · categories are automatic</p>
 {claims.slice(0,limit).map(c=><button className="extract-choice" aria-pressed={c.evidence_ids.includes(selected?.id??'')} key={c.id} onClick={()=>{setBrowsedPage(0);onFocus(c.evidence_ids[0]);}}><span>{c.category.replaceAll('_',' ')} · p. {paper.evidence.find(e=>e.id===c.evidence_ids[0])?.page}</span><p>{c.text}</p></button>)}{claims.length>limit&&<button onClick={()=>setLimit(n=>n+12)}>Show more extracts</button>}{!claims.length&&<p>No extracts match. Browse the source pages, or try another category or search term.</p>}</div>
 <div className="reading-context" aria-live="polite">{selected&&<><h4>Selected quotation</h4><blockquote className="research-evidence" id={`research-evidence-${selected.id}`} tabIndex={-1}><p>{selected.quote}</p><footer>{paper.document.source.title} · PDF page {selected.page}</footer></blockquote></>}
 <label htmlFor="source-page">Source page</label><select id="source-page" value={page?.number} onChange={e=>setBrowsedPage(Number(e.target.value))}>{paper.document.pages.map(p=><option key={p.number} value={p.number}>Page {p.number}</option>)}</select>
 {selected&&page?.number!==selected.page&&<p className="research-meta">Browsing a different page. <button onClick={()=>setBrowsedPage(0)}>Return to quotation page</button></p>}
 <h4>Extracted page {page?.number}</h4><p className="research-meta">PDF text extraction can disrupt columns, symbols and tables. Check the original PDF for precise interpretation.</p>{pdf?<a href={pdf} target="_blank" rel="noopener noreferrer">Open source PDF at page {page?.number}</a>:<p className="research-meta">Uploaded source: open your original PDF alongside this text.</p>}
 <div className="source-page" tabIndex={0} aria-label={`Extracted page ${page?.number}`}><p className="research-prose">{page?.text||'No readable page text.'}</p></div>
 <details><summary>Source details and extraction gaps</summary><p>Source: {paper.document.source.uri}</p><p>Missing fields: {paper.missing_fields.join(', ')||'none reported'}</p><p>SHA256: {paper.document.source.sha256}</p></details></div></div></>;
}

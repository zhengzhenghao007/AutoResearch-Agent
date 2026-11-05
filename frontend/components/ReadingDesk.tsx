'use client';
import {useState,useRef} from 'react';
import PaperQuickRead from './PaperQuickRead';
import LocalPaperOutline from './LocalPaperOutline';
import type {PaperEvidence,ResearchRun} from '@/types/research';
import OriginalPdf from './OriginalPdf';
import {sourcePdf} from './EvidenceViewer';

export default function ReadingDesk({run,focusEvidence,focusSource='',onFocus,readOnly=false,onDirection}:{run:ResearchRun;focusEvidence:string;focusSource?:string;onFocus:(id:string)=>void;readOnly?:boolean;onDirection?:(text:string)=>void}) {
 const [sourceId,setSourceId]=useState(focusSource);
 const paper=run.papers.find(p=>p.evidence.some(e=>e.id===focusEvidence))??run.papers.find(p=>p.document.source.id===sourceId)??run.papers[0];
 return <section aria-label="Reading and evidence"><h3>Read with the source beside you</h3><p className="research-meta">Select a paper and an extract. Check the quotation against the surrounding page before using it.</p>
 {!paper?<p className="research-empty">No evidence extracted. Add a text-based PDF in Library, or analyze selected papers.</p>:<><label htmlFor="reading-source">Paper</label><select id="reading-source" value={paper.document.source.id} onChange={e=>{setSourceId(e.target.value);onFocus('');}}>{run.papers.map(p=><option key={p.document.source.id} value={p.document.source.id}>{p.document.source.title}</option>)}</select><h3 className="current-paper-title">{paper.document.source.title}</h3><PaperReader key={`${paper.document.source.id}:${run.research_goal??''}`} runId={run.id} goal={run.research_goal} readOnly={readOnly} onDirection={onDirection} paper={paper} focusEvidence={focusEvidence} onFocus={onFocus}/></>}
 </section>;
}
function PaperReader({paper,focusEvidence,onFocus,runId,goal,readOnly,onDirection}:{paper:PaperEvidence;focusEvidence:string;onFocus:(id:string)=>void;runId:string;goal?:string|null;readOnly:boolean;onDirection?:(text:string)=>void}) {
 const [query,setQuery]=useState(''),[category,setCategory]=useState('all'),[limit,setLimit]=useState(12);
 const [browsedPage,setBrowsedPage]=useState(0);
 const [pageQuery,setPageQuery]=useState('');
 const searchTerm = pageQuery.trim();
 const pages = paper.document.pages;
 const [quickQuote,setQuickQuote]=useState('');
 const contextRef=useRef<HTMLDivElement>(null);
 const selected=paper.evidence.find(e=>e.id===focusEvidence)??paper.evidence[0];
 const page=paper.document.pages.find(p=>p.number===(browsedPage||selected?.page))??paper.document.pages[0];
 const pageIndex = pages.indexOf(page);
 const matchingPages = searchTerm ? pages.filter(item => item.text.toLowerCase().includes(searchTerm.toLowerCase())) : [];
 function browse(number:number) {
  setQuickQuote('');
  setBrowsedPage(number);
 }
 const claims=paper.claims.filter(c=>(category==='all'||c.category===category)&&c.text.toLowerCase().includes(query.toLowerCase()));
 const pdf=sourcePdf(paper.document.source.uri,page?.number);
 function showPassage(number:number,quote:string) {
  setBrowsedPage(number);
  setQuickQuote(quote);
  contextRef.current?.scrollIntoView?.({behavior:'smooth',block:'start'});
 }
 return <><PaperQuickRead runId={runId} sourceId={paper.document.source.id} goal={goal} readOnly={readOnly} onDirection={onDirection} onPage={showPassage}/><LocalPaperOutline paper={paper} onPage={showPassage}/><div className="reading-meta"><span>{paper.document.pages.length} of {paper.document.total_pages} pages extracted</span><span>{paper.evidence.length} quotations</span>{paper.document.truncated&&<strong>Truncated document</strong>}</div>
 <div className="reading-desk"><div className="reading-extracts"><label htmlFor="extract-search">Find in extracts</label><input id="extract-search" type="search" value={query} onChange={e=>{setQuery(e.target.value);setLimit(12);}} placeholder="Search a method, dataset or phrase"/><label htmlFor="extract-category">Category</label><select id="extract-category" value={category} onChange={e=>{setCategory(e.target.value);setLimit(12);}}><option value="all">All categories</option>{['problem','method','dataset','experiment','result','limitation','future_work'].map(c=><option key={c} value={c}>{c.replaceAll('_',' ')}</option>)}</select><p className="research-meta">{claims.length} matching extracts · categories are automatic</p>
 {claims.slice(0,limit).map(c=><button className="extract-choice" aria-pressed={c.evidence_ids.includes(selected?.id??'')} key={c.id} onClick={()=>{setQuickQuote('');setBrowsedPage(0);onFocus(c.evidence_ids[0]);}}><span>{c.category.replaceAll('_',' ')} · p. {paper.evidence.find(e=>e.id===c.evidence_ids[0])?.page}</span><p>{c.text}</p></button>)}{claims.length>limit&&<button onClick={()=>setLimit(n=>n+12)}>Show more extracts</button>}{!claims.length&&<p>No extracts match. Browse the source pages, or try another category or search term.</p>}</div>
 <div ref={contextRef} className="reading-context" aria-live="polite">{quickQuote&&<blockquote className="research-evidence"><h4>Source passage</h4><p>{quickQuote}</p></blockquote>}{selected&&!quickQuote&&<><h4>Selected quotation</h4><blockquote className="research-evidence" id={`research-evidence-${selected.id}`} tabIndex={-1}><p>{selected.quote}</p><footer>{paper.document.source.title} · PDF page {selected.page}</footer></blockquote></>}
 <details><summary>Search paper text</summary>
 <label htmlFor="page-text-search">Find in extracted pages</label>
 <input id="page-text-search" type="search" value={pageQuery} onChange={event=>setPageQuery(event.target.value)}/>
 {searchTerm&&<><p role="status">{matchingPages.length} matching pages out of {pages.length} extracted.</p>
 {matchingPages.map(item=><button key={item.number} aria-label={`Show matching page ${item.number}`} onClick={()=>browse(item.number)}>Page {item.number}</button>)}</>}
 </details>
 <label htmlFor="source-page">Source page</label><select id="source-page" value={page?.number} onChange={e=>{setQuickQuote('');setBrowsedPage(Number(e.target.value));}}>{paper.document.pages.map(p=><option key={p.number} value={p.number}>Page {p.number}</option>)}</select>
 {pages.length>1&&<nav aria-label="Browse extracted pages">
 <button disabled={pageIndex<=0} onClick={()=>browse(pages[pageIndex-1].number)}>Previous page</button>
 <button disabled={pageIndex>=pages.length-1} onClick={()=>browse(pages[pageIndex+1].number)}>Next page</button>
 </nav>}
 {selected&&page?.number!==selected.page&&<p className="research-meta">Browsing a different page. <button onClick={()=>{setQuickQuote('');setBrowsedPage(0);}}>Return to quotation page</button></p>}
 <h4>Extracted page {page?.number}</h4>{paper.document.ocr_pages?.includes(page?.number??0)&&<p className="research-notice">This page was recognized with local OCR. Check words, equations and column order against the original PDF before citing.</p>}<p className="research-meta">PDF text extraction can disrupt columns, symbols and tables. Check the original PDF for precise interpretation.</p>{pdf?<a href={pdf} target="_blank" rel="noopener noreferrer">Open source PDF at page {page?.number}</a>:<OriginalPdf runId={runId} source={paper.document.source.id} page={page?.number??1} canAttach={!readOnly}/>}
 <div className="source-page" tabIndex={0} aria-label={`Extracted page ${page?.number}`}><p className="research-prose">{page?.text ? <HighlightedPassage text={page.text} term={searchTerm || quickQuote || (selected?.page===page.number ? selected.quote : '')}/> : 'No readable page text.'}</p></div>
 <details><summary>Source details and extraction gaps</summary><p>Source: {paper.document.source.uri}</p><p>Missing fields: {paper.missing_fields.join(', ')||'none reported'}</p><p>SHA256: {paper.document.source.sha256}</p></details></div></div></>;
}

function HighlightedPassage({text,term}:{text:string;term:string}) {
 if (!term) return <>{text}</>;
 const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
 return <>{text.split(new RegExp('('+escaped+')','gi')).map((part,index)=>
  index%2===1 ? <mark key={index}>{part}</mark> : part
 )}</>;
}
'use client';
import {useRef,useEffect,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {SearchBatch,SearchProvider} from '@/types/metadata-search';
const providers:SearchProvider[]=['arxiv','crossref','openalex','semantic_scholar'];
export default function MetadataSearch({runId,disabled}:{runId:string;disabled:boolean}) {
 const [query,setQuery]=useState('');
 const [sources,setSources]=useState<SearchProvider[]>(['crossref','openalex']);
 const [batches,setBatches]=useState<SearchBatch[]>([]);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const active=useRef(true);
 useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 async function load(search:boolean) {
  setBusy(true);setError('');
  try {
   if(search)await researchApi.metadataSearch(runId,query,sources);
   const result=await researchApi.metadataHistory(runId);
   if(active.current)setBatches(result.items);
  } catch(failure){if(active.current)setError(failure instanceof Error?failure.message:'Search failed.');}
  finally{if(active.current)setBusy(false);}
 }
 function download(batch:SearchBatch){
  const url=URL.createObjectURL(new Blob([JSON.stringify(batch,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download=`search-${batch.id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 return <details><summary>Search across literature databases</summary>
  <p>Search up to five results per database. Search history and metadata are saved to this project.</p>
  <form onSubmit={event=>{event.preventDefault();void load(true);}}>
   <fieldset disabled={disabled||busy}><label htmlFor="metadata-query">Literature search query</label><input id="metadata-query" value={query} onChange={event=>setQuery(event.target.value)} minLength={2} maxLength={500} required/>
   <fieldset><legend>Databases</legend>{providers.map(source=><label key={source}><input type="checkbox" checked={sources.includes(source)} onChange={event=>setSources(event.target.checked?[...sources,source]:sources.filter(item=>item!==source))}/>{source.replaceAll('_',' ')}</label>)}</fieldset>
   <button disabled={!sources.length||query.trim().length<2}>Search databases</button></fieldset>
  </form>
  <button disabled={busy} onClick={()=>void load(false)}>Load saved searches</button>
  {busy&&<p role="status">Loading search results…</p>}{error&&<p role="alert">{error}</p>}
  {batches.map(batch=><details key={batch.id}><summary>{batch.request.query} · {new Date(batch.created_at).toLocaleString()} · {batch.groups.length} records</summary>
   <p>{batch.scope}</p><button onClick={()=>download(batch)}>Download search record</button>
   {batch.sources.map(source=><p key={source.source}>{source.source}: {source.status} · {source.hits.length} records {source.error}</p>)}
   {batch.groups.map(group=><article key={group.key}><h4>{group.records[0].title}</h4>
    {group.records.map((hit,index)=><details key={`${hit.source}:${hit.source_id}:${index}`}><summary>{hit.source} · rank {hit.rank}</summary><p>{hit.title}</p><p>{hit.authors.join(', ')}</p><p>DOI {hit.doi??'unavailable'} · {hit.doi_status.replaceAll('_',' ')}</p>
    {hit.url&&<a href={hit.url} target="_blank" rel="noopener noreferrer">Open source record</a>} {' '}
    {hit.pdf_url&&<a href={hit.pdf_url} target="_blank" rel="noopener noreferrer">Open available PDF</a>}</details>)}
   </article>)}
  </details>)}
 </details>;
}

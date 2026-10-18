'use client';
import {useEffect,useRef,useState} from 'react';
import {researchApi} from '@/lib/research-api';
import type {ResearchRun} from '@/types/research';
import type {CsvMetadata,ExperimentDataset,ExperimentReport,ExperimentStatistics} from '@/types/experiments';

function download(text:string,name:string,type='application/json') {
  const url=URL.createObjectURL(new Blob([text],{type:`${type};charset=utf-8`}));
  const link=document.createElement('a');link.href=url;link.download=name;
  document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function original(dataset:ExperimentDataset):string {
  // Only decode the CSV envelope, never parse and reserialize numeric JSON input.
  return dataset.input_format==='csv' ? JSON.parse(dataset.raw_json).csv_text : dataset.raw_json;
}
type Props={run:ResearchRun;revision:number;busy:boolean;onImport:(file:File,format:'json'|'csv',metadata?:CsvMetadata)=>Promise<boolean>};
export default function Experiments(props:Props) {
  return <ExperimentPanel key={props.run.id} {...props}/>;
}
function ExperimentPanel({run,revision,busy,onImport}:Props) {
  const [format,setFormat]=useState<'json'|'csv'>('json');const [file,setFile]=useState<File|null>(null);
  const [title,setTitle]=useState('');const [protocol,setProtocol]=useState('');const [method,setMethod]=useState('');const [columns,setColumns]=useState('');
  const [pending,setPending]=useState(false);const [error,setError]=useState('');
  const fileRef=useRef<HTMLInputElement>(null);const active=useRef(false);const inFlight=useRef(false);
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  const datasets=run.experiments??[];
  async function submit() {
    if(!file||busy||inFlight.current||datasets.length>=20)return;
    setError('');
    const limit=format==='csv'?1:2;
    if(file.size>limit*1024*1024){setError(`Observation file exceeds ${limit} MiB.`);return;}
    let metadata:CsvMetadata|undefined;
    if(format==='csv') {
      const entries=columns.split(/\r?\n/).filter(line=>line.trim()).map(line=>{
        const separator=line.indexOf('=');
        if(separator<1)throw new Error('Use one column per line: name=unit (leave the unit empty if unknown).');
        return {name:line.slice(0,separator).trim(),unit:line.slice(separator+1).trim()||null};
      });
      if(!title.trim()||!entries.length){setError('CSV requires a title and declared columns.');return;}
      metadata={title:title.trim(),protocol:protocol.trim()||null,statistical_method:method.trim()||null,columns:entries};
    }
    inFlight.current=true;setPending(true);
    try {
      if(await onImport(file,format,metadata) && active.current) {
        setFile(null);if(fileRef.current)fileRef.current.value='';
      }
    } catch(e){if(active.current)setError(e instanceof Error?e.message:'Observation import failed.');}
    finally{inFlight.current=false;if(active.current)setPending(false);}
  }
  return <section className="research-exports research-experiments" aria-label="User experiment observations">
    <h3>User experiment observations</h3>
    <p>Offline user data, separate from paper evidence. Up to 20 datasets, 1 MiB per original file (2 MiB for a CSV metadata envelope), 1000 sample rows and 50 numeric columns. Data and scientific validity are unverified.</p>
    <form onSubmit={event=>{event.preventDefault();void submit().catch(e=>setError(e instanceof Error?e.message:'Invalid columns.'));}}>
      <label>Observation file format <select value={format} disabled={busy||pending} onChange={e=>setFormat(e.target.value as 'json'|'csv')}><option value="json">JSON with metadata</option><option value="csv">CSV with explicit metadata</option></select></label>
      <label>Observation file <input ref={fileRef} type="file" accept={format==='csv'?'.csv,text/csv':'.json,application/json'} disabled={busy||pending} onChange={e=>setFile(e.target.files?.[0]??null)}/></label>
      {format==='csv'&&<fieldset disabled={busy||pending}><legend>CSV metadata</legend>
        <label>Dataset title <input value={title} maxLength={200} required onChange={e=>setTitle(e.target.value)}/></label>
        <label>Protocol (optional) <textarea value={protocol} maxLength={10000} onChange={e=>setProtocol(e.target.value)}/></label>
        <label>Declared statistical method (optional) <textarea value={method} maxLength={2000} onChange={e=>setMethod(e.target.value)}/></label>
        <label>Columns and units <textarea value={columns} required maxLength={9000} placeholder={'temperature=C\nscore='} onChange={e=>setColumns(e.target.value)}/></label>
        <p>One column per line: name=unit. Leave the unit empty when unknown. CSV headers must be sample_id followed by these names in order. Empty numeric cells mean missing, not zero.</p>
      </fieldset>}
      <details><summary>JSON format example</summary><pre className="research-export-code">{'{"title":"Example only","protocol":null,"statistical_method":null,"columns":[{"name":"value","unit":null}],"rows":[{"sample_id":"sample-1","values":{"value":null}}]}'}</pre></details>
      <button disabled={busy||pending||!file||datasets.length>=20}>Import observations</button>
    </form>
    {pending&&<p role="status">Saving observations…</p>}{error&&<p role="alert">{error} Reopen the record before retrying an uncertain write.</p>}
    <h4>Saved datasets ({datasets.length}/20)</h4>
    {datasets.length===0?<p>No user observations imported.</p>:datasets.map(dataset=><details key={dataset.id}><summary>{dataset.data.title}</summary>
      <p>user_observation · {dataset.imported_at} · {dataset.data.rows.length} user-declared sample rows</p>
      <p>Dataset / input hash: {dataset.sha256}</p><p>Original file hash: {dataset.source_sha256??dataset.sha256}</p>
      <p>Protocol: {dataset.data.protocol??'Unknown'}</p><p>Declared method: {dataset.data.statistical_method??'Unknown'}</p>
      <button onClick={()=>download(original(dataset),`observations-${dataset.id}.${dataset.input_format==='csv'?'csv':'json'}`,dataset.input_format==='csv'?'text/csv':'application/json')}>Download original input</button>
      {dataset.input_format==='csv'&&<button onClick={()=>download(dataset.raw_json,`observation-envelope-${dataset.id}.json`)}>Download CSV with metadata</button>}
      <pre className="research-export-code">{original(dataset)}</pre>
    </details>)}
    {!busy&&<DataReports key={`${run.id}:${revision}`} runId={run.id}/>}
  </section>;
}
function DataReports({runId}:{runId:string}) {
  const [reports,setReports]=useState<{checks:ExperimentReport;stats:ExperimentStatistics}|null>(null);
  const [error,setError]=useState('');const [pending,setPending]=useState(false);
  const active=useRef(false);const inFlight=useRef(false);
  useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
  async function load() {
    if(inFlight.current)return;inFlight.current=true;setPending(true);setError('');setReports(null);
    try {
      const [checks,stats]=await Promise.all([researchApi.experiments(runId),researchApi.experimentStatistics(runId)]);
      if(checks.run_id!==runId||stats.run_id!==runId)throw new Error('Data report returned a different record.');
      if(active.current)setReports({checks,stats});
    }catch(e){if(active.current)setError(e instanceof Error?e.message:'Unable to load data report.');}
    finally{inFlight.current=false;if(active.current)setPending(false);}
  }
  return <div><button disabled={pending} onClick={()=>void load()}>Load data checks and statistics</button>
    {pending&&<p role="status">Computing descriptive statistics…</p>}{error&&<p role="alert">{error}</p>}
    {reports&&<><p>{reports.stats.scope}</p><p>Algorithm: {reports.stats.algorithm} · Scientific validation: not assessed</p>
      <button onClick={()=>download(JSON.stringify(reports.checks,null,2)+'\n',`data-checks-${runId}.json`)}>Download data checks JSON</button>
      <button onClick={()=>download(JSON.stringify(reports.stats,null,2)+'\n',`statistics-${runId}.json`)}>Download statistics and references JSON</button>
      {reports.stats.datasets.length===0&&<p>No datasets to calculate.</p>}
      {reports.checks.datasets.map(dataset=><div key={dataset.dataset_id}><p>{dataset.title}: {dataset.sample_count} user-declared samples</p><p>Missing metadata: {dataset.missing_metadata.join(', ')||'None declared missing (unverified)'}</p></div>)}
      {reports.stats.datasets.map(dataset=><article key={dataset.dataset_id}><h4>{dataset.title}</h4><p>Source dataset: {dataset.dataset_id}</p>
        {dataset.columns.map(column=><details key={column.name} open><summary>{column.name} ({column.unit??'unit unknown'})</summary>
          <p>Observed: {column.observed_count} · Missing: {column.missing_count}</p>
          <dl><dt>Mean</dt><dd>{column.mean??'Unavailable'}</dd><dt>Minimum</dt><dd>{column.minimum??'Unavailable'}</dd><dt>Maximum</dt><dd>{column.maximum??'Unavailable'}</dd><dt>Sample standard deviation (n−1)</dt><dd>{column.sample_standard_deviation??'Unavailable'}</dd></dl>
          {column.warnings.map(warning=><p key={warning}>{warning}</p>)}
          <details><summary>Input references ({column.references.length})</summary><p>Dataset {dataset.dataset_id}; each item identifies sample / column and the decimal value used. Showing up to 100 references; download statistics JSON for the complete list.</p><ul>{column.references.slice(0,100).map(ref=><li key={ref.sample_id}>{ref.sample_id} / {ref.column}: {ref.value}</li>)}</ul></details>
        </details>)}
      </article>)}
    </>}
  </div>;
}

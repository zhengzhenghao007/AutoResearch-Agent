import {useEffect, useRef, useState} from 'react';
import {researchApi} from '@/lib/research-api';

type Props = {runId:string; source:string; page:number; canAttach:boolean};

export default function OriginalPdf({runId, source, page, canAttach}: Props) {
  const [url, setUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [missing, setMissing] = useState(false);
  const [error, setError] = useState('');
  const active = useRef(true);
  const objectUrl = useRef('');
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    };
  }, []);
  async function load(file?:File) {
    setBusy(true);
    setError('');
    try {
      if (file) await researchApi.attachOriginalPdf(runId, source, file);
      const blob = await researchApi.originalPdf(runId, source);
      if (!active.current) return;
      objectUrl.current = URL.createObjectURL(blob);
      setUrl(objectUrl.current);
      setMissing(false);
    } catch (failure) {
      if (!active.current) return;
      if (!file && failure instanceof Error && 'status' in failure && failure.status === 404) setMissing(true);
      else setError(failure instanceof Error ? failure.message : 'Could not open the original PDF.');
    } finally {
      if (active.current) setBusy(false);
    }
  }
  const atPage = url + '#page=' + page;
  return <section aria-label="Original PDF">
    {url ? <><a href={atPage} target="_blank" rel="noopener noreferrer">Open original PDF at page {page}</a>
      <object data={atPage} type="application/pdf" aria-label={`Original PDF page ${page}`} width="100%" height="480">
        <a href={atPage} target="_blank" rel="noopener noreferrer">View PDF in another tab</a>
      </object></> : <button disabled={busy} onClick={() => void load()}>{busy ? 'Opening PDF…' : 'View original PDF'}</button>}
    {missing && <p>This record has no saved original. {canAttach && 'Choose the same PDF to restore its page view.'}</p>}
    {missing && canAttach && <label>Attach original PDF<input type="file" accept="application/pdf,.pdf" disabled={busy}
      onChange={event => {const file=event.target.files?.[0];event.target.value='';if(file)void load(file);}}/></label>}
    {error && <p role="alert">{error}</p>}
  </section>;
}

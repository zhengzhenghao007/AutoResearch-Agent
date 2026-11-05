import {useState} from 'react';
import type {Category, PaperEvidence} from '@/types/research';

const topics: [Category, string][] = [
  ['problem', 'Research question'], ['method', 'Method'], ['experiment', 'Experiments'],
  ['result', 'Reported results'], ['limitation', 'Limitations'], ['future_work', 'Future work'],
];

export default function LocalPaperOutline({paper, onPage}: {
  paper: PaperEvidence;
  onPage: (page: number, quote: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return <details className="local-outline" onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>Read key passages offline</summary>
    {open && <OutlineContents paper={paper} onPage={onPage}/>}
  </details>;
}

function OutlineContents({paper, onPage}: {paper: PaperEvidence; onPage: (page: number, quote: string) => void}) {
  const evidence = new Map(paper.evidence.map(item => [item.id, item]));
  const passages = topics.flatMap(([category, label]) => {
    const candidates = paper.claims.filter(claim => claim.category === category && claim.claim_type === 'paper_report')
      .flatMap(claim => claim.evidence_ids).map(id => evidence.get(id))
      .filter((item): item is NonNullable<typeof item> => item !== undefined && item.source_id === paper.document.source.id);
    // Prefer a short complete extract over long blocks produced by OCR or column merging.
    const item = candidates.find(item => item.quote.length <= 400) ?? candidates[0];
    return item ? [{label, item}] : [];
  });
  if (!passages.length) return <p>No categorized passages were extracted. Browse the source pages below.</p>;
  return <><p className="research-meta">Selected from this paper’s saved extracts. Categories are automatic. Open a page to check the surrounding text.</p>
    <dl>{passages.map(({label, item}) => <div key={label}><dt>{label}</dt><dd>
      <p>{item.quote.length > 400 ? `${item.quote.slice(0, 400)}…` : item.quote}</p>
      <button onClick={() => onPage(item.page, item.quote)}>Open page {item.page}</button>
    </dd></div>)}</dl></>;
}

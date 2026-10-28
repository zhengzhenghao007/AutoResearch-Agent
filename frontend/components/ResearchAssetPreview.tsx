'use client';
import type {ResearchAsset} from '@/types/manuscript-draft';
export default function ResearchAssetPreview({asset}:{asset:ResearchAsset}) {
 return <figure className="writing-asset">
  {asset.svg?
   // Server-generated SVG stays isolated in an image; never inject markup into the document.
   // eslint-disable-next-line @next/next/no-img-element
   <img src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(asset.svg)}`} alt={asset.title}/>
   :<div className="writing-table-scroll" tabIndex={0} role="region" aria-label={asset.title}><table><thead><tr>{asset.headers.map((h,i)=><th key={i}>{h}</th>)}</tr></thead><tbody>{asset.rows.slice(0,50).map((row,i)=><tr key={i}>{row.map((value,j)=><td key={j}>{value===null?'Missing':String(value)}</td>)}</tr>)}</tbody></table></div>}
  <figcaption>{asset.title}{!asset.svg&&asset.rows.length>50?` · Showing 50 of ${asset.rows.length} rows; export contains the full table.`:''}</figcaption>
  {asset.warnings.map((warning,i)=><p key={i} className="research-meta">{warning}</p>)}
 </figure>;
}

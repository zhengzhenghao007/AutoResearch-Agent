export type SearchProvider='arxiv'|'crossref'|'openalex'|'semantic_scholar';
export interface MetadataHit {source:SearchProvider;source_id:string;title:string;authors:string[];doi:string|null;doi_status:string;url:string;pdf_url:string;year:number|null;rank:number}
export interface SearchBatch {id:string;run_id:string;created_at:string;request:{query:string;sources:SearchProvider[];limit:number};sources:{source:SearchProvider;status:string;started_at:string;finished_at:string;error:string|null;hits:MetadataHit[]}[];groups:{key:string;records:MetadataHit[]}[];scope:string}

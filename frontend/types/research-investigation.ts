import type {Evidence} from './research';
export interface InvestigationReport {
 source_titles:Record<string,string>;
 input_sha256:string; goal:string; source_ids:string[]; total_candidates:number; limitations:string[];
 candidates:{claim_id:string;source_id:string;title:string;quotation:Evidence;related_passages:Evidence[];question:string;novelty:string}[];
}

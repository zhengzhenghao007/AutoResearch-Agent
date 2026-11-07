export interface ReasoningReport {
 matrix:{source_id:string;research_question:string;method:string;results:string;limitations:string;evidence_ids:string[];uncertainty:string}[];
 hypotheses:{kind:'hypothesis';text:string;evidence_ids:string[];validation_experiment:string;uncertainty:string}[];
 review:{theme:string;text:string;kind:'author_claim'|'synthesis';evidence_ids:string[];uncertainty:string}[];
 uncertainties:string[];
}
export interface ReasoningRecord {
 id:string;run_id:string;question:string;status:'reserved'|'completed'|'failed'|'stale';current:boolean;created_at:string;snapshot_sha256:string;
 coverage?:{selected:number;available:number;selected_sources:number;available_sources:number};
 report:ReasoningReport|null;error:string|null;
 usage:{input_tokens:number|null;output_tokens:number|null;total_tokens:number|null;cost_usd:number|null};
}

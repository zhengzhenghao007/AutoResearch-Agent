import type {Claim,Source,Evidence,Page} from './research';
export interface SemanticReviewReport {
  schema_version:1;run_id:string;input_sha256:string;
  input_claims:{claim:Claim;source:Source;evidence:Evidence[];pages:Page[]}[];
  omitted_claim_count:number;model:string;generated_at:string;
  output:{claims:{claim_id:string;verdict:'supported'|'unsupported'|'uncertain';evidence_ids:string[];rationale:string}[];
    contradictions:{claim_ids:string[];rationale:string}[]};
  scientific_validation:'not_assessed';scope:string;
}

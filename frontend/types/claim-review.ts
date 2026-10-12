import type {Category, Evidence} from './research';
export interface ClaimReviewData {
  schema_version: 1;
  rule_version: 'planning-language-en-v1';
  run_id: string;
  claim_count: number;
  checked_claim_count: number;
  flagged_claim_count: number;
  flags: {code:'planning_language_in_observation'; claim_id:string; source_id:string;
    category:Category; claim_text:string; matched_text:string; evidence:Evidence[]; message:string}[];
  semantic_validation: 'not_assessed';
  scope: string;
}

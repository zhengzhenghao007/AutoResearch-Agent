import type {ManuscriptDraftData} from './manuscript-draft';
export type SentenceKind='paper_report'|'user_observation'|'hypothesis'|'suggestion'|'placeholder'|'research_asset';
export interface ManuscriptSentence {id:string;text:string;kind:SentenceKind;reference_ids:string[]}
export interface ManuscriptSection {id:string;title:string;sentences:ManuscriptSentence[]}
export interface ManuscriptRevision {id:string;number:number;created_at:string;reason:string;content_sha256:string;input_sha256:string;sections:ManuscriptSection[];source:ManuscriptDraftData}
export interface ManuscriptReview {id:string;revision_id:string;content_sha256:string;input_sha256:string;model:string;created_at:string;findings:{sentence_id:string;status:'supported'|'unsupported'|'uncertain';rationale:string}[];contradictions:{sentence_ids:[string,string];rationale:string}[];scientific_validation:'not_assessed'}
export interface ManuscriptApproval {review_count:number;revision_id:string;content_sha256:string;input_sha256:string;reviewer:string;note:string;created_at:string}
export interface ManuscriptState {run_id:string;current_input_sha256:string;revisions:ManuscriptRevision[];reviews:ManuscriptReview[];approvals:ManuscriptApproval[]}
export interface ManuscriptRevisionRequest {expected_revision:string|null;expected_input_sha256:string;reason:string;sections:ManuscriptSection[]|null}
export interface ManuscriptExport {filename:string;markdown:string;revision_id:string;content_sha256:string}

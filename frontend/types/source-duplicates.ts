export interface DuplicateMember {entity_type:'candidate'|'processed_source';entity_id:string;title:string;uri:string}
export interface DuplicateGroup {kind:'exact_arxiv_identifier'|'same_pdf_bytes'|'shared_user_supplied_doi';identity_value:string;identity_status:'explicit_identifier'|'exact_content_hash'|'user_supplied_unverified';members:DuplicateMember[]}
export interface SourceDuplicateReport {schema_version:1;run_id:string;groups:DuplicateGroup[];candidate_source_links:{candidate_id:string;source_id:string;arxiv_identifier:string}[]}

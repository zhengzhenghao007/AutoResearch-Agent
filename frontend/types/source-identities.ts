export interface IdentitySourceSnapshot { id:string; sha256:string; uri:string; title:string }
export type SourceIdentityRequest = {source_id:string; reason:string} & ({action:'set';doi:string}|{action:'clear';doi?:null});
export interface SourceIdentityAnnotation {source_id:string;action:'set'|'clear';doi:string|null;reason:string;source:IdentitySourceSnapshot;provenance:'user_supplied';recorded_at:string}
export interface CurrentSourceIdentity {source:IdentitySourceSnapshot;active:boolean;doi:string|null;provenance:'user_supplied'|null}
export interface SourceIdentitiesView {run_id:string;sources:CurrentSourceIdentity[];conflicts:{doi:string;source_ids:string[]}[]}

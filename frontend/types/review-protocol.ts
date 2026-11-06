export interface ProtocolFields {question:string;inclusion_criteria:string;exclusion_criteria:string;publication_range:string;search_strategy:string}
export interface ReviewProtocol extends ProtocolFields {revision:number;saved_at:string}
export interface ProtocolState {run_id:string;revisions:ReviewProtocol[]}

import type {Candidate, CandidateDecision} from './research';
export interface ScreeningReportData {
  schema_version: 1;
  run_id: string;
  topic: string;
  counts: {total:number; include:number; exclude:number; undecided:number; selected:number};
  items: {candidate:Candidate; status:'include'|'exclude'|'undecided'; selected_for_analysis:boolean;
    latest:CandidateDecision|null; history:CandidateDecision[];
    selection_notice:'excluded_but_selected'|'included_but_not_selected'|'selected_without_decision'|null}[];
  scope: string;
}

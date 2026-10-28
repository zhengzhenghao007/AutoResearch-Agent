import type {Source,Evidence} from './research';
import type {ExperimentStatistics} from './experiments';
type StatisticsColumn=ExperimentStatistics['datasets'][number]['columns'][number];
export interface ResearchAsset {item_id:string;title:string;headers:string[];rows:(string|number|null)[][];svg:string|null;markdown:string;warnings:string[];dataset_sha256:string|null}
export interface DraftBlock {id:string;kind:'paper_claim'|'user_statistics'|'placeholder'|'research_asset';text:string;asset?:ResearchAsset|null;paper:{claim_id:string;source:Source;evidence:Evidence[];parsed_pages:number;total_pages:number;truncated:boolean}|null;computation:{dataset_id:string;sha256:string;title:string;algorithm:'descriptive-v1';column:StatisticsColumn}|null}
export interface ManuscriptDraftData {schema_version:1;builder:'evidence-draft-v1';run_id:string;topic:string;input_sha256:string;sections:{id:string;title:string;purpose:string;blocks:DraftBlock[]}[];omitted_legacy_observation_claims:number;scientific_validation:'not_assessed';contradiction_review:'not_assessed';approval:'not_requested';statistics_scope:string;scope:string}

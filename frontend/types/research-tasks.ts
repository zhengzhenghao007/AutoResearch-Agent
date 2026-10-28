export interface TaskBudget {max_steps:number;max_seconds:number;max_evidence:number}
export interface ResearchTask {
 id:string;run_id:string;question:string;source_sha256:string;created_at:string;updated_at:string;
 status:'ready'|'running'|'paused'|'completed'|'incomplete'|'cancelled'|'budget_exhausted'|'stale'|'failed';
 stop_reason:string|null;budget:TaskBudget;
 usage:{steps:number;seconds:number;evidence:number;input_tokens:number;output_tokens:number;cost_usd:number};
 subquestions:{id:string;question:string;requirements:string[]}[];
 steps:{id:string;question_id:string;title:string;tool:string;depends_on:string[];status:'pending'|'running'|'completed'|'failed';attempts:number;input_sha256:string;result:{evidence_ids:string[];gaps:string[];summary:string}|null}[];
 events:{at:string;type:string;message:string}[];
}
export interface CreateResearchTask {question:string;subquestions:string[];budget:TaskBudget}

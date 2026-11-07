import type {AcquiredPaper,AcquisitionSelection} from '@/types/metadata-search';
import type {ReasoningRecord} from '@/types/research-reasoning';
import type {ProtocolState,ProtocolFields,ReviewProtocol} from '@/types/review-protocol';
import type {LiteraturePacket} from '@/types/literature-packet';
import type {SearchBatch,SearchProvider} from '@/types/metadata-search';
import type {InvestigationReport} from '@/types/research-investigation';
import type {ManuscriptState,ManuscriptRevisionRequest,ManuscriptExport} from '@/types/manuscript';
import type {PaperQuickRead} from '@/types/paper-quick-read';
import type {SemanticReviewReport} from '@/types/semantic-review';
import type {ManuscriptDraftData} from '@/types/manuscript-draft';
import type {CsvMetadata,ExperimentReport,ExperimentStatistics} from '@/types/experiments';
import type {Claim,Category} from '@/types/research';
import type {ClaimReviewData} from '@/types/claim-review';
import type {ScreeningReportData} from '@/types/screening-report';
import type {SourceDuplicateReport} from '@/types/source-duplicates';
import type {SourceIdentitiesView,SourceIdentityRequest} from '@/types/source-identities';
import type { CandidateDecision, ResearchHistory, ResearchRun } from '@/types/research';
import type { CitationRegistry, BibtexExport } from '@/types/citations';
import type {WorkspaceItemRequest,WorkspacePreview} from '@/types/workspace';
import type {ResearchTask,CreateResearchTask,TaskBudget} from '@/types/research-tasks';
const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
export const REQUEST_TIMEOUT_MS = 120_000;
export class ResearchApiError extends Error {
  constructor(message:string, public status:number) { super(message); }
}
let accessToken = '';
export function setResearchToken(token: string) { accessToken = token; }
export interface ResearchSession { mode:'local'|'deployment'; user_id:string; role:'reader'|'writer'; jobs_enabled:boolean }
export interface ResearchJob { id:string; kind:'search'|'analyze'; status:string; attempt:number; run_id:string|null; error:string|null; progress:string }
export type JobRequest = {kind:'search';topic:string;run_id?:string}|{kind:'analyze';run_id:string;selected_ids:string[]};

function detailText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(detailText).join('; ');
  if (value && typeof value === 'object') {
    const entry = value as { loc?: unknown[]; msg?: string; detail?: unknown };
    if (entry.msg) return `${entry.loc?.join('.') ? entry.loc.join('.') + ': ' : ''}${entry.msg}`;
    if (entry.detail) return detailText(entry.detail);
  }
  return '';
}

async function request<T>(path: string, init?: RequestInit, binary = false, timeoutMs = REQUEST_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const headers = new Headers(init?.headers);
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
    const response = await fetch(`${base}/api/research${path}`, { ...init, headers, signal: controller.signal, cache: 'no-store' });
    if (!response.ok) {
      let message = '';
      try { message = detailText(await response.json()); } catch { /* Fall back to HTTP status. */ }
      throw new ResearchApiError(message || `Request failed (${response.status}).`, response.status);
    }
    return await (binary ? response.blob() : response.json()) as T;
  } catch (error) {
    if (timedOut) throw new Error('Request timed out. The server may still be processing this operation. Refresh history and reopen the record to check its state before starting another operation.');
    if (error instanceof TypeError) throw new Error('Connection lost. The operation may still be running on the server. Refresh history and reopen the record to check its state.');
    throw error;
  } finally { clearTimeout(timer); }
}
const json = (body: unknown): RequestInit => ({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export type EditingProfile = 'minimal'|'standard';
export type EditingPolicy = {enabled:true;profile:EditingProfile;editable:boolean};
export const researchApi = {
  editingPolicy:()=>request<EditingPolicy>('/settings/academic-humanizer'),
  updateEditingPolicy:(profile:EditingProfile)=>request<EditingPolicy>('/settings/academic-humanizer',{...json({profile}),method:'PUT'}),
 acquisitionHistory:(id:string)=>request<AcquiredPaper[]>(`/runs/${encodeURIComponent(id)}/paper-acquisitions`),
 acquirePapers:(id:string,selections:AcquisitionSelection[])=>request<AcquiredPaper[]>(`/runs/${encodeURIComponent(id)}/paper-acquisitions`,json({selections})),
 importAcquired:(id:string,item:string)=>request<ResearchRun>(`/runs/${encodeURIComponent(id)}/paper-acquisitions/${encodeURIComponent(item)}/import`,json({})),
 reasoningHistory:(id:string)=>request<{items:ReasoningRecord[]}>(`/runs/${encodeURIComponent(id)}/reasoning`),
 generateReasoning:(id:string,body:{question:string;allow_model:boolean;max_output_tokens:number})=>request<ReasoningRecord>(`/runs/${encodeURIComponent(id)}/reasoning`,json(body)),
 researchSkills:(id:string)=>request<{items:{id:string;version:number;description:string;permissions:string[]}[]}>(`/runs/${encodeURIComponent(id)}/tasks/skills`),
 reviewProtocol:(id:string)=>request<ProtocolState>(`/runs/${encodeURIComponent(id)}/review-protocol`),
 saveReviewProtocol:(id:string,fields:ProtocolFields,revision:number)=>request<ReviewProtocol>(`/runs/${encodeURIComponent(id)}/review-protocol`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...fields,expected_revision:revision})}),
 literaturePacket:(id:string,sourceIds:string[])=>request<LiteraturePacket>(`/runs/${encodeURIComponent(id)}/literature-packet`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_ids:sourceIds})}),
 metadataHistory:(id:string)=>request<{items:SearchBatch[]}>(`/runs/${encodeURIComponent(id)}/metadata-search`),
 metadataSearch:(id:string,query:string,sources:SearchProvider[])=>request<SearchBatch>(`/runs/${encodeURIComponent(id)}/metadata-search`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query,sources,limit:5})}),
 investigation: (id:string, sourceIds:string[]) => request<InvestigationReport>(`/runs/${encodeURIComponent(id)}/investigation`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_ids:sourceIds})}),
  originalPdf:(id:string,source:string)=>request<Blob>(`/runs/${encodeURIComponent(id)}/papers/${encodeURIComponent(source)}/original`,undefined,true),
  attachOriginalPdf:(id:string,source:string,file:File)=>{
    const body=new FormData();
    body.append('file',file);
    return request<{saved:boolean}>(`/runs/${encodeURIComponent(id)}/papers/${encodeURIComponent(source)}/original`,{method:'POST',body});
  },
  quickRead:(id:string,sourceId:string)=>request<PaperQuickRead|null>(`/runs/${encodeURIComponent(id)}/papers/${encodeURIComponent(sourceId)}/quick-read`),
  generateQuickRead:(id:string,sourceId:string)=>request<PaperQuickRead>(`/runs/${encodeURIComponent(id)}/papers/${encodeURIComponent(sourceId)}/quick-read`,json({allow_model:true})),
  updateProject:(id:string,body:{project_name:string;research_goal:string;expected_project_name:string|null;expected_research_goal:string|null})=>request<ResearchRun>(`/runs/${encodeURIComponent(id)}/project`,json(body)),
  researchTaskReport:(id:string,taskId:string,format:'json'|'markdown')=>request<Blob>(`/runs/${encodeURIComponent(id)}/tasks/${encodeURIComponent(taskId)}/report?format=${format}`,undefined,true),
  researchTasks:(id:string)=>request<{items:ResearchTask[]}>(`/runs/${encodeURIComponent(id)}/tasks`),
  createResearchTask:(id:string,body:CreateResearchTask)=>request<ResearchTask>(`/runs/${encodeURIComponent(id)}/tasks`,json(body)),
  researchTask:(id:string,taskId:string)=>request<ResearchTask>(`/runs/${encodeURIComponent(id)}/tasks/${encodeURIComponent(taskId)}`),
  nextResearchTask:(id:string,taskId:string)=>request<ResearchTask>(`/runs/${encodeURIComponent(id)}/tasks/${encodeURIComponent(taskId)}/next`,json({})),
  cancelResearchTask:(id:string,taskId:string)=>request<ResearchTask>(`/runs/${encodeURIComponent(id)}/tasks/${encodeURIComponent(taskId)}/cancel`,json({})),
  increaseResearchTaskBudget:(id:string,taskId:string,body:TaskBudget)=>request<ResearchTask>(`/runs/${encodeURIComponent(id)}/tasks/${encodeURIComponent(taskId)}/budget`,json(body)),
  saveWorkspaceItem: (id:string,body:WorkspaceItemRequest) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}/workspace/items`,json(body)),
  previewWorkspaceItem: (id:string,body:WorkspaceItemRequest) => request<WorkspacePreview>(`/runs/${encodeURIComponent(id)}/workspace/preview`,json(body)),
  workspaceItem: (id:string,itemId:string) => request<WorkspacePreview>(`/runs/${encodeURIComponent(id)}/workspace/items/${encodeURIComponent(itemId)}`),
  manuscriptBundle: (id:string,revisionId:string) => request<Blob>(`/runs/${encodeURIComponent(id)}/manuscript/bundle?revision_id=${encodeURIComponent(revisionId)}`,undefined,true),
  session: () => request<ResearchSession>('/session'),
  jobs: () => request<{items:ResearchJob[]}>('/jobs'),
  submitJob: (body:JobRequest) => request<ResearchJob>('/jobs',json(body)),
  cancelJob: (id:string) => request<ResearchJob>(`/jobs/${encodeURIComponent(id)}/cancel`,json({})),
  retryJob: (id:string) => request<ResearchJob>(`/jobs/${encodeURIComponent(id)}/retry`,json({})),
  deleteJob: (id:string) => request<{removed:string}>(`/jobs/${encodeURIComponent(id)}`,{method:'DELETE'}),
  manuscript: (id:string) => request<ManuscriptState>(`/runs/${encodeURIComponent(id)}/manuscript`),
  saveManuscript: (id:string,body:ManuscriptRevisionRequest) => request<ManuscriptState>(`/runs/${encodeURIComponent(id)}/manuscript/revisions`,json(body)),
  reviewManuscript: (id:string,revision_id:string) => request<ManuscriptState>(`/runs/${encodeURIComponent(id)}/manuscript/review`,json({revision_id,allow_model:true})),
  approveManuscript: (id:string,revision_id:string,reviewer:string,note:string,expected_review_count:number) => request<ManuscriptState>(`/runs/${encodeURIComponent(id)}/manuscript/approval`,json({revision_id,reviewer,note,expected_review_count,confirm:true})),
  exportManuscript: (id:string,revision_id:string) => request<ManuscriptExport>(`/runs/${encodeURIComponent(id)}/manuscript/export?revision_id=${encodeURIComponent(revision_id)}`),
  manuscriptDraft: (id:string) => request<ManuscriptDraftData>(`/runs/${encodeURIComponent(id)}/manuscript-draft`),
  create: (topic = '', project_name?:string, research_goal?:string) => request<ResearchRun>('/runs',json({topic,project_name,research_goal})),
  experiments: (id:string) => request<ExperimentReport>(`/runs/${encodeURIComponent(id)}/experiments`),
  experimentStatistics: (id:string) => request<ExperimentStatistics>(`/runs/${encodeURIComponent(id)}/experiment-statistics`),
  importExperiment: (id:string,file:File,format:'json'|'csv',metadata?:CsvMetadata) => {
    const body=new FormData();body.append('file',file);
    if(format==='csv')body.append('metadata',JSON.stringify(metadata));
    return request<ResearchRun>(`/runs/${encodeURIComponent(id)}/experiments${format==='csv'?'/csv':''}`,{method:'POST',body});
  },
  semanticReview: (id:string,claim_ids:string[]) => request<SemanticReviewReport>(`/runs/${encodeURIComponent(id)}/semantic-review`,json({claim_ids,allow_model:true})),
  reviseCategory: (id:string,expected_claim:Claim,category:Category,reason:string) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}/category-revisions`,json({expected_claim,category,reason})),
  claimReview: (id: string) => request<ClaimReviewData>(`/runs/${encodeURIComponent(id)}/claim-review`),
  screeningReport: (id: string) => request<ScreeningReportData>(`/runs/${encodeURIComponent(id)}/screening-report`),
  sourceDuplicates: (id: string) => request<SourceDuplicateReport>(`/runs/${encodeURIComponent(id)}/source-duplicates`),
  sourceIdentities: (id: string) => request<SourceIdentitiesView>(`/runs/${encodeURIComponent(id)}/source-identities`),
  sourceIdentity: (id: string, body: SourceIdentityRequest) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}/source-identities`,json(body)),
  candidateDecision: (id: string, body: Omit<CandidateDecision, "decided_at">) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}/candidate-decisions`, json(body)),
  citations: (id: string) => request<CitationRegistry>(`/runs/${encodeURIComponent(id)}/citations`),
  bibtex: (id: string) => request<BibtexExport>(`/runs/${encodeURIComponent(id)}/bibtex`),
  list: (page = 1) => request<ResearchHistory>(`/runs?page=${page}&page_size=10`),
  get: (id: string) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}`),
  search: (topic: string, run_id?:string) => request<ResearchRun>('/search', json({topic,max_results:5,run_id})),
  analyze: (id: string, selected: string[]) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}/analyze`,json({selected_ids:selected})),
  upload: (file: File, runId?: string) => { const body=new FormData(); body.append('file',file); if(runId) body.append('run_id',runId); return request<ResearchRun>('/upload',{method:'POST',body},false,720_000); },
};

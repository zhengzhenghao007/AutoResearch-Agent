import type {SemanticReviewReport} from '@/types/semantic-review';
import type {CsvMetadata,ExperimentReport,ExperimentStatistics} from '@/types/experiments';
import type {Claim,Category} from '@/types/research';
import type {ClaimReviewData} from '@/types/claim-review';
import type {ScreeningReportData} from '@/types/screening-report';
import type {SourceDuplicateReport} from '@/types/source-duplicates';
import type {SourceIdentitiesView,SourceIdentityRequest} from '@/types/source-identities';
import type { CandidateDecision, ResearchHistory, ResearchRun } from '@/types/research';
import type { CitationRegistry, BibtexExport } from '@/types/citations';
const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
export const REQUEST_TIMEOUT_MS = 120_000;

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${base}/api/research${path}`, { ...init, signal: controller.signal, cache: 'no-store' });
    if (!response.ok) {
      let message = '';
      try { message = detailText(await response.json()); } catch { /* Fall back to HTTP status. */ }
      throw new Error(message || `Request failed (${response.status}).`);
    }
    return await response.json() as T;
  } catch (error) {
    if (timedOut) throw new Error('Request timed out. The server may still be processing this operation. Refresh history and reopen the record to check its state before starting another operation.');
    if (error instanceof TypeError) throw new Error('Connection lost. The operation may still be running on the server. Refresh history and reopen the record to check its state.');
    throw error;
  } finally { clearTimeout(timer); }
}
const json = (body: unknown): RequestInit => ({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export const researchApi = {
  create: (topic:string) => request<ResearchRun>('/runs',json({topic})),
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
  search: (topic: string) => request<ResearchRun>('/search', json({topic,max_results:5})),
  analyze: (id: string, selected: string[]) => request<ResearchRun>(`/runs/${encodeURIComponent(id)}/analyze`,json({selected_ids:selected})),
  upload: (file: File, runId?: string) => { const body=new FormData(); body.append('file',file); if(runId) body.append('run_id',runId); return request<ResearchRun>('/upload',{method:'POST',body}); },
};

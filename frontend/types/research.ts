/** Mirrors schemas/research.py, schema version 1. */
export type Category = 'problem' | 'method' | 'dataset' | 'experiment' | 'result' | 'limitation' | 'future_work';
export interface Source { id: string; title: string; kind: 'paper' | 'user_data'; uri: string; sha256: string; collected_at: string }
export interface Page { number: number; text: string }
export interface Document { source: Source; pages: Page[]; total_pages: number; truncated: boolean }
export interface Evidence { id: string; source_id: string; page: number; quote: string }
export interface Claim { id: string; text: string; category: Category; claim_type: 'paper_report' | 'user_observation' | 'synthesis' | 'hypothesis' | 'suggestion'; evidence_ids: string[]; created_by: string; timestamp: string }
export interface PaperEvidence { document: Document; evidence: Evidence[]; claims: Claim[]; missing_fields: Category[]; extractor: string }
export interface Review { approved: boolean; issues: string[]; scope: string }
export interface Candidate { id: string; title: string; pdf_url: string; summary: string; authors: string[] }
export interface Artifact { kind: 'literature_summary' | 'method_comparison' | 'research_ideas' | 'coverage_gaps'; title: string; content: string; claim_ids: string[]; evidence_ids: string[] }
export interface ResearchRun { schema_version: 1; id: string; topic: string; plan: string[]; candidates: Candidate[]; selected_ids: string[]; papers: PaperEvidence[]; generated_claims: Claim[]; artifacts: Artifact[]; review: Review }
export interface ResearchRunSummary { id: string; topic: string; candidate_count: number; selected_count: number; paper_count: number; updated_at: string; source_support_passed: boolean }
export interface ResearchHistory { items: ResearchRunSummary[]; total: number; page: number; page_size: number }

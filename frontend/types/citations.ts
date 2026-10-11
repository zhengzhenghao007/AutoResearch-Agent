import type { Category, Claim } from './research';
export interface CitationRegistry {
  schema_version: 1;
  run_id: string;
  topic: string;
  sources: {
    source_id: string; sha256: string; title: string; kind: 'paper' | 'user_data';
    uri: string; arxiv_revision_id: string | null;
    evidence: { id: string; page: number; quote: string }[];
    claims: { id: string; text: string; category: Category; claim_type: Claim['claim_type']; evidence_ids: string[] }[];
  }[];
}
export interface BibtexExport {
  run_id: string;
  bibtex: string;
  skipped_sources: { source_id: string; reason: 'missing_bibliographic_identity' }[];
}

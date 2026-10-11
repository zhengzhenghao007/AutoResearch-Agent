export interface Paper {
  title: string;
  authors: string[];
  summary: string;
  published: string;
  pdf_url: string;
  entry_id: string;
}

export interface PaperSearchResponse {
  topic: string;
  plan: unknown;
  papers: Paper[];
  total: number;
}

export interface PaperAnalysis {
  research_problem?: unknown;
  methodology?: unknown;
  datasets?: unknown;
  main_contributions?: unknown;
  limitations?: unknown;
  model_name?: unknown;
  elapsed_seconds?: unknown;
  estimated_cost_usd?: unknown;
}

export interface PaperReview {
  approved?: unknown;
  score?: unknown;
  feedback?: unknown;
  warnings?: unknown;
  issues?: unknown;
}

export interface PaperAnalysisResponse {
  topic: string;
  paper: Paper;
  pdf_path: string | null;
  extracted_text_length: number;
  extracted_text_preview: string;
  analysis: PaperAnalysis | null;
  review: PaperReview | null;
  reader_pipeline: unknown;
  used_fallback: boolean;
  pipeline_error: string | null;
}
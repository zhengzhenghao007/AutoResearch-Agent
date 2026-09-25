import type {
  Paper,
  PaperAnalysisResponse,
  PaperSearchResponse,
} from "@/types/paper";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

interface SearchPapersInput {
  topic: string;
  maxResults?: number;
}

interface AnalyzePaperInput {
  paper: Paper;
  topic: string;
  plan?: unknown;
  maxPages?: number;
  readerMode?: "auto" | "llm" | "rule";
  maxReaderRetries?: number;
}

async function parseApiError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as {
      detail?: string;
    };

    return data.detail ?? `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

export async function searchPapers({
  topic,
  maxResults = 5,
}: SearchPapersInput): Promise<PaperSearchResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/papers/search`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic,
        max_results: maxResults,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  return response.json() as Promise<PaperSearchResponse>;
}

export async function analyzePaper({
  paper,
  topic,
  plan = null,
  maxPages = 5,
  readerMode = "auto",
  maxReaderRetries = 2,
}: AnalyzePaperInput): Promise<PaperAnalysisResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/papers/analyze`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        paper,
        topic,
        plan,
        max_pages: maxPages,
        reader_mode: readerMode,
        max_reader_retries: maxReaderRetries,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  return response.json() as Promise<PaperAnalysisResponse>;
}

"use client";

import { FormEvent, useState } from "react";
import EvidenceWorkspace from "@/components/EvidenceWorkspace";

import {
  analyzePaper,
  searchPapers,
} from "@/lib/api";
import type {
  Paper,
  PaperAnalysisResponse,
  PaperSearchResponse,
} from "@/types/paper";

const DEFAULT_TOPIC =
  "vision language robot navigation";


function valueToText(
  value: unknown,
  fallback = "Not available",
): string {
  if (value === null || value === undefined) {
    return fallback;
  }

  if (typeof value === "string") {
    const cleanedValue = value.trim();

    return cleanedValue || fallback;
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return fallback;
    }

    return value
      .map((item) => valueToText(item, ""))
      .filter(Boolean)
      .join(", ");
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(
        value,
        null,
        2,
      );
    } catch {
      return String(value);
    }
  }

  return String(value);
}


function valueToList(
  value: unknown,
): string[] {
  if (value === null || value === undefined) {
    return ["Not available"];
  }

  if (Array.isArray(value)) {
    const items = value
      .map((item) => valueToText(item, ""))
      .filter((item) => item.trim().length > 0);

    return items.length > 0
      ? items
      : ["Not available"];
  }

  if (typeof value === "string") {
    const cleanedValue = value.trim();

    if (!cleanedValue) {
      return ["Not available"];
    }

    const lineItems = cleanedValue
      .split(/\r?\n/)
      .map((item) =>
        item
          .replace(
            /^[\s*•\-–—\d.)]+/,
            "",
          )
          .trim(),
      )
      .filter(Boolean);

    if (lineItems.length > 1) {
      return lineItems;
    }

    return [cleanedValue];
  }

  if (typeof value === "object") {
    return Object.entries(
      value as Record<string, unknown>,
    ).map(
      ([key, item]) =>
        `${key}: ${valueToText(item)}`,
    );
  }

  return [String(value)];
}


function formatAuthors(
  authors: string[],
): string {
  if (!Array.isArray(authors)) {
    return "Unknown authors";
  }

  if (authors.length === 0) {
    return "Unknown authors";
  }

  return authors.join(", ");
}


function formatBoolean(
  value: unknown,
): string {
  if (value === true) {
    return "Yes";
  }

  if (value === false) {
    return "No";
  }

  return valueToText(value, "Unknown");
}


function formatNumber(
  value: unknown,
): string {
  if (typeof value === "number") {
    return Number.isInteger(value)
      ? String(value)
      : value.toFixed(2);
  }

  return valueToText(value, "Unknown");
}


export default function Home() {
  const [topic, setTopic] = useState(
    DEFAULT_TOPIC,
  );

  const [
    searchResult,
    setSearchResult,
  ] =
    useState<PaperSearchResponse | null>(
      null,
    );

  const [
    analysisResult,
    setAnalysisResult,
  ] =
    useState<PaperAnalysisResponse | null>(
      null,
    );

  const [searching, setSearching] =
    useState(false);

  const [
    analyzingEntryId,
    setAnalyzingEntryId,
  ] = useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);


  async function handleSearch(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanedTopic = topic.trim();

    if (!cleanedTopic) {
      setError(
        "Please enter a research topic.",
      );
      return;
    }

    setSearching(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await searchPapers({
        topic: cleanedTopic,
        maxResults: 5,
      });

      setSearchResult(result);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Paper search failed.",
      );
    } finally {
      setSearching(false);
    }
  }


  async function handleAnalyze(
    paper: Paper,
  ) {
    if (!searchResult) {
      return;
    }

    const identifier =
      paper.entry_id || paper.title;

    setAnalyzingEntryId(identifier);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await analyzePaper({
        paper,
        topic: searchResult.topic,
        plan: searchResult.plan,
        maxPages: 5,
        readerMode: "auto",
        maxReaderRetries: 2,
      });

      setAnalysisResult(result);

      window.setTimeout(() => {
        document
          .getElementById(
            "analysis-result",
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Paper analysis failed.",
      );
    } finally {
      setAnalyzingEntryId(null);
    }
  }


  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <EvidenceWorkspace />
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              AutoResearch Agent
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              AI powered academic paper search
              and analysis
            </p>
          </div>

          <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
            FastAPI + Next.js
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10">
        <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
              Research workspace
            </p>

            <h2 className="mt-3 text-4xl font-bold tracking-tight">
              Search, read and review
              academic papers
            </h2>

            <p className="mt-4 text-lg leading-8 text-slate-600">
              Search arXiv papers and run
              selected papers through the
              ReaderPipeline and Reviewer
              agents.
            </p>
          </div>

          <form
            onSubmit={handleSearch}
            className="mt-8 flex flex-col gap-3 md:flex-row"
          >
            <input
              value={topic}
              onChange={(event) =>
                setTopic(event.target.value)
              }
              className="min-h-14 flex-1 rounded-2xl border border-slate-300 bg-white px-5 text-base outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
              placeholder="Enter a research topic"
            />

            <button
              type="submit"
              disabled={searching}
              className="min-h-14 rounded-2xl bg-indigo-600 px-8 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300"
            >
              {searching
                ? "Searching..."
                : "Search papers"}
            </button>
          </form>
        </section>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-red-700">
            {error}
          </div>
        )}

        {searchResult && (
          <section className="mt-10">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-sm font-semibold text-indigo-600">
                  Search results
                </p>

                <h2 className="mt-1 text-3xl font-bold">
                  Found{" "}
                  {searchResult.total} papers
                </h2>
              </div>

              <p className="max-w-xl text-sm text-slate-500 md:text-right">
                {searchResult.topic}
              </p>
            </div>

            <div className="mt-6 grid gap-5">
              {searchResult.papers.map(
                (paper, index) => {
                  const paperKey =
                    paper.entry_id ||
                    `${paper.title}-${index}`;

                  const identifier =
                    paper.entry_id ||
                    paper.title;

                  const isAnalyzing =
                    analyzingEntryId ===
                    identifier;

                  return (
                    <article
                      key={paperKey}
                      className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-indigo-200 hover:shadow-md"
                    >
                      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start gap-4">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-bold text-indigo-700">
                              {index + 1}
                            </div>

                            <div>
                              <h3 className="text-xl font-bold leading-7">
                                {paper.title}
                              </h3>

                              <p className="mt-2 text-sm leading-6 text-slate-500">
                                {formatAuthors(
                                  paper.authors,
                                )}
                              </p>

                              <p className="mt-1 text-sm text-slate-500">
                                Published:{" "}
                                {paper.published ||
                                  "Unknown"}
                              </p>
                            </div>
                          </div>

                          <p className="mt-5 line-clamp-4 leading-7 text-slate-600">
                            {paper.summary ||
                              "No abstract available."}
                          </p>
                        </div>

                        <div className="flex shrink-0 gap-3 lg:flex-col">
                          <button
                            type="button"
                            disabled={
                              analyzingEntryId !==
                              null
                            }
                            onClick={() =>
                              handleAnalyze(paper)
                            }
                            className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                          >
                            {isAnalyzing
                              ? "Analyzing..."
                              : "Analyze"}
                          </button>

                          {paper.pdf_url && (
                            <a
                              href={
                                paper.pdf_url
                              }
                              target="_blank"
                              rel="noreferrer"
                              className="rounded-xl border border-slate-300 px-5 py-3 text-center text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700"
                            >
                              Open PDF
                            </a>
                          )}
                        </div>
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          </section>
        )}

        {analysisResult && (
          <section
            id="analysis-result"
            className="mt-12 scroll-mt-8"
          >
            <div className="rounded-3xl bg-slate-950 p-8 text-white">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-300">
                Analysis complete
              </p>

              <h2 className="mt-3 max-w-4xl text-3xl font-bold leading-tight">
                {
                  analysisResult.paper
                    .title
                }
              </h2>

              <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                  label="Approved"
                  value={formatBoolean(
                    analysisResult.review
                      ?.approved,
                  )}
                />

                <MetricCard
                  label="Score"
                  value={formatNumber(
                    analysisResult.review
                      ?.score,
                  )}
                />

                <MetricCard
                  label="Extracted characters"
                  value={String(
                    analysisResult
                      .extracted_text_length,
                  )}
                />

                <MetricCard
                  label="Fallback used"
                  value={
                    analysisResult
                      .used_fallback
                      ? "Yes"
                      : "No"
                  }
                />
              </div>

              {analysisResult
                .pipeline_error && (
                <div className="mt-6 rounded-2xl border border-red-300/30 bg-red-500/10 p-4 text-sm text-red-100">
                  {
                    analysisResult
                      .pipeline_error
                  }
                </div>
              )}
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <ResultCard
                title="Research Problem"
                content={valueToText(
                  analysisResult.analysis
                    ?.research_problem,
                )}
              />

              <ResultCard
                title="Methodology"
                content={valueToText(
                  analysisResult.analysis
                    ?.methodology,
                )}
              />

              <ListResultCard
                title="Datasets"
                items={valueToList(
                  analysisResult.analysis
                    ?.datasets,
                )}
              />

              <ListResultCard
                title="Main Contributions"
                items={valueToList(
                  analysisResult.analysis
                    ?.main_contributions,
                )}
              />

              <ListResultCard
                title="Limitations"
                items={valueToList(
                  analysisResult.analysis
                    ?.limitations,
                )}
              />

              <ResultCard
                title="Reviewer Feedback"
                content={valueToText(
                  analysisResult.review
                    ?.feedback,
                )}
              />

              <ListResultCard
                title="Reviewer Warnings"
                items={valueToList(
                  analysisResult.review
                    ?.warnings,
                )}
              />

              <ListResultCard
                title="Detected Issues"
                items={valueToList(
                  analysisResult.review
                    ?.issues,
                )}
              />
            </div>

            <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-bold">
                Extracted Text Preview
              </h3>

              <p className="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap rounded-2xl bg-slate-50 p-5 text-sm leading-7 text-slate-600">
                {analysisResult
                  .extracted_text_preview ||
                  "Not available"}
              </p>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}


interface MetricCardProps {
  label: string;
  value: string;
}


function MetricCard({
  label,
  value,
}: MetricCardProps) {
  return (
    <div className="rounded-2xl bg-white/10 p-4">
      <p className="text-sm text-slate-300">
        {label}
      </p>

      <p className="mt-1 break-words text-2xl font-bold">
        {value}
      </p>
    </div>
  );
}


interface ResultCardProps {
  title: string;
  content: string;
}


function ResultCard({
  title,
  content,
}: ResultCardProps) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-bold">
        {title}
      </h3>

      <p className="mt-4 whitespace-pre-wrap break-words leading-7 text-slate-600">
        {content}
      </p>
    </article>
  );
}


interface ListResultCardProps {
  title: string;
  items: string[];
}


function ListResultCard({
  title,
  items,
}: ListResultCardProps) {
  const safeItems = Array.isArray(items)
    ? items
    : valueToList(items);

  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-bold">
        {title}
      </h3>

      <ul className="mt-4 space-y-3 text-slate-600">
        {safeItems.map(
          (item, index) => (
            <li
              key={`${item}-${index}`}
              className="flex gap-3 leading-7"
            >
              <span className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />

              <span className="min-w-0 break-words">
                {item}
              </span>
            </li>
          ),
        )}
      </ul>
    </article>
  );
}

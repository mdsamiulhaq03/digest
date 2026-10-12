import "server-only";

import { ApiError } from "@/lib/api";
import { authedJson } from "@/lib/auth";

// Mirrors the API's DocumentResponse (backend/app/schemas/document.py).

export type DocumentStatus = "ready" | "processing" | "failed";

export type TextInsights = {
  char_count: number;
  char_count_no_whitespace: number;
  word_count: number;
  unique_word_count: number;
  sentence_count: number;
  paragraph_count: number;
  average_word_length: number;
  top_words: string[];
  estimated_reading_time_seconds: number;
};

export type ColumnStats = {
  name: string;
  null_count: number;
  inferred_type: string;
  min: number | null;
  max: number | null;
  mean: number | null;
};

export type CsvInsights = {
  row_count: number;
  column_count: number;
  columns: ColumnStats[];
};

export type Document = {
  id: string;
  title: string;
  status: DocumentStatus;
  job_id: string | null;
  text: string | null;
  original_filename: string | null;
  content_type: string | null;
  size_bytes: number | null;
  insights: TextInsights | null;
  csv_insights: CsvInsights | null;
  created_at: string;
};

export async function listDocuments(): Promise<Document[]> {
  const { documents } = await authedJson<{ documents: Document[] }>("/documents");
  return documents;
}

export type JobState = "queued" | "running" | "succeeded" | "failed";

export type Job = {
  id: string;
  document_id: string;
  state: JobState;
  attempts: number;
  last_error: string | null;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
};

// The API answers 404 for a missing id and for someone else's alike, so null
// means "nothing of yours by that id" either way.

export async function getDocument(id: string): Promise<Document | null> {
  return orNullOn404(authedJson<Document>(`/documents/${encodeURIComponent(id)}`));
}

export async function getJob(id: string): Promise<Job | null> {
  return orNullOn404(authedJson<Job>(`/jobs/${encodeURIComponent(id)}`));
}

async function orNullOn404<T>(request: Promise<T>): Promise<T | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

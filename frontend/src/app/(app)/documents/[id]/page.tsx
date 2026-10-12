import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AutoRefresh } from "@/components/auto-refresh";
import {
  documentSource,
  formatDateTime,
  formatNumber,
  formatReadingTime,
} from "@/components/format";
import { StatusBadge } from "@/components/status-badge";
import {
  type CsvInsights,
  type Document,
  getDocument,
  getJob,
  type TextInsights,
} from "@/lib/documents";

const POLL_INTERVAL_MS = 2000;

export default function DocumentPage({ params }: PageProps<"/documents/[id]">) {
  return (
    <Suspense fallback={<p className="text-zinc-500">Loading…</p>}>
      <DocumentView params={params} />
    </Suspense>
  );
}

async function DocumentView({ params }: Pick<PageProps<"/documents/[id]">, "params">) {
  const { id } = await params;
  const document = await getDocument(id);
  if (document === null) {
    notFound();
  }
  return (
    <>
      <Link href="/" className="text-sm underline">
        ← Your documents
      </Link>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="break-words text-2xl font-semibold tracking-tight">{document.title}</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {documentSource(document)} · added {formatDateTime(document.created_at)}
          </p>
        </div>
        <StatusBadge status={document.status} />
      </div>
      <Body document={document} />
    </>
  );
}

async function Body({ document }: { document: Document }) {
  if (document.status === "processing") {
    return (
      <>
        {/* Swaps itself for the insights once the job finishes. */}
        <AutoRefresh intervalMs={POLL_INTERVAL_MS} />
        <Notice>
          This file is still being analysed.{" "}
          {document.job_id && (
            <Link href={`/jobs/${document.job_id}`} className="underline">
              Watch its progress
            </Link>
          )}
        </Notice>
      </>
    );
  }
  if (document.status === "failed") {
    const job = document.job_id ? await getJob(document.job_id) : null;
    return (
      <Notice tone="error">
        This file couldn&apos;t be analysed
        {job?.last_error ? `: ${job.last_error}` : "."}
      </Notice>
    );
  }
  return (
    <>
      {document.insights && <TextInsightsView insights={document.insights} />}
      {document.csv_insights && <CsvInsightsView insights={document.csv_insights} />}
      {document.text !== null && (
        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Text</h2>
          <p className="whitespace-pre-wrap rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800">
            {document.text}
          </p>
        </section>
      )}
    </>
  );
}

function TextInsightsView({ insights }: { insights: TextInsights }) {
  const stats: [string, string][] = [
    ["Words", formatNumber(insights.word_count)],
    ["Unique words", formatNumber(insights.unique_word_count)],
    ["Sentences", formatNumber(insights.sentence_count)],
    ["Paragraphs", formatNumber(insights.paragraph_count)],
    ["Characters", formatNumber(insights.char_count)],
    ["Without spaces", formatNumber(insights.char_count_no_whitespace)],
    ["Average word length", `${formatNumber(insights.average_word_length)} letters`],
    ["Reading time", formatReadingTime(insights.estimated_reading_time_seconds)],
  ];
  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-medium">Insights</h2>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map(([label, value]) => (
          <div key={label} className="rounded border border-zinc-200 p-3 dark:border-zinc-800">
            <dt className="text-xs text-zinc-500">{label}</dt>
            <dd className="text-lg font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-medium">Top words</h3>
        {insights.top_words.length === 0 ? (
          <p className="text-sm text-zinc-500">None - only common words like &ldquo;the&rdquo;.</p>
        ) : (
          <ol className="flex flex-wrap gap-2">
            {insights.top_words.map((word) => (
              <li key={word} className="rounded bg-zinc-100 px-2 py-1 text-sm dark:bg-zinc-800">
                {word}
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}

function CsvInsightsView({ insights }: { insights: CsvInsights }) {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-medium">Insights</h2>
      <p className="text-sm">
        {formatNumber(insights.row_count)} rows × {formatNumber(insights.column_count)} columns
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-200 dark:border-zinc-800">
            <tr>
              {["Column", "Type", "Empty", "Min", "Max", "Mean"].map((heading) => (
                <th key={heading} className="py-2 pr-4 font-medium">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {insights.columns.map((column, index) => (
              // Index too: a CSV can repeat a header name.
              <tr key={`${index}-${column.name}`} className="border-b border-zinc-100 dark:border-zinc-900">
                <td className="py-2 pr-4 font-medium">{column.name}</td>
                <td className="py-2 pr-4">{column.inferred_type}</td>
                <td className="py-2 pr-4">{formatNumber(column.null_count)}</td>
                <td className="py-2 pr-4">{optional(column.min)}</td>
                <td className="py-2 pr-4">{optional(column.max)}</td>
                <td className="py-2 pr-4">{optional(column.mean)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-zinc-500">Min, max and mean are only computed for numeric columns.</p>
    </section>
  );
}

function Notice({ children, tone = "info" }: { children: React.ReactNode; tone?: "info" | "error" }) {
  const colours =
    tone === "error"
      ? "bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-200"
      : "bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-200";
  return (
    <p role={tone === "error" ? "alert" : "status"} className={`rounded px-3 py-2 text-sm ${colours}`}>
      {children}
    </p>
  );
}

function optional(value: number | null): string {
  return value === null ? "-" : formatNumber(value);
}

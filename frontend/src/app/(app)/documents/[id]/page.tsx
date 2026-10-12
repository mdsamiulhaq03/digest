import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AutoRefresh } from "@/components/auto-refresh";
import { CsvInsightsView } from "@/components/csv-insights";
import {
  documentSource,
  formatDateTime,
  formatNumber,
  formatReadingTime,
} from "@/components/format";
import { HighlightedText, rankStyle } from "@/components/highlighted-text";
import { StatusBadge } from "@/components/status-badge";
import { type Document, getDocument, getJob, type TextInsights } from "@/lib/documents";

const POLL_INTERVAL_MS = 2000;

export default function DocumentPage({ params }: PageProps<"/documents/[id]">) {
  return (
    <Suspense fallback={<p className="text-graphite">Loading…</p>}>
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
      <Link href="/" className="link self-start text-sm">
        Back to your documents
      </Link>
      <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3 border-b border-rule pb-6">
        <div className="min-w-0">
          <h1 className="wrap-break-word text-4xl font-extrabold tracking-tight">{document.title}</h1>
          <p className="mt-2 flex flex-wrap gap-x-4 text-graphite">
            <span>{documentSource(document)}</span>
            <span>
              Added{" "}
              <time dateTime={document.created_at}>{formatDateTime(document.created_at)}</time>
            </span>
          </p>
        </div>
        <StatusBadge status={document.status} />
      </header>
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
          This file is still being analysed. The insights appear here when it&apos;s done.{" "}
          {document.job_id && (
            <Link href={`/jobs/${document.job_id}`} className="link">
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
        {job?.last_error ? `: ${job.last_error}` : "."} Check that it&apos;s a UTF-8 .txt or
        .csv file and upload it again.
      </Notice>
    );
  }
  if (document.insights) {
    return <TextReading insights={document.insights} text={document.text} />;
  }
  if (document.csv_insights) {
    return <CsvInsightsView insights={document.csv_insights} />;
  }
  return null;
}

/** The text on a sheet with its top words marked, and the counts in the margin. */
function TextReading({ insights, text }: { insights: TextInsights; text: string | null }) {
  if (text === null) {
    return <Margin insights={insights} wide />;
  }
  return (
    <div className="grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,1fr)_16rem]">
      <article
        aria-label="Text"
        className="order-2 rounded-md border border-rule bg-sheet px-5 py-8 sm:px-10 sm:py-12 lg:order-1"
      >
        <p className="max-w-[66ch] whitespace-pre-wrap wrap-break-word font-serif text-lg leading-[1.75]">
          <HighlightedText text={text} words={insights.top_words} />
        </p>
      </article>
      <div className="order-1 lg:sticky lg:top-6 lg:order-2">
        <Margin insights={insights} />
      </div>
    </div>
  );
}

function Margin({ insights, wide = false }: { insights: TextInsights; wide?: boolean }) {
  const stats: [string, string][] = [
    ["Words", formatNumber(insights.word_count)],
    ["Different words", formatNumber(insights.unique_word_count)],
    ["Sentences", formatNumber(insights.sentence_count)],
    ["Paragraphs", formatNumber(insights.paragraph_count)],
    ["Characters", formatNumber(insights.char_count)],
    ["Without spaces", formatNumber(insights.char_count_no_whitespace)],
    ["Average word", `${formatNumber(insights.average_word_length)} letters`],
  ];
  return (
    <aside className={`grid gap-8 ${wide ? "sm:grid-cols-2" : "sm:grid-cols-2 lg:grid-cols-1"}`}>
      <section aria-labelledby="top-words" className="flex flex-col gap-3">
        <h2 id="top-words" className="font-semibold">
          Most used words
        </h2>
        {insights.top_words.length === 0 ? (
          <p className="text-graphite">
            None stand out. Only common words like &ldquo;the&rdquo; repeat.
          </p>
        ) : (
          <ol className="flex flex-wrap gap-x-5 gap-y-1.5 lg:flex-col">
            {insights.top_words.map((word, index) => (
              <li key={word} className="flex items-baseline gap-2 lg:gap-3">
                <span className="text-sm text-graphite lg:w-5 lg:text-right">{index + 1}</span>
                <span className="mark font-serif text-lg" style={rankStyle(index)}>
                  {word}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>
      <section aria-labelledby="counts" className="flex flex-col gap-3">
        <h2 id="counts" className="font-semibold">
          {capitalise(formatReadingTime(insights.estimated_reading_time_seconds))} to read
        </h2>
        <dl className="divide-y divide-rule border-y border-rule">
          {stats.map(([label, value]) => (
            <div key={label} className="flex items-baseline justify-between gap-4 py-2">
              <dt className="text-graphite">{label}</dt>
              <dd className="font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </aside>
  );
}

function capitalise(phrase: string): string {
  return phrase.charAt(0).toUpperCase() + phrase.slice(1);
}

function Notice({ children, tone = "info" }: { children: React.ReactNode; tone?: "info" | "error" }) {
  const colours =
    tone === "error"
      ? "border-correction bg-correction-wash"
      : "border-graphite bg-sheet";
  return (
    <p
      role={tone === "error" ? "alert" : "status"}
      className={`max-w-[70ch] rounded-r-md border-l-4 px-4 py-3 ${colours}`}
    >
      {children}
    </p>
  );
}

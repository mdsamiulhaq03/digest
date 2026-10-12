import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AutoRefresh } from "@/components/auto-refresh";
import { Contents } from "@/components/contents";
import { CsvInsightsView } from "@/components/csv-insights";
import {
  creditLine,
  formatDateTime,
  formatNumber,
  formatReadingTime,
} from "@/components/format";
import { HighlightedText, rankStyle } from "@/components/highlighted-text";
import { JobTrail, journeySummary } from "@/components/job-trail";
import { StatusBadge } from "@/components/status-badge";
import {
  type Document,
  getDocument,
  getJob,
  type Job,
  type TextInsights,
} from "@/lib/documents";

const POLL_INTERVAL_MS = 2000;

export default function DocumentPage({ params }: PageProps<"/documents/[id]">) {
  return (
    <Suspense fallback={<p className="text-muted">Loading…</p>}>
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
  const job = document.job_id ? await getJob(document.job_id) : null;
  return (
    <>
      <Link href="/" className="link self-start text-sm">
        Back to your documents
      </Link>
      <header className="flex flex-col gap-3">
        {/* An upload's title is its filename: capitals would change it. */}
        <h1
          className={`cover-line max-w-[28ch] text-5xl wrap-break-word sm:text-6xl ${
            document.original_filename ? "normal-case" : ""
          }`}
        >
          {document.title}
        </h1>
        <p className="credit text-lg">
          {creditLine(document)}, received{" "}
          <time dateTime={document.created_at}>{formatDateTime(document.created_at)}</time>
        </p>
        {/* The running line: state and journey in one glance. */}
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 border-y border-ink py-2 text-[0.9375rem]">
          <StatusBadge status={document.status} jobState={job?.state} />
          <span className="text-muted">{journeySummary(job)}</span>
        </p>
      </header>
      <Body document={document} job={job} />
    </>
  );
}

function Body({ document, job }: { document: Document; job: Job | null }) {
  if (document.status === "processing") {
    return (
      <div className="grid max-w-xl gap-6">
        {/* Swaps itself for the insights once the job finishes. */}
        <AutoRefresh intervalMs={POLL_INTERVAL_MS} />
        <p role="status" className="font-serif text-2xl leading-snug">
          Still being condensed. The counts appear here when the worker is done.
        </p>
        <JobTrail document={document} job={job} />
        {document.job_id && (
          <Link href={`/jobs/${document.job_id}`} className="link justify-self-start">
            Watch the job
          </Link>
        )}
      </div>
    );
  }
  if (document.status === "failed") {
    return (
      <div className="grid max-w-xl gap-6">
        <p role="alert" className="notice notice-error">
          This file couldn&apos;t be analysed
          {job?.last_error ? `: ${withFullStop(job.last_error)}` : "."} Check that it&apos;s a UTF-8 .txt or
          .csv file and upload it again.
        </p>
        <JobTrail document={document} job={job} />
        <Link href="/documents/new" className="btn justify-self-start">
          Upload it again
        </Link>
      </div>
    );
  }
  if (document.insights) {
    return <TextReading document={document} job={job} insights={document.insights} />;
  }
  if (document.csv_insights) {
    return (
      <div className="grid items-start gap-12 lg:grid-cols-[22rem_minmax(0,1fr)]">
        <div className="flex flex-col gap-6 lg:sticky lg:top-6">
          <p className="flex flex-col">
            <span className="cover-line text-8xl leading-[0.85]">
              {formatNumber(document.csv_insights.row_count)}
            </span>
            <span className="cover-label mt-2 text-lg">
              {document.csv_insights.row_count === 1 ? "row" : "rows"} across{" "}
              {formatNumber(document.csv_insights.column_count)}{" "}
              {document.csv_insights.column_count === 1 ? "column" : "columns"}
            </span>
          </p>
          <JobTrail document={document} job={job} />
        </div>
        <CsvInsightsView insights={document.csv_insights} />
      </div>
    );
  }
  return null;
}

/** The counts and the journey down the left, like a digest's contents; the
 * text itself on the right with the words it leans on marked. */
function TextReading({
  document,
  job,
  insights,
}: {
  document: Document;
  job: Job | null;
  insights: TextInsights;
}) {
  return (
    <div className="grid items-start gap-12 lg:grid-cols-[22rem_minmax(0,1fr)] xl:gap-16">
      <div className="flex flex-col gap-6 lg:sticky lg:top-6">
        <p className="flex flex-col">
          <span className="cover-line text-8xl leading-[0.85]">
            {formatNumber(insights.word_count)}
          </span>
          <span className="cover-label mt-2 text-lg">
            words, {formatReadingTime(insights.estimated_reading_time_seconds)} to read
          </span>
        </p>
        <section aria-labelledby="counts" className="section-rule flex flex-col gap-2">
          <h2 id="counts" className="cover-label text-base">
            In this document
          </h2>
          <Contents
            rows={[
              { label: "Different words", figure: formatNumber(insights.unique_word_count) },
              { label: "Sentences", figure: formatNumber(insights.sentence_count) },
              { label: "Paragraphs", figure: formatNumber(insights.paragraph_count) },
              { label: "Characters", figure: formatNumber(insights.char_count) },
              { label: "Without spaces", figure: formatNumber(insights.char_count_no_whitespace) },
              {
                label: "Average word",
                figure: `${formatNumber(insights.average_word_length)} letters`,
              },
            ]}
          />
        </section>
        <JobTrail document={document} job={job} />
      </div>
      <div className="flex min-w-0 flex-col gap-8">
        <TopWords words={insights.top_words} />
        {document.text !== null && (
          <article
            aria-label="Text"
            className="border-t border-ink pt-6 font-serif text-lg leading-[1.75] sm:text-xl"
          >
            <p className="max-w-[68ch] whitespace-pre-wrap wrap-break-word">
              <HighlightedText text={document.text} words={insights.top_words} />
            </p>
          </article>
        )}
      </div>
    </div>
  );
}

/** The API's error text has no closing full stop; the sentence after it needs one. */
function withFullStop(message: string): string {
  return /[.!?]$/.test(message) ? message : `${message}.`;
}

function TopWords({ words }: { words: string[] }) {
  return (
    <section aria-labelledby="top-words" className="section-rule flex flex-col gap-3">
      <h2 id="top-words" className="cover-label text-base">
        Words it leans on
      </h2>
      {words.length === 0 ? (
        <p className="text-muted">
          None stand out. Only common words like &ldquo;the&rdquo; repeat.
        </p>
      ) : (
        <ol className="flex flex-wrap gap-x-6 gap-y-2">
          {words.map((word, index) => (
            <li key={word} className="flex items-baseline gap-1.5">
              <span className="text-sm font-semibold text-viridian">{index + 1}</span>
              <span
                className="mark-word cover-line text-2xl leading-tight"
                style={rankStyle(index)}
              >
                {word}
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

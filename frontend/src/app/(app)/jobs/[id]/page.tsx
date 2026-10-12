import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AutoRefresh } from "@/components/auto-refresh";
import { Contents } from "@/components/contents";
import { formatDateTime } from "@/components/format";
import { jobRows } from "@/components/job-trail";
import { getDocument, getJob, type JobState } from "@/lib/documents";

const POLL_INTERVAL_MS = 1000;

const HEADINGS: Record<JobState, string> = {
  queued: "Waiting its turn",
  running: "Analysing your file",
  succeeded: "Your file is ready",
  failed: "This file couldn't be analysed",
};

export default function JobPage({ params }: PageProps<"/jobs/[id]">) {
  return (
    <Suspense fallback={<p className="text-muted">Loading…</p>}>
      <JobStatus params={params} />
    </Suspense>
  );
}

async function JobStatus({ params }: Pick<PageProps<"/jobs/[id]">, "params">) {
  const { id } = await params;
  const job = await getJob(id);
  if (job === null) {
    notFound();
  }
  const finished = job.state === "succeeded" || job.state === "failed";
  const document = await getDocument(job.document_id);
  return (
    <div className="flex max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-3">
        <h1 aria-live="polite" className="cover-line text-5xl sm:text-6xl">
          {HEADINGS[job.state]}
        </h1>
        {document && (
          <p className="credit text-lg">
            {document.title}, received{" "}
            <time dateTime={document.created_at}>{formatDateTime(document.created_at)}</time>
          </p>
        )}
        <p className="text-sm text-muted">
          {finished ? "" : "This page updates by itself. "}Job {job.id}
        </p>
      </div>
      {/* Polls until the job finishes; a finished page stops rendering it. */}
      {!finished && <AutoRefresh intervalMs={POLL_INTERVAL_MS} />}
      <section aria-labelledby="trail" className="section-rule flex flex-col gap-2">
        <h2 id="trail" className="cover-label text-base">
          How it got here
        </h2>
        <Contents rows={jobRows(job)} className="text-lg" />
      </section>
      {job.state === "failed" && job.last_error && (
        <p role="alert" className="notice notice-error">
          {job.last_error}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        {job.state === "succeeded" && (
          <Link href={`/documents/${job.document_id}`} className="btn">
            Read the insights
          </Link>
        )}
        {job.state !== "succeeded" && (
          <Link href={`/documents/${job.document_id}`} className="link">
            Open the document
          </Link>
        )}
        {job.state === "failed" && (
          <Link href="/documents/new" className="btn">
            Upload it again
          </Link>
        )}
        <Link href="/" className="link">
          Back to your documents
        </Link>
      </div>
    </div>
  );
}

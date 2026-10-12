import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AutoRefresh } from "@/components/auto-refresh";
import { formatDateTime } from "@/components/format";
import { getJob, type Job, type JobState } from "@/lib/documents";

const POLL_INTERVAL_MS = 1000;

const HEADINGS: Record<JobState, string> = {
  queued: "Waiting to be processed…",
  running: "Processing…",
  succeeded: "Done",
  failed: "Processing failed",
};

export default function JobPage({ params }: PageProps<"/jobs/[id]">) {
  return (
    <Suspense fallback={<p className="text-zinc-500">Loading…</p>}>
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
  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight">{HEADINGS[job.state]}</h1>
      {/* Polls until the job finishes; a finished page stops rendering it. */}
      {!finished && <AutoRefresh intervalMs={POLL_INTERVAL_MS} />}
      <Details job={job} />
      {job.state === "failed" && job.last_error && (
        <p
          role="alert"
          className="rounded bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950 dark:text-red-200"
        >
          {job.last_error}
        </p>
      )}
      {job.state === "succeeded" && (
        <Link
          href={`/documents/${job.document_id}`}
          className="self-start rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          View insights
        </Link>
      )}
      {!finished && <p className="text-sm text-zinc-500">This page updates by itself.</p>}
      <Link href="/" className="text-sm underline">
        Back to your documents
      </Link>
    </>
  );
}

function Details({ job }: { job: Job }) {
  const rows: [string, string][] = [
    ["State", job.state],
    ["Attempts", String(job.attempts)],
    ["Queued", formatDateTime(job.queued_at)],
    ...(job.finished_at ? [["Finished", formatDateTime(job.finished_at)] as [string, string]] : []),
  ];
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
      {rows.map(([label, value]) => (
        <div key={label} className="contents">
          <dt className="text-zinc-500">{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AutoRefresh } from "@/components/auto-refresh";
import { formatDateTime } from "@/components/format";
import { getJob, type Job, type JobState } from "@/lib/documents";

const POLL_INTERVAL_MS = 1000;

const HEADINGS: Record<JobState, string> = {
  queued: "Waiting its turn",
  running: "Analysing your file",
  succeeded: "Your file is ready",
  failed: "This file couldn't be analysed",
};

// How far along the three steps each state is.
const REACHED: Record<JobState, number> = { queued: 0, running: 1, succeeded: 2, failed: 2 };

export default function JobPage({ params }: PageProps<"/jobs/[id]">) {
  return (
    <Suspense fallback={<p className="text-graphite">Loading…</p>}>
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
    <div className="flex max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 aria-live="polite" className="text-4xl font-extrabold tracking-tight">
          {HEADINGS[job.state]}
        </h1>
        {!finished && <p className="text-graphite">This page updates by itself.</p>}
      </div>
      {/* Polls until the job finishes; a finished page stops rendering it. */}
      {!finished && <AutoRefresh intervalMs={POLL_INTERVAL_MS} />}
      <Steps job={job} />
      {job.state === "failed" && job.last_error && (
        <p
          role="alert"
          className="rounded-r-md border-l-4 border-correction bg-correction-wash px-4 py-3"
        >
          {job.last_error}
        </p>
      )}
      <Details job={job} />
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        {job.state === "succeeded" && (
          <Link href={`/documents/${job.document_id}`} className="btn">
            View insights
          </Link>
        )}
        <Link href="/" className="link">
          Back to your documents
        </Link>
      </div>
    </div>
  );
}

function Steps({ job }: { job: Job }) {
  const reached = REACHED[job.state];
  const labels = ["Queued", "Analysing", job.state === "failed" ? "Failed" : "Done"];
  return (
    <ol className="grid grid-cols-3 gap-2">
      {labels.map((label, index) => {
        const current = index === reached;
        let bar = "bg-rule";
        if (current && job.state === "failed") {
          bar = "bg-correction";
        } else if (index < reached || job.state === "succeeded") {
          bar = "bg-ink";
        } else if (current) {
          bar = "bg-graphite pulse-dot";
        }
        return (
          <li
            key={label}
            aria-current={current ? "step" : undefined}
            className={`flex flex-col gap-2 text-sm ${index <= reached ? "font-semibold" : "text-graphite"}`}
          >
            <span aria-hidden className={`h-1.5 rounded-full ${bar}`} />
            {label}
          </li>
        );
      })}
    </ol>
  );
}

function Details({ job }: { job: Job }) {
  const rows: [string, string][] = [
    ["Attempts", String(job.attempts)],
    ["Queued", formatDateTime(job.queued_at)],
    ...(job.finished_at ? [["Finished", formatDateTime(job.finished_at)] as [string, string]] : []),
  ];
  return (
    <dl className="divide-y divide-rule border-y border-rule">
      {rows.map(([label, value]) => (
        <div key={label} className="flex justify-between gap-4 py-2">
          <dt className="text-graphite">{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

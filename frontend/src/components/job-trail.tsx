import { Contents, type ContentsRow } from "@/components/contents";
import { formatDuration, formatTime } from "@/components/format";
import type { Document, Job } from "@/lib/documents";

// The worker's default retry limit (backend: settings.job_max_attempts), shown
// so "attempt 1" reads against something.
const MAX_ATTEMPTS = 3;

/** "How it got here": the steps a document went through, as contents lines.
 * The step still happening is the only one in ochre. */
export function JobTrail({ document, job }: { document: Document; job: Job | null }) {
  return (
    <section aria-labelledby="trail" className="section-rule flex flex-col gap-2">
      <h2 id="trail" className="cover-label text-base">
        How it got here
      </h2>
      <Contents rows={job ? jobRows(job) : pastedRows(document)} />
    </section>
  );
}

/** The whole journey in one phrase, for the running line under a title. */
export function journeySummary(job: Job | null): string {
  if (job === null) {
    return "pasted, analysed on arrival";
  }
  const attempts = `${job.attempts} ${job.attempts === 1 ? "attempt" : "attempts"}`;
  switch (job.state) {
    case "queued":
      return `queued ${formatTime(job.queued_at)}, waiting for a worker`;
    case "running":
      return `picked up ${formatTime(job.started_at ?? job.queued_at)}, attempt ${Math.max(job.attempts, 1)} of ${MAX_ATTEMPTS}`;
    case "succeeded":
      return job.finished_at
        ? `queued ${formatTime(job.queued_at)}, analysed in ${formatDuration(job.queued_at, job.finished_at)}`
        : `queued ${formatTime(job.queued_at)}, analysed`;
    case "failed":
      return `gave up after ${attempts}`;
  }
}

function pastedRows(document: Document): ContentsRow[] {
  return [
    { label: "Pasted in", figure: formatTime(document.created_at) },
    { label: "Analysed on arrival", figure: "no queue" },
  ];
}

export function jobRows(job: Job): ContentsRow[] {
  const rows: ContentsRow[] = [{ label: "Queued for the worker", figure: formatTime(job.queued_at) }];
  const attempt = `attempt ${Math.max(job.attempts, 1)} of ${MAX_ATTEMPTS}`;
  if (job.state === "queued") {
    rows.push({ label: "Waiting for a worker", figure: "in line", tone: "live" });
    return rows;
  }
  if (job.started_at) {
    rows.push({ label: `Picked up, ${attempt}`, figure: formatTime(job.started_at) });
  }
  if (job.state === "running") {
    rows.push({ label: "Counting and ranking", figure: "in progress", tone: "live" });
    return rows;
  }
  if (job.finished_at) {
    rows.push(
      job.state === "succeeded"
        ? { label: "Analysed", figure: formatTime(job.finished_at) }
        : { label: "Gave up", figure: formatTime(job.finished_at), tone: "failed" },
    );
    rows.push({ label: "Time taken", figure: formatDuration(job.queued_at, job.finished_at) });
  }
  return rows;
}

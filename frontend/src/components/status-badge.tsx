import type { DocumentStatus, JobState } from "@/lib/documents";

const LABELS: Record<DocumentStatus, string> = {
  ready: "Ready",
  processing: "In progress",
  failed: "Failed",
};

/** With the job's state at hand, a processing document says exactly what is
 * happening to it; without it (the list), it says only that it isn't done. */
export function StatusBadge({ status, jobState }: { status: DocumentStatus; jobState?: JobState }) {
  let label = LABELS[status];
  if (status === "processing" && jobState === "queued") {
    label = "In line";
  } else if (status === "processing" && jobState === "running") {
    label = "Analysing";
  }
  return <span className={`state state-${status}`}>{label}</span>;
}

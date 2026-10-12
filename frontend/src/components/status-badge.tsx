import type { DocumentStatus } from "@/lib/documents";

const LABELS: Record<DocumentStatus, string> = {
  ready: "Ready",
  processing: "Analysing",
  failed: "Failed",
};

const DOTS: Record<DocumentStatus, string> = {
  ready: "bg-settled",
  processing: "bg-graphite pulse-dot",
  failed: "bg-correction",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span className="inline-flex shrink-0 items-center gap-2 text-sm font-medium">
      <span aria-hidden className={`size-2 rounded-full ${DOTS[status]}`} />
      {LABELS[status]}
    </span>
  );
}

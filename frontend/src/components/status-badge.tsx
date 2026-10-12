import type { DocumentStatus } from "@/lib/documents";

const STYLES: Record<DocumentStatus, string> = {
  ready: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  processing: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {status}
    </span>
  );
}

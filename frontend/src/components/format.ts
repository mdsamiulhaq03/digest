import type { Document } from "@/lib/documents";

// Server-rendered, so the server's clock zone would leak into the page; UTC is
// stated rather than guessed.
export function formatDateTime(iso: string): string {
  const formatted = new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
  return `${formatted} UTC`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString("en-GB", { maximumFractionDigits: 2 });
}

export function formatReadingTime(seconds: number): string {
  if (seconds < 60) {
    return "under a minute";
  }
  const minutes = Math.round(seconds / 60);
  return `about ${minutes} min`;
}

/** What kind of document this is. An upload's title is already its filename,
 * so this names the type rather than repeating the name. */
export function documentSource(document: Document): string {
  if (document.size_bytes === null) {
    return "Pasted text";
  }
  const kind = document.content_type === "text/csv" ? "CSV file" : "Text file";
  return `${kind}, ${formatBytes(document.size_bytes)}`;
}

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

/** The day only, in the same style as every other date in the app. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { dateStyle: "medium", timeZone: "UTC" });
}

/** Just the clock time, to the second, for the steps of one job. */
export function formatTime(iso: string): string {
  const formatted = new Date(iso).toLocaleTimeString("en-GB", { timeZone: "UTC" });
  return `${formatted} UTC`;
}

/** How long between two moments, said the way a person would. */
export function formatDuration(fromIso: string, toIso: string): string {
  const seconds = Math.max(0, Math.round((Date.parse(toIso) - Date.parse(fromIso)) / 1000));
  if (seconds < 60) {
    return `${seconds} s`;
  }
  return `${Math.floor(seconds / 60)} min ${seconds % 60} s`;
}

/** The digest's credit line: where this condensed version came from. */
export function creditLine(document: Document): string {
  if (document.size_bytes === null) {
    return "Condensed from pasted text";
  }
  const kind = document.content_type === "text/csv" ? "a CSV file" : "a text file";
  return `Condensed from ${kind}, ${formatBytes(document.size_bytes)}`;
}

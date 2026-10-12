import Link from "next/link";
import { Suspense } from "react";

import { creditLine, formatDateTime } from "@/components/format";
import { StatusBadge } from "@/components/status-badge";
import { type Document, listDocuments } from "@/lib/documents";

export default function DocumentsPage() {
  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
        <h1 className="cover-line text-5xl sm:text-6xl">Your documents</h1>
        <Link href="/documents/new" className="btn">
          New document
        </Link>
      </div>
      <Suspense fallback={<p className="text-muted">Loading your documents…</p>}>
        <DocumentList />
      </Suspense>
    </>
  );
}

async function DocumentList() {
  const documents = await listDocuments();
  if (documents.length === 0) {
    return (
      <section className="section-rule flex max-w-2xl flex-col items-start gap-5 pt-8">
        <p className="font-serif text-3xl leading-snug">
          Nothing condensed yet. Paste some text or upload a file, and Digest will count it,
          rank the words it leans on, and show how it got there.
        </p>
        <p className="text-muted">Pasted text, .txt and .csv files up to 10 MB all work.</p>
        <Link href="/documents/new" className="btn">
          Add your first document
        </Link>
      </section>
    );
  }
  return (
    <section aria-labelledby="count" className="section-rule flex flex-col">
      <h2 id="count" className="cover-label pb-2 text-sm text-muted">
        {documents.length} {documents.length === 1 ? "document" : "documents"}, newest first
      </h2>
      <ul className="border-t border-ink">
        {documents.map((document) => (
          <DocumentRow key={document.id} document={document} />
        ))}
      </ul>
    </section>
  );
}

/** Every entry carries the same furniture in the same places: title, leaders,
 * state; then the credit line and the date beneath. */
function DocumentRow({ document }: { document: Document }) {
  return (
    <li className="border-b border-rule">
      <Link
        href={`/documents/${document.id}`}
        className="group flex flex-col gap-1 py-4 transition-colors hover:bg-surface focus-visible:-outline-offset-2 sm:px-3"
      >
        <span className="flex gap-3 [align-items:last_baseline]">
          <span className="min-w-0 text-lg font-semibold wrap-break-word group-hover:underline group-hover:underline-offset-4">
            {document.title}
          </span>
          <span aria-hidden className="min-w-8 flex-1 -translate-y-1 border-b-2 border-dotted border-[var(--leader)]" />
          <span>
            <StatusBadge status={document.status} />
          </span>
        </span>
        <span className="flex flex-wrap gap-x-4 text-[0.9375rem]">
          <span className="credit">{creditLine(document)}</span>
          <time dateTime={document.created_at} className="text-muted">
            {formatDateTime(document.created_at)}
          </time>
        </span>
      </Link>
    </li>
  );
}

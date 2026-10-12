import Link from "next/link";
import { Suspense } from "react";

import { documentSource, formatDateTime } from "@/components/format";
import { StatusBadge } from "@/components/status-badge";
import { type Document, listDocuments } from "@/lib/documents";

export default function DocumentsPage() {
  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-4xl font-extrabold tracking-tight">Your documents</h1>
        <Link href="/documents/new" className="btn">
          New document
        </Link>
      </div>
      <Suspense fallback={<p className="text-graphite">Loading your documents…</p>}>
        <DocumentList />
      </Suspense>
    </>
  );
}

async function DocumentList() {
  const documents = await listDocuments();
  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-start gap-4 rounded-md border border-dashed border-rule bg-sheet px-6 py-14 sm:px-10">
        <p className="max-w-[34ch] font-serif text-2xl leading-snug">
          Paste some text or upload a file, and Digest will mark the{" "}
          <span className="mark">words</span> it leans on most.
        </p>
        <p className="text-graphite">Plain text and CSV files up to 10 MB both work.</p>
        <Link href="/documents/new" className="btn">
          Add your first document
        </Link>
      </div>
    );
  }
  return (
    <section aria-labelledby="count" className="flex flex-col gap-3">
      <p id="count" className="text-sm text-graphite">
        {documents.length} {documents.length === 1 ? "document" : "documents"}, newest first
      </p>
      <ul className="divide-y divide-rule overflow-hidden rounded-md border border-rule bg-sheet">
        {documents.map((document) => (
          <DocumentRow key={document.id} document={document} />
        ))}
      </ul>
    </section>
  );
}

function DocumentRow({ document }: { document: Document }) {
  return (
    <li>
      <Link
        href={`/documents/${document.id}`}
        className="group flex items-center justify-between gap-6 px-5 py-4 focus-visible:-outline-offset-2"
      >
        <div className="min-w-0">
          <p className="truncate text-lg font-semibold group-hover:underline">{document.title}</p>
          <p className="mt-0.5 flex flex-wrap gap-x-4 text-sm text-graphite">
            <span>{documentSource(document)}</span>
            <time dateTime={document.created_at}>{formatDateTime(document.created_at)}</time>
          </p>
        </div>
        <StatusBadge status={document.status} />
      </Link>
    </li>
  );
}

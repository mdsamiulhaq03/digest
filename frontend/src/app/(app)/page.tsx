import Link from "next/link";
import { Suspense } from "react";

import { documentSource, formatDateTime } from "@/components/format";
import { StatusBadge } from "@/components/status-badge";
import { type Document, listDocuments } from "@/lib/documents";

export default function DocumentsPage() {
  return (
    <>
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Your documents</h1>
        <Link
          href="/documents/new"
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          New document
        </Link>
      </div>
      <Suspense fallback={<p className="text-zinc-500">Loading your documents…</p>}>
        <DocumentList />
      </Suspense>
    </>
  );
}

async function DocumentList() {
  const documents = await listDocuments();
  if (documents.length === 0) {
    return (
      <div className="rounded border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
        <p className="font-medium">No documents yet</p>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Paste some text or upload a .txt or .csv file to see its insights.
        </p>
        <Link href="/documents/new" className="mt-4 inline-block text-sm underline">
          Add your first document
        </Link>
      </div>
    );
  }
  return (
    <>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        {documents.length} {documents.length === 1 ? "document" : "documents"}, newest
        first
      </p>
      <ul className="divide-y divide-zinc-200 rounded border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
        {documents.map((document) => (
          <DocumentRow key={document.id} document={document} />
        ))}
      </ul>
    </>
  );
}

function DocumentRow({ document }: { document: Document }) {
  return (
    <li>
      <Link
        href={`/documents/${document.id}`}
        className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-900"
      >
        <div className="min-w-0">
          <p className="truncate font-medium">{document.title}</p>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {documentSource(document)} · {formatDateTime(document.created_at)}
          </p>
        </div>
        <StatusBadge status={document.status} />
      </Link>
    </li>
  );
}

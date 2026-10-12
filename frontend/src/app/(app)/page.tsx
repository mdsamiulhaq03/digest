import { Suspense } from "react";

import { getApiStatus } from "@/lib/api";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 px-4 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">Digest</h1>
      <p className="text-zinc-600 dark:text-zinc-400">
        Document ingestion and insights. The interface arrives in Phase 8.
      </p>
      <Suspense fallback={<p className="text-zinc-500">Checking the API…</p>}>
        <ApiStatusLine />
      </Suspense>
    </main>
  );
}

async function ApiStatusLine() {
  const status = await getApiStatus();
  const colour = status === "ok" ? "text-green-600" : "text-red-600";
  return (
    <p>
      API: <span className={colour}>{status}</span>
    </p>
  );
}

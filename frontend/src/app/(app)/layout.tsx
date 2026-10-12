import Link from "next/link";
import { Suspense } from "react";

import { logout } from "@/app/(auth)/actions";
import { ApiStatusLine } from "@/components/api-status";
import { getCurrentUser } from "@/lib/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-3">
          <Link href="/" className="font-semibold tracking-tight">
            Digest
          </Link>
          {/* The session read stays inside a boundary, so the rest of the
              layout doesn't wait on it. */}
          <Suspense fallback={null}>
            <Account />
          </Suspense>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-8">
        {children}
      </main>
      <footer className="mx-auto w-full max-w-3xl px-4 py-4 text-xs text-zinc-500">
        <Suspense fallback={null}>
          <ApiStatusLine />
        </Suspense>
      </footer>
    </>
  );
}

async function Account() {
  const user = await getCurrentUser();
  return (
    <div className="flex items-center gap-3 text-sm">
      {user.role === "admin" && (
        <Link href="/admin" className="underline">
          Admin
        </Link>
      )}
      <span className="text-zinc-600 dark:text-zinc-400">{user.email}</span>
      <form action={logout}>
        <button type="submit" className="underline">
          Log out
        </button>
      </form>
    </div>
  );
}

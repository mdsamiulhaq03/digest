import Link from "next/link";
import { Suspense } from "react";

import { logout } from "@/app/(auth)/actions";
import { ApiStatusLine } from "@/components/api-status";
import { getCurrentUser } from "@/lib/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b border-rule">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-4 sm:px-6">
          <Link href="/" className="text-xl font-extrabold tracking-tight">
            Digest
          </Link>
          {/* The session read stays inside a boundary, so the rest of the
              layout doesn't wait on it. */}
          <Suspense fallback={null}>
            <Account />
          </Suspense>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-10 sm:px-6">
        {children}
      </main>
      <footer className="mx-auto w-full max-w-5xl px-4 pb-6 text-sm text-graphite sm:px-6">
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
    <nav className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
      <Link href="/" className="font-medium hover:underline">
        Documents
      </Link>
      {user.role === "admin" && (
        <Link href="/admin" className="font-medium hover:underline">
          Accounts
        </Link>
      )}
      <span className="text-graphite">{user.email}</span>
      <form action={logout}>
        <button type="submit" className="link">
          Log out
        </button>
      </form>
    </nav>
  );
}

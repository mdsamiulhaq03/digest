import Link from "next/link";
import { Suspense } from "react";

import { logout } from "@/app/(auth)/actions";
import { ApiStatusLine } from "@/components/api-status";
import { NavLink } from "@/components/nav-link";
import { getCurrentUser } from "@/lib/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="band">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-x-8 gap-y-3 px-4 py-4 sm:px-8">
          <Link href="/" className="cover-line text-4xl">
            Digest
          </Link>
          {/* The session read stays inside a boundary, so the rest of the
              layout doesn't wait on it. */}
          <Suspense fallback={null}>
            <Account />
          </Suspense>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-10 sm:px-8">
        {children}
      </main>
      <footer className="mx-auto w-full max-w-6xl px-4 pb-8 sm:px-8">
        <div className="border-t border-rule pt-4 text-muted">
          <Suspense fallback={null}>
            <ApiStatusLine />
          </Suspense>
        </div>
      </footer>
    </>
  );
}

async function Account() {
  const user = await getCurrentUser();
  return (
    <nav aria-label="Main" className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[0.9375rem]">
      <NavLink href="/">Documents</NavLink>
      <NavLink href="/documents/new">New document</NavLink>
      {user.role === "admin" && <NavLink href="/admin">Accounts</NavLink>}
      <span className="hidden text-on-band-muted sm:inline">{user.email}</span>
      <form action={logout}>
        <button
          type="submit"
          className="font-medium underline decoration-on-band-muted underline-offset-4 hover:decoration-on-band"
        >
          Log out
        </button>
      </form>
    </nav>
  );
}

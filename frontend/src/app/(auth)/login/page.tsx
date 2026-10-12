import Link from "next/link";
import { Suspense } from "react";

import { login } from "../actions";
import { AuthForm } from "../auth-form";
import { DemoButtons } from "../demo-buttons";

export default function LoginPage({ searchParams }: PageProps<"/login">) {
  return (
    <>
      <h1 className="text-xl font-medium">Log in</h1>
      {/* Reads the URL at request time, so it streams in behind a boundary. */}
      <Suspense fallback={null}>
        <ExpiredNotice searchParams={searchParams} />
      </Suspense>
      <AuthForm action={login} submitLabel="Log in" />
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        No account?{" "}
        <Link href="/register" className="underline">
          Create one
        </Link>
      </p>
      {/* Asks the API whether demo mode is on, so it streams in separately. */}
      <Suspense fallback={null}>
        <DemoButtons />
      </Suspense>
    </>
  );
}

async function ExpiredNotice({ searchParams }: Pick<PageProps<"/login">, "searchParams">) {
  const { expired } = await searchParams;
  if (expired !== "1") {
    return null;
  }
  return (
    <p className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
      Your session has expired. Log in again.
    </p>
  );
}

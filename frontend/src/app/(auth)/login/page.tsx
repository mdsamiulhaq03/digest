import Link from "next/link";
import { Suspense } from "react";

import { login } from "../actions";
import { AuthForm } from "../auth-form";
import { DemoButtons } from "../demo-buttons";

export default function LoginPage({ searchParams }: PageProps<"/login">) {
  return (
    <>
      <h1 className="text-3xl font-extrabold tracking-tight">Log in</h1>
      {/* Reads the URL at request time, so it streams in behind a boundary. */}
      <Suspense fallback={null}>
        <ExpiredNotice searchParams={searchParams} />
      </Suspense>
      <AuthForm action={login} submitLabel="Log in" />
      <p className="text-graphite">
        No account?{" "}
        <Link href="/register" className="link text-ink">
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
    <p role="status" className="rounded-r-md border-l-4 border-graphite bg-sheet px-4 py-3">
      Your session has expired. Log in again.
    </p>
  );
}

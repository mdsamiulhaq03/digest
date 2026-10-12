import Link from "next/link";

import { NotFoundNotice } from "@/components/not-found-notice";

// Any address that matches no route. There's no session read here, so the
// band carries only the wordmark.
export default function NotFound() {
  return (
    <>
      <header className="band">
        <div className="mx-auto w-full max-w-6xl px-4 py-4 sm:px-8">
          <Link href="/" className="cover-line text-4xl">
            Digest
          </Link>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-8">
        <NotFoundNotice />
      </main>
    </>
  );
}

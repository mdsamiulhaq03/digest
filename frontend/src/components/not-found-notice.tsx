import Link from "next/link";

/** What every "nothing here" shows. Someone else's document lands here too,
 * worded so it never says whether the id exists. */
export function NotFoundNotice() {
  return (
    <div className="flex max-w-2xl flex-col items-start gap-6">
      <h1 className="cover-line text-5xl sm:text-6xl">Nothing here</h1>
      <p className="font-serif text-xl leading-relaxed text-muted">
        There&apos;s no document, job or page of yours at this address. It may have been
        removed, or the link may be wrong.
      </p>
      <Link href="/" className="btn">
        Back to your documents
      </Link>
    </div>
  );
}

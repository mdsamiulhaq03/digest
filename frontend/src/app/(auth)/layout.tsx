export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid flex-1 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
      <section className="flex flex-col justify-between gap-10 border-b border-rule bg-sheet px-4 py-8 sm:px-10 lg:border-r lg:border-b-0 lg:px-16 lg:py-14">
        <p className="text-xl font-extrabold tracking-tight">Digest</p>
        <Specimen />
        <p className="hidden text-sm text-graphite lg:block">
          Works with pasted text, .txt files and .csv files.
        </p>
      </section>
      <main className="flex flex-col justify-center px-4 py-12 sm:px-10 lg:px-16">
        <div className="mx-auto flex w-full max-w-sm flex-col gap-6">{children}</div>
      </main>
    </div>
  );
}

/** A sample of what Digest does: the paragraph's own most used word, marked. */
function Specimen() {
  return (
    <figure className="flex max-w-xl flex-col gap-5">
      <blockquote className="font-serif text-2xl leading-snug sm:text-4xl sm:leading-[1.2]">
        Every piece of writing leans on a few <Mark i={0}>words</Mark> more than the rest.
        Paste or upload yours, and Digest counts its <Mark i={1}>words</Mark>, sentences and
        paragraphs, then marks the <Mark i={2}>words</Mark> that keep coming back.
      </blockquote>
      <figcaption className="text-graphite">
        Here, that&apos;s &ldquo;words&rdquo;, used three times.
      </figcaption>
    </figure>
  );
}

function Mark({ i, children }: { i: number; children: React.ReactNode }) {
  return (
    <span className="mark mark-draw" style={{ "--i": i } as React.CSSProperties}>
      {children}
    </span>
  );
}

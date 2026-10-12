import { Contents } from "@/components/contents";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid flex-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <Cover />
      <main className="flex flex-col justify-center px-4 py-12 sm:px-10 lg:px-16">
        <div className="mx-auto flex w-full max-w-sm flex-col gap-6">{children}</div>
      </main>
    </div>
  );
}

/** The digest's cover: its contents are exactly what Digest does to a
 * document. The leaders set across once, on arrival. */
function Cover() {
  return (
    <section className="band flex flex-col justify-between gap-10 px-4 py-8 sm:px-10 lg:px-16 lg:py-14">
      <p className="cover-line text-[clamp(4.5rem,11vw,9rem)] leading-[0.8]">Digest</p>
      <div className="flex max-w-lg flex-col gap-4">
        <p className="cover-label border-t-[3px] border-on-band pt-3 text-base">
          What it makes of a document
        </p>
        <Contents
          animated
          className="text-lg [--leader:var(--on-band-muted)]"
          rows={[
            { label: "Words, sentences, paragraphs", figure: "counted" },
            { label: "The ten words it leans on", figure: "ranked" },
            { label: "Time it takes to read", figure: "estimated" },
            { label: "CSV columns, types, min and max", figure: "profiled" },
            { label: "Every upload, queue to finish", figure: "tracked" },
          ]}
        />
      </div>
      <p className="credit text-on-band-muted">
        Works with pasted text, .txt files and .csv files up to 10 MB.
      </p>
    </section>
  );
}

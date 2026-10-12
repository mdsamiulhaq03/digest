import { NewDocumentForms } from "./new-document-forms";

export default function NewDocumentPage() {
  return (
    <div className="flex max-w-3xl flex-col gap-8">
      <div className="flex flex-col gap-3">
        <h1 className="cover-line text-5xl sm:text-6xl">New document</h1>
        <p className="max-w-[56ch] font-serif text-xl leading-relaxed text-muted">
          Pasted text is condensed straight away. An uploaded file goes to the worker&apos;s
          queue, and you can watch it go through.
        </p>
      </div>
      <NewDocumentForms />
    </div>
  );
}

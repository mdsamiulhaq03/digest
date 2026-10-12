import { NewDocumentForms } from "./new-document-forms";

export default function NewDocumentPage() {
  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-extrabold tracking-tight">New document</h1>
        <p className="max-w-[60ch] text-graphite">
          Pasted text is analysed straight away. An uploaded file is analysed in the
          background, and you can watch its progress.
        </p>
      </div>
      <NewDocumentForms />
    </div>
  );
}

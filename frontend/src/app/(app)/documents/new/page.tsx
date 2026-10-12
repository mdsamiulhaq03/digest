import { NewDocumentForms } from "./new-document-forms";

export default function NewDocumentPage() {
  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight">New document</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Pasted text is analysed straight away. An uploaded file is analysed in the
        background, and you can watch its progress.
      </p>
      <NewDocumentForms />
    </>
  );
}

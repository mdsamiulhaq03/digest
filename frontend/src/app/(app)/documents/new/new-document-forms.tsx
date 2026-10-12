"use client";

import { useActionState, useState } from "react";

import { createTextDocument, type NewDocumentState, uploadDocument } from "./actions";

// The API's limit (MAX_UPLOAD_BYTES). Checked here first so nobody sends
// 10+ MB only to have it refused.
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

type Tab = "text" | "file";

const TAB_LABELS: Record<Tab, string> = { text: "Paste text", file: "Upload a file" };

const INPUT = "rounded border border-zinc-300 bg-transparent px-3 py-2 dark:border-zinc-700";

export function NewDocumentForms() {
  const [tab, setTab] = useState<Tab>("text");
  return (
    <div className="flex flex-col gap-6">
      <div role="tablist" className="flex gap-2 border-b border-zinc-200 dark:border-zinc-800">
        {(Object.keys(TAB_LABELS) as Tab[]).map((option) => (
          <button
            key={option}
            type="button"
            role="tab"
            aria-selected={tab === option}
            onClick={() => setTab(option)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab === option
                ? "border-zinc-900 dark:border-zinc-100"
                : "border-transparent text-zinc-500"
            }`}
          >
            {TAB_LABELS[option]}
          </button>
        ))}
      </div>
      {tab === "text" ? <PasteForm /> : <UploadForm />}
    </div>
  );
}

function PasteForm() {
  const [state, action, pending] = useActionState(createTextDocument, undefined);
  return (
    <form action={action} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">Title</span>
        <input
          name="title"
          required
          maxLength={255}
          defaultValue={state?.title}
          aria-invalid={state?.fieldErrors.title ? true : undefined}
          className={INPUT}
        />
        <FieldError message={state?.fieldErrors.title} />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">Text</span>
        <textarea
          name="text"
          required
          rows={10}
          defaultValue={state?.text}
          aria-invalid={state?.fieldErrors.text ? true : undefined}
          className={INPUT}
        />
        <FieldError message={state?.fieldErrors.text} />
      </label>
      <FormFooter state={state} pending={pending} label="Get insights" />
    </form>
  );
}

function UploadForm() {
  const [state, action, pending] = useActionState(uploadDocument, undefined);
  const [tooLarge, setTooLarge] = useState(false);
  return (
    <form action={action} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">File</span>
        <input
          name="file"
          type="file"
          required
          accept=".txt,.csv"
          onChange={(event) => {
            const file = event.target.files?.[0];
            setTooLarge(file !== undefined && file.size > MAX_UPLOAD_BYTES);
          }}
          className="text-sm"
        />
        <span className="text-zinc-500">A .txt or .csv file, up to 10 MB, UTF-8 encoded.</span>
        <FieldError message={tooLarge ? "That file is over 10 MB." : undefined} />
      </label>
      <FormFooter state={state} pending={pending} disabled={tooLarge} label="Upload" />
    </form>
  );
}

function FormFooter({
  state,
  pending,
  disabled = false,
  label,
}: {
  state: NewDocumentState;
  pending: boolean;
  disabled?: boolean;
  label: string;
}) {
  return (
    <>
      {state?.message && (
        <p role="alert" className="text-sm text-red-600">
          {state.message}
        </p>
      )}
      <button
        type="submit"
        disabled={pending || disabled}
        className="self-start rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {pending ? "Please wait…" : label}
      </button>
    </>
  );
}

function FieldError({ message }: { message?: string }) {
  return message ? <span className="text-red-600">{message}</span> : null;
}

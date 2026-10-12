"use client";

import { useActionState, useState } from "react";

import { createTextDocument, type NewDocumentState, uploadDocument } from "./actions";

// The API's limit (MAX_UPLOAD_BYTES). Checked here first so nobody sends
// 10+ MB only to have it refused.
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

type Tab = "text" | "file";

const TAB_LABELS: Record<Tab, string> = { text: "Paste text", file: "Upload a file" };

export function NewDocumentForms() {
  const [tab, setTab] = useState<Tab>("text");
  return (
    <div className="flex flex-col gap-6">
      <div role="tablist" className="flex gap-6 border-b border-rule">
        {(Object.keys(TAB_LABELS) as Tab[]).map((option) => (
          <button
            key={option}
            type="button"
            role="tab"
            aria-selected={tab === option}
            onClick={() => setTab(option)}
            className={`-mb-px border-b-[3px] pb-2.5 font-semibold ${
              tab === option ? "border-ink" : "border-transparent text-graphite hover:text-ink"
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
    <form action={action} className="flex flex-col gap-5">
      <label className="flex flex-col gap-1.5">
        <span className="font-medium">Title</span>
        <input
          name="title"
          required
          maxLength={255}
          defaultValue={state?.title}
          aria-invalid={state?.fieldErrors.title ? true : undefined}
          className="field"
        />
        <FieldError message={state?.fieldErrors.title} />
      </label>
      <label className="flex flex-col gap-1.5">
        <span className="font-medium">Text</span>
        <textarea
          name="text"
          required
          rows={12}
          defaultValue={state?.text}
          aria-invalid={state?.fieldErrors.text ? true : undefined}
          className="field font-serif text-lg leading-relaxed"
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
    <form action={action} className="flex flex-col gap-5">
      <label className="flex flex-col gap-3 rounded-md border border-dashed border-rule bg-sheet px-5 py-8 hover:border-graphite">
        <span className="font-medium">Choose a file</span>
        <input
          name="file"
          type="file"
          required
          accept=".txt,.csv"
          aria-invalid={tooLarge ? true : undefined}
          onChange={(event) => {
            const file = event.target.files?.[0];
            setTooLarge(file !== undefined && file.size > MAX_UPLOAD_BYTES);
          }}
          className="text-sm text-graphite file:mr-4 file:cursor-pointer file:rounded-md file:border file:border-rule file:bg-paper file:px-3 file:py-2 file:font-semibold file:text-ink"
        />
        <span className="text-sm text-graphite">
          A .txt or .csv file, up to 10 MB, UTF-8 encoded.
        </span>
        <FieldError
          message={tooLarge ? "That file is over 10 MB. Pick a smaller one." : undefined}
        />
      </label>
      <FormFooter state={state} pending={pending} disabled={tooLarge} label="Upload and analyse" />
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
        <p role="alert" className="text-correction">
          {state.message}
        </p>
      )}
      <button type="submit" disabled={pending || disabled} className="btn self-start">
        {pending ? "Working…" : label}
      </button>
    </>
  );
}

function FieldError({ message }: { message?: string }) {
  return message ? <span className="text-sm text-correction">{message}</span> : null;
}

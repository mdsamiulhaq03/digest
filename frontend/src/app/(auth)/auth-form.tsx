"use client";

import { useActionState } from "react";

import type { AuthFormState } from "./actions";

type AuthAction = (state: AuthFormState, formData: FormData) => Promise<AuthFormState>;

export function AuthForm({
  action,
  submitLabel,
  passwordHint,
}: {
  action: AuthAction;
  submitLabel: string;
  passwordHint?: string;
}) {
  const [state, formAction, pending] = useActionState(action, undefined);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <Field
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        defaultValue={state?.email}
        error={state?.fieldErrors.email}
      />
      <Field
        label="Password"
        name="password"
        type="password"
        autoComplete={passwordHint ? "new-password" : "current-password"}
        hint={passwordHint}
        error={state?.fieldErrors.password}
      />
      {state?.message && (
        <p role="alert" className="text-sm text-red-600">
          {state.message}
        </p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="rounded bg-zinc-900 px-4 py-2 font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {pending ? "Please wait…" : submitLabel}
      </button>
    </form>
  );
}

function Field({
  label,
  name,
  type,
  autoComplete,
  defaultValue,
  hint,
  error,
}: {
  label: string;
  name: string;
  type: string;
  autoComplete: string;
  defaultValue?: string;
  hint?: string;
  error?: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium">{label}</span>
      <input
        name={name}
        type={type}
        required
        autoComplete={autoComplete}
        defaultValue={defaultValue}
        aria-invalid={error ? true : undefined}
        className="rounded border border-zinc-300 bg-transparent px-3 py-2 dark:border-zinc-700"
      />
      {hint && !error && <span className="text-zinc-500">{hint}</span>}
      {error && <span className="text-red-600">{error}</span>}
    </label>
  );
}

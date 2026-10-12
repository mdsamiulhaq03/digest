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
    <form action={formAction} className="flex flex-col gap-5">
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
        <p role="alert" className="notice notice-error">
          {state.message}
        </p>
      )}
      <button type="submit" disabled={pending} className="btn w-full">
        {pending ? "Working…" : submitLabel}
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
    <label className="flex flex-col gap-1.5">
      <span className="font-semibold">{label}</span>
      <input
        name={name}
        type={type}
        required
        autoComplete={autoComplete}
        defaultValue={defaultValue}
        aria-invalid={error ? true : undefined}
        className="field"
      />
      {hint && !error && <span className="text-sm text-muted">{hint}</span>}
      {error && <span className="text-sm font-medium text-fail">{error}</span>}
    </label>
  );
}

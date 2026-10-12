import Link from "next/link";

import { register } from "../actions";
import { AuthForm } from "../auth-form";

export default function RegisterPage() {
  return (
    <>
      <h1 className="text-xl font-medium">Create an account</h1>
      <AuthForm
        action={register}
        submitLabel="Create account"
        passwordHint="At least 8 characters."
      />
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Already have one?{" "}
        <Link href="/login" className="underline">
          Log in
        </Link>
      </p>
    </>
  );
}

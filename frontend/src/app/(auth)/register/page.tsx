import Link from "next/link";

import { register } from "../actions";
import { AuthForm } from "../auth-form";

export default function RegisterPage() {
  return (
    <>
      <h1 className="text-3xl font-extrabold tracking-tight">Create an account</h1>
      <AuthForm
        action={register}
        submitLabel="Create account"
        passwordHint="At least 8 characters."
      />
      <p className="text-graphite">
        Already have one?{" "}
        <Link href="/login" className="link text-ink">
          Log in
        </Link>
      </p>
    </>
  );
}

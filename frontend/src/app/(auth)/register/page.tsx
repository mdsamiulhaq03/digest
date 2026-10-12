import Link from "next/link";

import { register } from "../actions";
import { AuthForm } from "../auth-form";

export default function RegisterPage() {
  return (
    <>
      <h1 className="cover-line text-5xl">Create an account</h1>
      <AuthForm
        action={register}
        submitLabel="Create account"
        passwordHint="At least 8 characters."
      />
      <p className="text-muted">
        Already have one?{" "}
        <Link href="/login" className="link">
          Log in
        </Link>
      </p>
    </>
  );
}

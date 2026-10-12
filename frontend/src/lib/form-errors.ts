import "server-only";

import { unstable_rethrow } from "next/navigation";

import { ApiError } from "@/lib/api";

export type FormError = {
  message: string;
  fieldErrors: Record<string, string>;
};

/** Turns a failed API call into what a form shows: one message, plus a
 * message next to each field the API rejected. */
export function toFormError(error: unknown): FormError {
  // redirect() and friends work by throwing; they must reach Next.js.
  unstable_rethrow(error);
  if (error instanceof ApiError) {
    const hasFieldErrors = Object.keys(error.fieldErrors).length > 0;
    // Field errors are shown next to their fields; the API's own summary for
    // those ("Request validation failed") is for developers, not users. Its
    // other messages ("Invalid email or password", "Only .txt, .csv files
    // are accepted") are written for users and shown as they are.
    const message = hasFieldErrors ? "Check the highlighted fields." : error.message;
    return { message, fieldErrors: error.fieldErrors };
  }
  console.error("request to the API failed:", error);
  return {
    message: "Something went wrong reaching the server. Try again.",
    fieldErrors: {},
  };
}

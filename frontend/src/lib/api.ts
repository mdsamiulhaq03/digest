import "server-only";

import { unstable_rethrow } from "next/navigation";
import { connection } from "next/server";

// The only way into FastAPI. Server-side only: the browser talks to Next.js
// alone, so it never learns where the API lives - and never holds the login
// token, which stays in an httpOnly cookie (see session.ts).

// Above the API's own worst case (~3.5s when Postgres's hostname won't
// resolve), so a "not ready" answer arrives instead of a timeout.
const HEALTH_TIMEOUT_MS = 5000;

// ok: ready to serve. not_ready: the API answered but can't serve (e.g. no
// Postgres). unreachable: no answer at all, or no API_URL to ask.
export type ApiStatus = "ok" | "not_ready" | "unreachable";

/** A failed API call, carrying the API's own message and, for a rejected
 * payload, which field was wrong and why. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly fieldErrors: Record<string, string> = {},
  ) {
    super(message);
  }
}

// The API's one error shape (see the README's "Errors" section).
type ErrorBody = {
  error?: {
    message?: string;
    details?: { loc: (string | number)[]; msg: string }[];
  };
};

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  // Defers to request time. Without it, Next.js would prerender callers at
  // build time - when API_URL isn't set - and serve that result forever.
  await connection();
  const baseUrl = process.env.API_URL;
  if (!baseUrl) {
    throw new Error("API_URL is not set");
  }
  return fetch(new URL(path, baseUrl), init);
}

/** Calls the API and returns the parsed JSON body, or throws ApiError. */
export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) {
    throw await toApiError(response);
  }
  return (await response.json()) as T;
}

async function toApiError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => ({}))) as ErrorBody;
  const details = body.error?.details ?? [];
  // loc is e.g. ["body", "password"]: the last part names the field.
  const fieldErrors = Object.fromEntries(
    details.map((detail) => [String(detail.loc.at(-1)), detail.msg]),
  );
  return new ApiError(
    response.status,
    body.error?.message ?? `API returned HTTP ${response.status}`,
    fieldErrors,
  );
}

export async function getApiStatus(): Promise<ApiStatus> {
  try {
    const response = await apiFetch("/health/ready", {
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    if (!response.ok) {
      console.error(`API not ready: HTTP ${response.status}`);
      return "not_ready";
    }
    return "ok";
  } catch (error) {
    // Next.js stops prerendering by throwing from connection(); that signal
    // must reach Next.js, not be logged here as a failed health check.
    unstable_rethrow(error);
    // Logged on the server only. Without it, a missing API_URL looks
    // exactly like the API being down.
    console.error("API health check failed:", error);
    return "unreachable";
  }
}

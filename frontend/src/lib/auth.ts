import "server-only";

import { redirect } from "next/navigation";

import { ApiError, apiJson } from "@/lib/api";
import { getToken } from "@/lib/session";

// The data access layer: every call made as the signed-in user goes through
// here, so the "no token, or a token the API rejects" handling lives in one
// place. proxy.ts only redirects when the cookie is missing - a cheap first
// filter. The real check is the API accepting the token, on every call.

export type CurrentUser = {
  id: string;
  email: string;
  role: string;
};

export async function authedJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken();
  if (!token) {
    redirect("/login");
  }
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  try {
    return await apiJson<T>(path, { ...init, headers });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      // Expired, or the account was deleted. Logging in again replaces the
      // stale cookie.
      redirect("/login?expired=1");
    }
    throw error;
  }
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const user = await authedJson<CurrentUser>("/auth/me");
  // Only what the UI shows - nothing else from the API reaches the client.
  return { id: user.id, email: user.email, role: user.role };
}

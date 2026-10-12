import "server-only";

import { cookies } from "next/headers";

import { TOKEN_COOKIE } from "@/lib/session-cookie";

// The API's access token, kept in a cookie no script on the page can read
// (httpOnly) - so an XSS bug can't steal it. Only server code touches it.

export async function getToken(): Promise<string | undefined> {
  return (await cookies()).get(TOKEN_COOKIE)?.value;
}

export async function saveToken(token: string, expiresInSeconds: number): Promise<void> {
  (await cookies()).set(TOKEN_COOKIE, token, {
    httpOnly: true,
    // Browsers treat http://localhost as a secure origin, so this also works
    // for the production build running locally in Compose.
    secure: process.env.NODE_ENV === "production",
    // Sent on top-level navigations from other sites (following a link in),
    // but not on cross-site form posts - the CSRF protection.
    sameSite: "lax",
    path: "/",
    // Dies with the token: a cookie outliving it would only produce 401s.
    maxAge: expiresInSeconds,
  });
}

export async function clearToken(): Promise<void> {
  (await cookies()).delete(TOKEN_COOKIE);
}

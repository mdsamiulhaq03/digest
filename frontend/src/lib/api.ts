import "server-only";

import { connection } from "next/server";

// The only way into FastAPI. Server-side only: the browser talks to Next.js
// alone, so it never learns where the API lives - and, from Phase 8, never
// holds the login token, which stays in an httpOnly cookie.

const HEALTH_TIMEOUT_MS = 2000;

export type ApiStatus = "ok" | "unreachable";

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

export async function getApiStatus(): Promise<ApiStatus> {
  try {
    const response = await apiFetch("/health", {
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    if (!response.ok) {
      console.error(`API health check failed: HTTP ${response.status}`);
      return "unreachable";
    }
    return "ok";
  } catch (error) {
    // Logged on the server only. Without it, a missing API_URL looks
    // exactly like the API being down.
    console.error("API health check failed:", error);
    return "unreachable";
  }
}

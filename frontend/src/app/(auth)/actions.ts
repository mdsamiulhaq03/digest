"use server";

import { redirect } from "next/navigation";

import { apiJson } from "@/lib/api";
import type { DemoRole } from "@/lib/demo";
import { toFormError } from "@/lib/form-errors";
import { clearToken, saveToken } from "@/lib/session";

export type AuthFormState =
  | {
      message: string;
      fieldErrors: Record<string, string>;
      // Re-filled after a failed attempt, so the user only retypes the password.
      email: string;
    }
  | undefined;

type TokenResponse = { access_token: string; expires_in: number };

export async function login(_: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const credentials = readCredentials(formData);
  try {
    await logIn(credentials);
  } catch (error) {
    return failure(error, credentials.email);
  }
  redirect("/");
}

export async function register(_: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const credentials = readCredentials(formData);
  try {
    await apiJson("/auth/register", jsonPost(credentials));
    // Straight in: making a new user log in with what they just typed adds
    // nothing.
    await logIn(credentials);
  } catch (error) {
    return failure(error, credentials.email);
  }
  redirect("/");
}

export async function logout(): Promise<void> {
  await clearToken();
  redirect("/login");
}

type Credentials = { email: string; password: string };

function readCredentials(formData: FormData): Credentials {
  return {
    email: String(formData.get("email") ?? "").trim(),
    password: String(formData.get("password") ?? ""),
  };
}

async function logIn(credentials: Credentials): Promise<void> {
  const token = await apiJson<TokenResponse>("/auth/login", jsonPost(credentials));
  await saveToken(token.access_token, token.expires_in);
}

function jsonPost(body: Credentials): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

function failure(error: unknown, email: string): AuthFormState {
  return { ...toFormError(error), email };
}

export async function demoLogin(role: DemoRole): Promise<void> {
  // The API refuses this (404) unless demo mode is on; the buttons only show
  // when it is, so a failure here is unexpected and goes to the error page.
  const token = await apiJson<TokenResponse>("/auth/demo/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  await saveToken(token.access_token, token.expires_in);
  redirect("/");
}

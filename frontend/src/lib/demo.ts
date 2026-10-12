import "server-only";

import { unstable_rethrow } from "next/navigation";

import { ApiError, apiJson } from "@/lib/api";

export type DemoRole = "user" | "admin";
export type DemoAccount = { role: DemoRole; email: string };

/** The demo accounts the API offers, or none when demo mode is off (the API
 * answers 404) or the API can't be asked. */
export async function getDemoAccounts(): Promise<DemoAccount[]> {
  try {
    const { accounts } = await apiJson<{ accounts: DemoAccount[] }>("/auth/demo");
    return accounts;
  } catch (error) {
    unstable_rethrow(error);
    // 404 is the normal answer with demo mode off; anything else is a fault
    // worth seeing in the server log, not a silent missing button.
    if (!(error instanceof ApiError && error.status === 404)) {
      console.error("demo accounts unavailable:", error);
    }
    return [];
  }
}

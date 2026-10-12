import { defineConfig, devices } from "@playwright/test";

// End-to-end tests against the whole running stack - web, API, worker,
// Postgres, Redis - started with `docker compose up`. Nothing is mocked.
export default defineConfig({
  testDir: "./e2e",
  // Every test registers its own user, so tests share nothing and can run
  // in parallel and in any order.
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  // No retries: a flaky test is a bug to fix, not something to rerun until
  // it happens to pass.
  retries: 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});

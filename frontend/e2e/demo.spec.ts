import { expect, test } from "@playwright/test";

import { expectSignedInAs } from "./helpers";

// Needs DEMO_ACCOUNTS on, as docker-compose.yml sets it for the local stack.

test("the demo user is an ordinary user", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /Log in as demo user/ }).click();

  await expectSignedInAs(page, "demo@digest.local");
  await expect(page.getByRole("link", { name: "Admin", exact: true })).toHaveCount(0);
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Your documents" })).toBeVisible();
});

test("the demo admin can see every account", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /Log in as admin/ }).click();
  await expectSignedInAs(page, "admin@digest.local");

  await page.getByRole("link", { name: "Admin", exact: true }).click();
  await expect(page.getByRole("heading", { name: "All accounts" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "admin@digest.local" })).toBeVisible();
});

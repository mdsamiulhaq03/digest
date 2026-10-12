import { expect, test } from "@playwright/test";

import { expectSignedInAs, field, main, PASSWORD, register } from "./helpers";

test("signed out, every page sends you to the login page", async ({ page }) => {
  for (const path of ["/", "/documents/new", "/admin"]) {
    await page.goto(path);
    await expect(page).toHaveURL(/\/login$/);
  }
});

test("register, log out, and log back in", async ({ page }) => {
  const email = await register(page);

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);

  await field(page, "Email").fill(email);
  await field(page, "Password").fill(PASSWORD);
  await main(page).getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Your documents" })).toBeVisible();
  await expectSignedInAs(page, email);
});

test("the login token is out of reach of page scripts", async ({ page }) => {
  await register(page);
  // httpOnly: an XSS bug on the page couldn't read it.
  expect(await page.evaluate(() => document.cookie)).toBe("");
});

test("a wrong password is refused, keeping the email", async ({ page }) => {
  const email = await register(page);
  await page.getByRole("button", { name: "Log out" }).click();

  await field(page, "Email").fill(email);
  await field(page, "Password").fill("not-the-password");
  await main(page).getByRole("button", { name: "Log in", exact: true }).click();

  await expect(main(page).getByRole("alert")).toHaveText("Invalid email or password");
  await expect(field(page, "Email")).toHaveValue(email);
});

test("a too-short password shows the API's reason next to the field", async ({ page }) => {
  await page.goto("/register");
  await field(page, "Email").fill("short-password@example.com");
  await field(page, "Password").fill("short");
  await main(page).getByRole("button", { name: "Create account" }).click();

  await expect(page.getByText("String should have at least 8 characters")).toBeVisible();
  await expect(main(page).getByRole("alert")).toHaveText("Check the highlighted fields.");
});

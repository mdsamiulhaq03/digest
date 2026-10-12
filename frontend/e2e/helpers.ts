import { expect, type Locator, type Page } from "@playwright/test";

export const PASSWORD = "correct-horse-battery";

// Next.js keeps the previous page in the DOM, hidden, for instant
// back-navigation - even inside the same layout, so /login can still contain
// /register's form. Hence the two helpers below.

/** The page's content. Alerts are looked up in here because Next.js's route
 * announcer is a second, empty role="alert" outside <main>. */
export function main(page: Page): Locator {
  return page.getByRole("main");
}

/** A form field by its label, ignoring the hidden previous page's copy. */
export function field(page: Page, label: string): Locator {
  return page.getByLabel(label).filter({ visible: true });
}

/** Signed in: the header shows who, with a Log out button. */
export async function expectSignedInAs(page: Page, email: string): Promise<void> {
  const header = page.getByRole("banner");
  await expect(header.getByRole("button", { name: "Log out" })).toBeVisible();
  await expect(header.getByText(email, { exact: true })).toBeVisible();
}

/** A unique address per call, so tests never share an account. */
export function uniqueEmail(): string {
  return `e2e-${crypto.randomUUID()}@example.com`;
}

/** Registers through the UI and returns the new account's email. Lands on
 * the documents page, signed in. */
export async function register(page: Page): Promise<string> {
  const email = uniqueEmail();
  await page.goto("/register");
  await field(page, "Email").fill(email);
  await field(page, "Password").fill(PASSWORD);
  await main(page).getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Your documents" })).toBeVisible();
  await expectSignedInAs(page, email);
  return email;
}

/** The file input lives behind the "Upload a file" tab. */
export async function uploadFile(
  page: Page,
  file: { name: string; mimeType: string; content: string },
): Promise<void> {
  await page.goto("/documents/new");
  await main(page).getByRole("tab", { name: "Upload a file" }).click();
  await field(page, "File").setInputFiles({
    name: file.name,
    mimeType: file.mimeType,
    buffer: Buffer.from(file.content),
  });
  await main(page).getByRole("button", { name: "Upload", exact: true }).click();
}

import { expect, type Page, test } from "@playwright/test";

import { field, main, register, uploadFile } from "./helpers";

// How long the background worker may take. Polled by Playwright's expect, so
// a fast run finishes as soon as the job does - never a fixed sleep.
const JOB_TIMEOUT_MS = 30_000;

test("a new account starts with an empty list", async ({ page }) => {
  await register(page);
  await expect(page.getByText("No documents yet")).toBeVisible();
});

test("pasted text shows its insights straight away", async ({ page }) => {
  await register(page);
  await page.getByRole("link", { name: "New document", exact: true }).click();
  await field(page, "Title").fill("Fox story");
  // Hand-countable: 9 words, 3 sentences, 2 paragraphs; "fox" repeats.
  await field(page, "Text").fill("The fox ran. The fox hid.\n\nA bird sang.");
  await page.getByRole("button", { name: "Get insights" }).click();

  await expect(page.getByRole("heading", { name: "Fox story" })).toBeVisible();
  await expect(stat(page, "Words")).toHaveText("9");
  await expect(stat(page, "Sentences")).toHaveText("3");
  await expect(stat(page, "Paragraphs")).toHaveText("2");
  await expect(main(page).getByRole("listitem").first()).toHaveText("fox");

  await page.getByRole("link", { name: "← Your documents" }).click();
  const row = page.getByRole("link", { name: /Fox story/ });
  await expect(row).toContainText("Pasted text");
  await expect(row).toContainText("ready");
});

test("an uploaded CSV goes through the worker to its column table", async ({ page }) => {
  await register(page);
  await uploadFile(page, {
    name: "people.csv",
    mimeType: "text/csv",
    content: "name,age\nada,36\nalan,41\n",
  });

  // The job page polls by itself until the worker is done.
  await expect(page).toHaveURL(/\/jobs\//);
  await expect(page.getByRole("heading", { name: "Done" })).toBeVisible({
    timeout: JOB_TIMEOUT_MS,
  });
  await page.getByRole("link", { name: "View insights" }).click();

  await expect(page.getByText("2 rows × 2 columns")).toBeVisible();
  const age = page.getByRole("row", { name: /^age/ });
  await expect(age.getByRole("cell")).toHaveText(["age", "integer", "0", "36", "41", "38.5"]);
});

test("a file that isn't UTF-8 ends as failed, with the reason", async ({ page }) => {
  await register(page);
  await page.goto("/documents/new");
  await main(page).getByRole("tab", { name: "Upload a file" }).click();
  await field(page, "File").setInputFiles({
    name: "latin1.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("caf\xe9", "latin1"),
  });
  await main(page).getByRole("button", { name: "Upload", exact: true }).click();

  await expect(page.getByRole("heading", { name: "Processing failed" })).toBeVisible({
    timeout: JOB_TIMEOUT_MS,
  });
  await expect(main(page).getByRole("alert")).toHaveText("File is not valid UTF-8");
});

test("a file type the API doesn't accept is refused in the form", async ({ page }) => {
  await register(page);
  await uploadFile(page, { name: "report.pdf", mimeType: "application/pdf", content: "%PDF-1.4" });

  await expect(main(page).getByRole("alert")).toHaveText("Only .csv, .txt files are accepted");
  await expect(page).toHaveURL(/\/documents\/new$/);
});

test("someone else's document is a 404, like one that doesn't exist", async ({
  browser,
}) => {
  const ownerContext = await browser.newContext();
  const owner = await ownerContext.newPage();
  await register(owner);
  await owner.getByRole("link", { name: "New document", exact: true }).click();
  await field(owner, "Title").fill("Private");
  await field(owner, "Text").fill("Only mine.");
  await owner.getByRole("button", { name: "Get insights" }).click();
  await expect(owner.getByRole("heading", { name: "Private" })).toBeVisible();
  const documentUrl = owner.url();

  // A separate browser context: its own cookies, so a different user.
  const otherContext = await browser.newContext();
  const other = await otherContext.newPage();
  await register(other);
  await other.goto(documentUrl);

  await expect(other.getByText("This page could not be found.")).toBeVisible();
  await expect(other.getByText("Only mine.")).toHaveCount(0);
  await Promise.all([ownerContext.close(), otherContext.close()]);
});

function stat(page: Page, label: string) {
  // The insight cards are <dt>label</dt><dd>value</dd> pairs.
  return page.locator("dt", { hasText: new RegExp(`^${label}$`) }).locator("+ dd");
}

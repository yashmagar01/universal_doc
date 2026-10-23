import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { E2E_TOKEN } from "./live-env";

// Live ingest journey (M2): Home → upload fixture PDF → SSE progress → analysis workspace.
// Requires fixtures/generated/newsletter_2col.pdf (scripts/fixtures.ps1; e2e.ps1 runs it first).
const FIXTURE_PDF = path.resolve(__dirname, "../../fixtures/generated/newsletter_2col.pdf");

test.describe.configure({ mode: "serial" });

test("upload a PDF and land on the live analysis workspace", async ({ page }) => {
  await page.goto(`/?token=${E2E_TOKEN}`);
  await expect(page.locator('[data-qa="main-content"]')).toBeVisible();
  // one-time token is stripped from the URL after the session bootstrap
  await expect.poll(() => page.url()).not.toContain("token=");

  // live facts come from /status, and the greeting is not a fixture person (F-03)
  await expect(page.locator('[data-qa="status-bar"]')).toContainText("PDF Parser: PyMuPDF");
  await expect(page.locator('[data-qa="main-content"]')).not.toContainText("Shreya Iyer");

  await page.setInputFiles('[data-qa="upload-input"]', FIXTURE_PDF);

  await expect(page.locator('[data-qa="canvas-viewport"]')).toBeVisible({ timeout: 30_000 });
  const reference = page.locator('[data-qa="page-reference"]');
  await expect(reference).toBeVisible();
  expect(
    await reference.evaluate((img) => (img as HTMLImageElement).naturalWidth),
    "reference.png must be a real rendered image",
  ).toBeGreaterThan(0);

  await expect(page.locator('[data-qa="analysis-item"]').first()).toBeVisible();
  expect(await page.locator('[data-qa="analysis-item"]').count()).toBeGreaterThan(5);
  await expect(page.locator('[data-qa="analysis-status"]')).toContainText(/Needs review \(\d+\)/);
  await expect(page.locator('[data-qa="workspace-top-bar"]')).toContainText("newsletter_2col");
  // the live manual path is offered; the unimplemented mode picker is not (F-07)
  await expect(page.getByRole("link", { name: /Choose Mode/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Edit content" })).toBeVisible();

  await page.getByRole("tab", { name: /^Issues/ }).click();
  const issues = page.locator('[data-qa="tabpanel-issues"]');
  await expect(issues).toContainText("font");
  await expect(issues).toContainText("Arial");
});

test("a stored template reopens from Home without a job", async ({ page }) => {
  await page.goto(`/?token=${E2E_TOKEN}`);
  const card = page.getByRole("link", { name: /newsletter_2col/i }).first();
  await expect(card).toBeVisible({ timeout: 15_000 });
  await card.click();

  await expect(page.locator('[data-qa="canvas-viewport"]')).toBeVisible();
  expect(await page.locator('[data-qa="analysis-item"]').count()).toBeGreaterThan(5);
  await expect(page.locator('[data-qa="analysis-status"]')).toBeVisible();
});

test("edit a slot, autosave it, and export a real PDF", async ({ page }) => {
  await page.goto(`/?token=${E2E_TOKEN}`);
  const card = page.getByRole("link", { name: /newsletter_2col/i }).first();
  await expect(card).toBeVisible({ timeout: 15_000 });
  await card.click();
  await expect(page.locator('[data-qa="canvas-viewport"]')).toBeVisible();

  await page.getByRole("button", { name: "Edit content" }).click();
  await expect(page.locator('[data-qa="editor-canvas"]')).toBeVisible({ timeout: 30_000 });
  await expect(page.locator('[data-qa="page-reference"]')).toBeVisible();
  await expect(page.locator('[data-qa="save-status"]')).toHaveAttribute("data-state", "saved");

  const field = page.locator('[data-qa="slot-input"]').first();
  await expect(field).toBeVisible();
  const saved = page.waitForResponse(
    (response) => response.url().includes("/ops") && response.request().method() === "POST",
  );
  await field.fill("Templix live export check");
  expect((await saved).status()).toBe(200);
  await expect(page.locator('[data-qa="save-status"]')).toHaveAttribute("data-state", "saved");

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: /Export PDF/ }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  const file = await download.path();
  expect(file).toBeTruthy();
  expect(fs.statSync(file as string).size).toBeGreaterThan(1000);
});

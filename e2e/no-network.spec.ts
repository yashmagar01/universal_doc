import { test, expect } from "@playwright/test";
import { ROUTES } from "./routes";

// M0 acceptance: the app makes zero runtime network requests to any origin other than its own.
// Fonts, icons and styles are bundled; fixture mode means no backend calls.
test("no runtime network requests leave the app origin", async ({ page }) => {
  const external: string[] = [];
  page.on("request", (req) => {
    const url = req.url();
    if (url.startsWith("data:") || url.startsWith("blob:")) return;
    const host = new URL(url).hostname;
    if (host !== "localhost" && host !== "127.0.0.1") external.push(url);
  });

  for (const route of ROUTES) {
    await page.goto(route.path);
    await expect(page.locator(route.landmark)).toBeVisible();
  }

  expect(external).toEqual([]);
});

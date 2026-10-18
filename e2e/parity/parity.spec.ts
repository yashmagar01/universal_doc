import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { ROUTES } from "../routes";
import { PARITY_SCREENS, regionsFor } from "./regions";

// NFR-TEST-04 scaffold. Renders each design screen at the shared parity viewport and captures our
// landmark geometry + a screenshot into artifacts/parity/ for human review.
//
// This does NOT yet enforce the +/-4% stitch comparison (the Stitch exports carry no data-qa and the
// mapping is not visually signed off). Artifacts feed a later mapping step; see regions.ts.

const OUT = join("artifacts", "parity");
const VIEWPORT = { width: 1333, height: 900, deviceScaleFactor: 1.2 };

const SCREENS = ROUTES.filter((r) => (PARITY_SCREENS as readonly string[]).includes(r.name));

test.describe("parity artifacts (NFR-TEST-04, scaffold)", () => {
  for (const route of SCREENS) {
    test(`${route.name} captures landmark geometry + screenshot`, async ({ page }) => {
      test.setTimeout(60_000);
      const outDir = join(test.info().config.rootDir, "..", OUT);
      mkdirSync(outDir, { recursive: true });

      await page.goto(route.path);
      await expectMounted(page, route.landmark);

      const results = [];
      for (const region of regionsFor(route.name)) {
        const loc = page.locator(region.selector);
        const count = await loc.count();
        const box = count > 0 ? await loc.first().boundingBox() : null;
        results.push({ name: region.name, selector: region.selector, present: count > 0, box });
      }

      expect(results.some((r) => r.present), "no landmark regions found").toBe(true);

      await page.screenshot({ path: join(outDir, `${route.name}.png`), fullPage: true });

      writeFileSync(
        join(outDir, `${route.name}.json`),
        JSON.stringify({ screen: route.name, viewport: VIEWPORT, regions: results }, null, 2) + "\n",
      );
    });
  }
});

async function expectMounted(page: import("@playwright/test").Page, landmark: string) {
  await page.locator(landmark).first().waitFor({ state: "visible" });
  // let entrance motion settle so geometry is stable
  await page.waitForTimeout(300);
}

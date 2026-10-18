import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { ROUTES } from "./routes";

// M0 acceptance (NFR-A11Y-01): no serious/critical axe violations on any screen.
for (const route of ROUTES) {
  test(`a11y: ${route.name} renders and has no serious/critical axe violations`, async ({ page }) => {
    await page.goto(route.path);
    await expect(page.locator(route.landmark)).toBeVisible();
    // Wait for web fonts so Material Symbols ligatures render as glyphs, not as visible
    // text (otherwise axe flags label-content-name-mismatch on icon-only controls). This is
    // load-order flakiness, not a real violation.
    await page.evaluate(() => document.fonts.ready);

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const blocking = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(
      blocking.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.map((n) => n.target) })),
    ).toEqual([]);
  });
}

import { defineConfig, devices } from "@playwright/test";

// Parity viewport from design.md §14: 1333×900 @ DPR 1.2.
// Override the port when something else owns 5173; never reuse a stranger's server then.
const PORT = Number(process.env.E2E_WEB_PORT ?? 5173);
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: ".",
  testIgnore: ["live/**"],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    viewport: { width: 1333, height: 900 },
    deviceScaleFactor: 1.2,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1333, height: 900 }, deviceScaleFactor: 1.2 } }],
  webServer: {
    command: `npx vite --port ${PORT} --strictPort`,
    cwd: "../apps/web",
    env: { VITE_FIXTURES: "1" },
    url: BASE_URL,
    reuseExistingServer: !process.env.CI && !process.env.E2E_WEB_PORT,
    timeout: 60_000,
  },
});

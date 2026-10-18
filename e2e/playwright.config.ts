import { defineConfig, devices } from "@playwright/test";

// Parity viewport from design.md §14: 1333×900 @ DPR 1.2.
const PORT = 5173;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: ".",
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
    command: "npx vite --port 5173 --strictPort",
    cwd: "../apps/web",
    env: { VITE_FIXTURES: "1" },
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});

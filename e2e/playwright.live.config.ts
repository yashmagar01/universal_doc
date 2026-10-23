import { defineConfig, devices } from "@playwright/test";
import os from "node:os";
import path from "node:path";
import { E2E_BASE_URL, E2E_TOKEN, WEB_PORT } from "./live/live-env";

// Live e2e: real FastAPI server (fresh TEMPLIX_HOME per run) + Vite without VITE_FIXTURES.
// Uploads share one server instance, so tests run serially on a single worker.
export default defineConfig({
  testDir: "live",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: E2E_BASE_URL,
    trace: "on-first-retry",
    viewport: { width: 1333, height: 900 },
    deviceScaleFactor: 1.2,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1333, height: 900 }, deviceScaleFactor: 1.2 },
    },
  ],
  webServer: [
    {
      command: "uv run python -m templix.serve",
      cwd: "../apps/server",
      env: {
        TEMPLIX_TOKEN: E2E_TOKEN,
        TEMPLIX_HOME: path.join(os.tmpdir(), `templix-e2e-${Date.now()}`),
        TEMPLIX_PORT: "8000",
        TEMPLIX_WEB_PORT: String(WEB_PORT),
      },
      // /api/v1/status answers 401 without a session cookie — still proves the server is up.
      url: "http://127.0.0.1:8000/api/v1/status",
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npx vite --port ${WEB_PORT} --strictPort`,
      cwd: "../apps/web",
      // .env.development sets VITE_FIXTURES=1; process env wins, so live mode is explicit.
      env: { VITE_FIXTURES: "0" },
      url: E2E_BASE_URL,
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});

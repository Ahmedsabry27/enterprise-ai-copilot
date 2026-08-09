import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e-live",
  outputDir: "artifacts/playwright-live",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "artifacts/playwright-live-report", open: "never" }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:4174",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: process.env.PLAYWRIGHT_REUSE_APP === "true" ? undefined : {
    command: "npm run dev -- --mode e2e --host 127.0.0.1 --port 4174",
    url: "http://127.0.0.1:4174",
    timeout: 120_000,
    reuseExistingServer: false,
  },
  projects: [
    { name: "live-desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "live-mobile", use: { ...devices["iPhone 13"], browserName: "chromium" } },
  ],
});

import fs from "node:fs";
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

type E2EState = {
  token: string;
  cross_tenant_token: string;
  tenant: string;
  actor: string;
  agent_id: string;
};
const statePath = process.env.E2E_STATE_PATH;
if (!statePath) throw new Error("E2E_STATE_PATH is required");
const state = JSON.parse(fs.readFileSync(statePath, "utf8")) as E2EState;
const apiBase = process.env.VITE_API_URL || "http://127.0.0.1:8000";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((token) => {
    window.sessionStorage.setItem("e2e_access_token", token);
  }, state.token);
});

test("real backend persists and filters the seeded Agent", async ({ page }) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/agents")) requests.push(request.url());
  });
  await page.goto("/agents");
  await expect(page.getByRole("heading", { name: "Agents" })).toBeVisible();
  await expect(page.getByText("Live E2E Agent")).toBeVisible();
  await page.getByRole("textbox", { name: /search/i }).fill("Live E2E Agent");
  await expect(page.getByText("Live E2E Agent")).toBeVisible();
  expect(requests.some((url) => url.includes("search=Live+E2E+Agent") || url.includes("search=Live%20E2E%20Agent"))).toBeTruthy();

  const response = await page.request.get(`${apiBase}/api/v1/agents/${state.agent_id}`, {
    headers: { Authorization: `Bearer ${state.token}` },
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.tenant_id).toBe(state.tenant);
  expect(body.owner_id).toBe(state.actor);

  const axe = await new AxeBuilder({ page }).disableRules(["color-contrast"]).analyze();
  expect(axe.violations.filter((item) => ["critical", "serious"].includes(item.impact || ""))).toEqual([]);
});

test("cross-tenant signed identity cannot read the Agent", async ({ request }) => {
  const response = await request.get(`${apiBase}/api/v1/agents/${state.agent_id}`, {
    headers: { Authorization: `Bearer ${state.cross_tenant_token}` },
  });
  expect(response.status()).toBe(404);
});

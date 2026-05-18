// Nightly-by-default e2e — full create/list flow through the UI.
// Pulled onto PRs via the backend-route path trigger (see
// scripts/path_triggers.sh) when the items API changes.
import { test, expect } from "@playwright/test";

test("create an item via the form and see it in the list", async ({ page }) => {
  await page.goto("/");
  const title = `e2e-${Date.now()}`;
  await page.getByPlaceholder("New item title").fill(title);
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.getByRole("listitem").filter({ hasText: title })).toBeVisible();
});

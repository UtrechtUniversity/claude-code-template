import { test, expect } from '@playwright/test';

test('shows Template App heading', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Template App' })).toBeVisible();
});

test('health endpoint returns ok', async ({ request }) => {
  const res = await request.get('/api/health');
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body).toMatchObject({ status: 'ok' });
});

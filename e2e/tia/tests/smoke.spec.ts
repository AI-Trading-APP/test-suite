import { test, expect } from '@playwright/test';

/**
 * No fetch-tap, no SLA collection — just navigate and confirm the analysis
 * page renders a recommendation tier within 60s. Used to isolate whether the
 * SLA fetch-tap is responsible for the timeouts seen in stock-analysis.spec.ts.
 */
test('smoke: /analysis/QSI eventually renders a recommendation', async ({ page }) => {
  page.on('console', (msg) => {
    console.log(`[browser-${msg.type()}]`, msg.text());
  });
  page.on('pageerror', (err) => console.log('[browser-pageerror]', err.message));
  page.on('response', async (resp) => {
    const status = resp.status();
    if (resp.url().includes('/api/') || status >= 400) {
      console.log(`[response] ${resp.request().method()} ${resp.url()} -> ${status}`);
    }
  });

  await page.goto('/analysis/QSI', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1', { hasText: /stock analysis/i })).toBeVisible();

  // If auto-start didn't fire, click Analyse explicitly. The input is already filled by the URL.
  const analyseBtn = page.locator('button', { hasText: /^Analyse$/i }).first();
  await page.waitForTimeout(2_000);
  if (await analyseBtn.isEnabled().catch(() => false)) {
    console.log('[smoke] auto-start did not fire — clicking Analyse manually');
    await analyseBtn.click().catch(() => {});
  }

  const recRegex = /(Strong\s+Buy|Buy|Hold|Sell|Strong\s+Sell)/i;
  await expect(page.locator('body')).toContainText(recRegex, { timeout: 60_000 });
});

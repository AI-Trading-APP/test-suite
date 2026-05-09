import { test, expect, Page } from '@playwright/test';
import { startSample, attachListeners, summariseSamples, SlaSample } from './helpers/sla';
import * as fs from 'fs';
import * as path from 'path';

const TICKERS = (process.env.TIA_TICKERS ?? 'QSI,TOST,TMDX')
  .split(',')
  .map((t) => t.trim().toUpperCase());
const SLA_BUDGET_MS = Number(process.env.TIA_SLA_BUDGET_MS ?? 30_000);
const STREAM_TIMEOUT_MS = SLA_BUDGET_MS + 60_000;

const samples: SlaSample[] = [];

test.afterAll(async () => {
  const out = summariseSamples(samples);
  // eslint-disable-next-line no-console
  console.log(out);
  const reportDir = path.resolve(process.cwd(), 'playwright-report');
  fs.mkdirSync(reportDir, { recursive: true });
  fs.writeFileSync(path.join(reportDir, 'sla.txt'), out);
  fs.writeFileSync(path.join(reportDir, 'sla.json'), JSON.stringify(samples, null, 2));
});

async function dumpDiagnostics(page: Page, ticker: string, sample: SlaSample) {
  const diagDir = path.resolve(process.cwd(), 'playwright-report', 'diag');
  fs.mkdirSync(diagDir, { recursive: true });
  fs.writeFileSync(path.join(diagDir, `${ticker}-sample.json`), JSON.stringify(sample, null, 2));
  await page.screenshot({ path: path.join(diagDir, `${ticker}-final.png`), fullPage: true }).catch(() => {});
}

test.describe('Stock Analysis (TIA) — E2E', () => {
  test.beforeEach(async ({ context }) => {
    // KNOWN ISSUE on test VPS: /api/watchlists returns 403 for the e2etest admin
    // account, causing react-query to retry every ~250ms. Each retry re-renders
    // the Stock Analysis page, which transiently aborts the in-flight SSE
    // consumer (the cleanup function on the useAnalysisStream effect calls
    // AbortController.abort()). Stub the route to a benign empty list so the
    // E2E flow can complete. Tracked separately as a frontend issue.
    await context.route('**/api/watchlists**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    );
  });

  for (const ticker of TICKERS) {
    test(`analyses ${ticker} end-to-end and renders all report sections within SLA`, async ({ page }) => {
      const sample = startSample(ticker);
      attachListeners(page, ticker);

      const navStart = Date.now();
      await page.goto(`/analysis/${ticker}`, { waitUntil: 'domcontentloaded' });
      sample.navigationMs = Date.now() - navStart;

      await expect(page.locator('h1', { hasText: /stock analysis/i })).toBeVisible();

      // Auto-start should fire when the page mounts. If it doesn't, click the button.
      // (The input is pre-populated from the URL.)
      await page.waitForTimeout(2_500);
      const analyseBtn = page.locator('button', { hasText: /^Analyse$/i }).first();
      if (await analyseBtn.isEnabled().catch(() => false)) {
        sample.errors.push('auto-start did not fire — clicked Analyse manually');
        await analyseBtn.click().catch(() => {});
      }

      // Wait for the recommendation tier to appear OR for an error alert.
      const recRegex = /(Strong\s+Buy|Buy|Hold|Sell|Strong\s+Sell)/;
      const errAlert = page.locator('[role="alert"]', { hasText: /(network error|fetch failed|http \d+|unknown error)/i });

      try {
        const winner = await Promise.race([
          page.locator('body').filter({ hasText: recRegex }).first().waitFor({ timeout: STREAM_TIMEOUT_MS }).then(() => 'rec'),
          errAlert.waitFor({ timeout: STREAM_TIMEOUT_MS }).then(() => 'err'),
        ]);

        sample.endToEndMs = Date.now() - sample.startedAt;
        sample.reportRenderedMs = sample.endToEndMs;

        if (winner === 'err') {
          const txt = await errAlert.textContent().catch(() => '');
          throw new Error(`Error alert appeared instead of report: ${txt?.slice(0, 200)}`);
        }

        // Capture the recommendation text for the report.
        const rec = await page.locator('body').textContent();
        const m = rec?.match(recRegex);
        sample.recommendationText = m ? m[0] : null;

        samples.push(sample);

        // SLA invariant
        expect(sample.endToEndMs!, `End-to-end SLA breach for ${ticker}: ${sample.endToEndMs}ms > ${SLA_BUDGET_MS}ms`).toBeLessThanOrEqual(
          SLA_BUDGET_MS,
        );

        // Section presence — degraded sections render an empty-state, not a missing one.
        const expectedSectionLabels = [
          /technical/i,
          /fundamental/i,
          /news/i,
          /sector/i,
          /horizon|prediction/i,
          /confidence/i,
        ];
        for (const re of expectedSectionLabels) {
          await expect(page.locator('body')).toContainText(re);
        }
      } catch (err) {
        if (!samples.includes(sample)) samples.push(sample);
        await dumpDiagnostics(page, ticker, sample);
        throw err;
      }
    });
  }
});

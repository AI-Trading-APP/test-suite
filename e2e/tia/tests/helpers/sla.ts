import type { Page, Response as PWResponse, Request as PWRequest } from '@playwright/test';

export interface SlaSample {
  ticker: string;
  startedAt: number;
  navigationMs: number | null;     // page.goto → DOMContentLoaded
  authCheckMs: number | null;      // /api/auth/me round-trip end (relative to startedAt)
  streamRequestMs: number | null;  // when the SSE POST request was sent (relative to startedAt)
  streamWaitMs: number | null;     // headers timing (TTFB from server perspective)
  streamReceiveMs: number | null;  // body receive duration
  streamTotalMs: number | null;    // wait + receive
  endToEndMs: number | null;       // sample end (recommendation visible) - startedAt
  reportRenderedMs: number | null; // when recommendation tier appeared
  recommendationText: string | null;
  errors: string[];
}

const ACTIVE = new Map<string, SlaSample>();

export function startSample(ticker: string): SlaSample {
  const s: SlaSample = {
    ticker,
    startedAt: Date.now(),
    navigationMs: null,
    authCheckMs: null,
    streamRequestMs: null,
    streamWaitMs: null,
    streamReceiveMs: null,
    streamTotalMs: null,
    endToEndMs: null,
    reportRenderedMs: null,
    recommendationText: null,
    errors: [],
  };
  ACTIVE.set(ticker, s);
  return s;
}

export function attachListeners(page: Page, ticker: string) {
  const sample = ACTIVE.get(ticker);
  if (!sample) throw new Error(`startSample(${ticker}) must be called first`);

  page.on('request', (req: PWRequest) => {
    if (req.method() === 'POST' && req.url().includes(`/api/analysis/${ticker}/stream`)) {
      sample.streamRequestMs = Date.now() - sample.startedAt;
    }
  });

  page.on('response', async (resp: PWResponse) => {
    const url = resp.url();
    if (url.endsWith('/api/auth/me') && resp.request().method() === 'GET') {
      sample.authCheckMs = Date.now() - sample.startedAt;
    }
    if (resp.request().method() === 'POST' && url.includes(`/api/analysis/${ticker}/stream`)) {
      try {
        // Wait for the response to fully complete then pull timing from CDP-style metadata.
        await resp.finished().catch(() => null);
        // Playwright doesn't expose `wait` / `receive` directly on Response. The HAR
        // trace has them. As a reasonable approximation, we measure from request-sent
        // to response.finished using our own clock.
        sample.streamTotalMs = Date.now() - sample.startedAt - (sample.streamRequestMs ?? 0);
      } catch (err) {
        sample.errors.push(`response-fault: ${(err as Error).message}`);
      }
    }
  });

  page.on('pageerror', (err) => sample.errors.push(`pageerror: ${err.message}`));
  page.on('console', (msg) => {
    if (msg.type() === 'error') sample.errors.push(`console: ${msg.text().slice(0, 120)}`);
  });
}

export function summariseSamples(samples: SlaSample[]): string {
  const lines: string[] = [];
  lines.push(`\n${'='.repeat(110)}`);
  lines.push('  TIA E2E SLA — per-ticker (ms relative to navigation start)');
  lines.push('='.repeat(110));
  const cols = ['ticker', 'auth_me', 'stream_req', 'stream_total', 'rec_visible', 'end_to_end', 'recommendation'];
  lines.push(cols.map((h) => h.padEnd(15)).join(''));
  for (const s of samples) {
    lines.push(
      [
        s.ticker,
        s.authCheckMs ?? '-',
        s.streamRequestMs ?? '-',
        s.streamTotalMs ?? '-',
        s.reportRenderedMs ?? '-',
        s.endToEndMs ?? '-',
        s.recommendationText ?? '-',
      ]
        .map((v) => String(v).padEnd(15))
        .join(''),
    );
    if (s.errors.length) {
      const dedup = Array.from(new Set(s.errors)).slice(0, 6);
      lines.push(`  errors[${s.ticker}] (${s.errors.length} total, dedup top): ${dedup.join(' | ')}`);
    }
  }
  lines.push('='.repeat(110));
  return lines.join('\n');
}

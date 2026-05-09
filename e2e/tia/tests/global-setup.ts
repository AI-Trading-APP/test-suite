import { chromium, FullConfig, request } from '@playwright/test';
import { TEST_EMAIL, TEST_PASSWORD } from './helpers/auth';
import * as path from 'path';

/**
 * Logs in once via the public Next.js proxy, captures the auth cookies into
 * `storage-state.json`, and sets it on every test context. This avoids hitting
 * the user-service rate-limit and removes the per-test login flake.
 */
export default async function globalSetup(config: FullConfig) {
  const baseURL = (config.projects[0].use.baseURL ?? process.env.TIA_BASE_URL ?? 'https://test.ktrading.tech') as string;
  const ctx = await request.newContext({ baseURL, ignoreHTTPSErrors: true });
  const res = await ctx.post('/api/auth/login', {
    headers: { 'Content-Type': 'application/json' },
    data: { email: TEST_EMAIL, password: TEST_PASSWORD },
  });
  if (res.status() !== 200) {
    const body = await res.text();
    throw new Error(`globalSetup: login ${res.status()} for ${TEST_EMAIL} — ${body.slice(0, 200)}`);
  }
  const storageStatePath = path.resolve(process.cwd(), 'storage-state.json');
  await ctx.storageState({ path: storageStatePath });
  await ctx.dispose();
  // eslint-disable-next-line no-console
  console.log(`globalSetup: storage state written to ${storageStatePath}`);
}
